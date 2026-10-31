"""Read-only helpers for the CCDI Data Federation API. See SKILL.md."""
import json, requests, yaml
from pathlib import Path

BASE = "https://federation.ccdi.cancer.gov/api/v1"
SPEC_URL = "https://cbiit.github.io/ccdi-federation-api-aggregation/swagger-aggr.yml"
TIMEOUT = 90  # single count calls have taken over 30 seconds

NOTES = {
    "source_totals": "NOTE: these are ALL records with no filter. If the question names a file type, "
                     "disease, tissue, or any other condition, these numbers do not answer it. Use "
                     "find_value() and check_filter(). These are per-source counts, not unique people.",
    "check_filter": "NOTE: per-source counts, not unique people. The same child may be in more than one "
                    "source, so a unique total cannot be worked out. If asked for a unique or overall "
                    "total, say this in your first sentence.",
}

def _show(fn):
    """Print each helper's result, with any note the agent must act on."""
    def wrapper(*args, **kwargs):
        result = fn(*args, **kwargs)
        print(f"{fn.__name__}{args}: {result}")
        if fn.__name__ in NOTES:
            print(NOTES[fn.__name__])
        return result
    wrapper.__doc__, wrapper.__wrapped__ = fn.__doc__, fn
    return wrapper

def ccdi_get(path, **params):
    r = requests.get(f"{BASE}/{path.lstrip('/')}", params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def split_sources(payload):
    """Return (ok, failed). The HTTP status can be 200 while sources fail."""
    ok = [s for s in payload if "errors" not in s]
    failed = {s["source"]: s["errors"][0].get("kind", "unknown") for s in payload if "errors" in s}
    return ok, failed

@_show
def federation_info():
    """Current sources and the API version each one runs. Call this first."""
    return {s["source"]: s["api"]["api_version"] for s in ccdi_get("info") if "api" in s}

def _skill_dir():
    return Path(__file__).resolve().parents[1]

_spec = None
def load_spec():
    """Latest published spec, or the bundled snapshot if it cannot be fetched."""
    global _spec
    if _spec is None:
        try:
            r = requests.get(SPEC_URL, timeout=TIMEOUT)
            r.raise_for_status()
            _spec = yaml.safe_load(r.text)
        except Exception:
            _spec = yaml.safe_load((_skill_dir() / "references/openapi.yml").read_text())
    return _spec

def spec_params(path):
    """Query parameter names for a route such as '/sample'. Do not print the whole spec."""
    get = load_spec()["paths"][path]["get"]
    return [p["name"] for p in get.get("parameters", []) if p.get("in") == "query"]

@_show
def source_totals(entity):
    """Record totals per source for 'subject', 'sample', or 'file'. Use for "how many" with no filter."""
    ok, failed = split_sources(ccdi_get(f"{entity}/summary"))
    return {s["source"]: s["counts"]["total"] for s in ok}, failed

@_show
def list_fields(entity):
    """Fields each source supports for an entity. Use these names with live_values()."""
    ok, failed = [], {}
    for s in ccdi_get(f"metadata/fields/{entity}"):
        if "errors" in s:
            failed[s["source"]] = s["errors"][0].get("kind", "unknown")
        else:
            ok.append(s)
    return {s["source"]: sorted(f.get("path", f.get("name", "?")) for f in s.get("fields", [])) for s in ok}, failed

@_show
def live_values(entity, field):
    """Values each source holds for a metadata field such as 'sex' or 'tissue_type', not an ID field."""
    ok, failed = split_sources(ccdi_get(f"{entity}/by/{field}/count"))
    return {s["source"]: {"values": s.get("values", []), "missing": s.get("missing")} for s in ok}, failed

def _pv(entity):
    return json.loads((_skill_dir() / f"references/pv/{entity}-pv-metadata.json").read_text())

@_show
def find_value(entity, term):
    """Map the user's word to real filters. Returns [(field, value, meaning)]. Use before check_filter()."""
    term = term.lower()
    usable = set(spec_params(f"/{entity}"))
    hits = []
    for field, info in _pv(entity).items():
        for pv in info.get("permissible_values") or []:
            value, meaning = str(pv["value"]), pv.get("vm_long_name") or ""
            text = (value.lower(), meaning.lower())
            matched = term in text if len(term) < 3 else any(term in s for s in text)
            if field in usable and matched:
                hits.append((field, value, meaning))
    return sorted(hits, key=lambda h: (len(h[1]), h[0]))

@_show
def check_filter(entity, field, value):
    """Validate a filter, then run it next to a made-up control value and classify each source.

    Returns one dict: {source: {"status": ..., "count": ...}}. It is not a pair.
    Raises ValueError with suggestions if the field or value is not valid. Do not report that
    error as a source failure. Fix the call, or tell the user the value does not exist.
    A source can accept a filter and ignore it, returning its full total with no error.
    Treat only sources marked ok or no_match as real results.
    """
    usable = spec_params(f"/{entity}")
    if field not in usable:
        raise ValueError(f"'{field}' is not a {entity} filter. Valid filters: {usable}")
    official = [str(v["value"]) for v in (_pv(entity).get(field, {}).get("permissible_values") or [])]
    if official and value not in official:
        by_source, _ = live_values.__wrapped__(entity, field)
        held = {str(v["value"]) for s in by_source.values() for v in s["values"]}
        if value not in held:
            raise ValueError(f"'{value}' is not a valid value of {field}. Tell the user this and list these "
                             f"valid values: {official[:40]}. Values in the data: {sorted(held)[:40]}")
    def counts(v):
        ok, failed = split_sources(ccdi_get(entity, **{field: v, "page": 1, "per_page": 1}))
        return {s["source"]: s["summary"]["counts"]["all"] for s in ok}, failed
    real, failed = counts(value)
    control, _ = counts("ccdi-control-not-a-real-value")
    result = {}
    for source, n in real.items():
        if n and control.get(source) == n:
            result[source] = {"status": "filter_ignored", "count": None}
        elif n == 0:
            result[source] = {"status": "no_match", "count": 0}
        else:
            result[source] = {"status": "ok", "count": n}
    # A source can reject a filter but still answer the same question on its count route.
    if failed:
        rows, _ = split_sources(ccdi_get(f"{entity}/by/{field}/count"))
        by_count = {s["source"]: s.get("values", []) for s in rows}
    for source, reason in failed.items():
        hits = [v["count"] for v in by_count.get(source, []) if str(v["value"]) == value]
        if hits:
            result[source] = {"status": "ok", "count": hits[0], "via": "count endpoint"}
        else:
            result[source] = {"status": "failed", "reason": reason, "count": None}
    return result

@_show
def search_diagnosis(entity, term):
    """Experimental free-text diagnosis search for 'subject' or 'sample'. These are text matches, not exact counts."""
    ok, failed = split_sources(ccdi_get(f"{entity}-diagnosis", search=term, page=1, per_page=1))
    return {
        "match_type": "FREE-TEXT MATCH, not an exact count and not a diagnosis_category count",
        "matches": {s["source"]: s["summary"]["counts"]["all"] for s in ok},
        "failed": failed,
    }
