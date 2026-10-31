---
name: ccdi-federation
description: >-
  Query, plan, explain, and validate metadata-only workflows against the CCDI
  Data Federation API, which aggregates childhood and pediatric cancer subject,
  sample, and file metadata from multiple independent source servers. Use when
  the user asks about pediatric cancer cohorts or counts, or needs to build or
  review CCDI cohort queries, map natural-language cohort terms to subject/sample/file
  fields or permissible values, explain CCDI Federation endpoints, parameters,
  response fields, pagination, harmonized versus unharmonized metadata,
  node-level errors, or run read-only metadata GET requests against the CCDI
  Federation API with OpenAPI and PV guardrails. Not for adult cancer cohorts
  (use GDC or CDA) or canine data (use ICDC).
---

# CCDI Federation

Use this skill for CCDI Data Federation API work that stays at the metadata
layer. When the user asks a data question, run the queries and answer it.

## Start here: import the helpers

Run this once per session. Do not retype or redefine the helpers, because the copies here
hold the guardrails. They print their own results, and if an import fails, fix the path rather
than rewriting them. Empty output does not mean the API failed. Never tell the user the API is
down unless a call raised an error.

```python
import sys
from pathlib import Path
try:
    import beaker_biomedical
    pkg = Path(beaker_biomedical.__file__).parent
except ImportError:
    pkg = next(p / "src/beaker_biomedical" for p in (Path.cwd(), *Path.cwd().parents)
               if (p / "src/beaker_biomedical").is_dir())
sys.path.insert(0, str(pkg / "beaker_biomedical_context/skills/ccdi-federation/scripts"))
from ccdi_helpers import (federation_info, source_totals, list_fields, find_value, check_filter,
                          live_values, search_diagnosis, spec_params, ccdi_get, split_sources)
```

## The standard steps for any "how many" question

```python
find_value("sample", "<the user's word>")           # 1. get the real field and value
check_filter("sample", "<field>", "<value>")        # 2. get the checked per-source result
search_diagnosis("sample", "<disease>")             # 3. only if few sources answered in step 2
```

Every helper already covers all sources, so never loop over sources yourself. For a disease,
always do steps 1 and 2 before step 3, and report the two results separately. Step 3 is a text
match, so never call it a category count.

## Which helper to use

| Question | Call |
|---|---|
| Total records only, with no condition at all. "BAM files" or "tumor samples" have a condition, so do not use this | `source_totals(entity)` |
| Which field and value a word means, such as "tumor" or "female" | `find_value(entity, term)`, always first |
| How many match a value | `check_filter(entity, field, value)` |
| A disease, especially when few sources support the filter | `search_diagnosis(entity, term)` |
| Breakdown by a field, or which values exist | `live_values(entity, field)` |
| Which fields can be used | `list_fields(entity)` |

## Required checks

0. **Answer the question directly in the first sentence.** If the value the user asked
   about is not in the data, say so plainly, even when another helper gave you useful
   numbers. For example: "No subjects have sex X, because X is not a valid value." Then give
   the closest real values.
1. **Call `federation_info()` first.** The sources and their versions change, so never
   assume a fixed list. Each source runs its own API version, and a filter in the latest
   spec may not work on an older source. Warn the user when that applies.
2. **HTTP 200 does not mean every source answered.** Always use `split_sources()`, and
   name every failed source and its reason in the answer. Never present a partial result
   as complete.
3. **Zero matches is not the same as a failed source.** `no_match` means the source
   answered and found nothing. `failed` means it did not answer. Report them differently.
4. **Sources can silently ignore a filter.** Call `check_filter()` before reporting any
   filtered result. Exclude sources marked `filter_ignored` and say so. Their counts are
   not answers to the question.
5. **Report counts per source.** Do not sum them into one total unless you also say the
   same child may appear in more than one source.
6. **Include `missing` when interpreting `/by/{field}/count`.** Null or empty values never
   match a filter.
7. **If most sources fail with a parameter or field error, suspect your own call first.**
   Check the table above and `list_fields()`, fix the call, and retry before reporting
   anything. Report failures to the user only after a corrected call, and do not end an
   answer with errors alone if another helper can answer the question.
8. **Never guess a field or value.** Use `find_value()` first. If `check_filter()` raises
   `ValueError`, the call is wrong, not the sources. Fix it, or tell the user the value does
   not exist and suggest the closest real ones. Do not report it as zero or as a failure.
9. **When few sources can answer, offer another route.** Also run `search_diagnosis()` and
   label it as a text match, not an exact count. Do not mix the two numbers.
10. **Filtering rules.** Values in one field are OR, separate filters are AND, and a
   cross-field OR needs separate calls and a union. Always start at `page=1`.

## Resources

- Cohort query planning and execution workflow: `references/cohort-query-builder.md`
- Endpoint, parameter, response, and permissible-value explanation workflow:
  `references/api-explainer.md`
- OpenAPI snapshot, used only when the live spec cannot be fetched:
  `references/openapi.yml`
- Permissible-value metadata:
  - `references/pv/subject-pv-metadata.json`
  - `references/pv/sample-pv-metadata.json`
  - `references/pv/file-pv-metadata.json`

## Routing

- For cohort requests, field/PV normalization, cohort query plans, or live
  cohort metadata fetches, read `references/cohort-query-builder.md`.
- For endpoint, parameter, response payload, permissible-value, pagination,
  relationship, or error explanations, read `references/api-explainer.md`.
- For mixed requests, start with the cohort workflow when the user is trying
  to identify a cohort; otherwise start with the API explainer workflow.

## Guardrails

- Validate routes, methods, and parameters with `spec_params()` before executing
  calls. It reads the latest published spec and falls back to the bundled snapshot.
- **Use three sources for controlled values, each for its own job.**
  - Use the bundled PV files in `references/pv/` to map the user's words to
    candidate values. They hold the descriptions.
  - Use the live spec to confirm a value is official.
  - Use `live_values()` to see what each source really holds before filtering.
    Filters are exact and case-sensitive, and sources can differ from the official
    spelling (for example `ATAC-seq` in data versus the official `ATAC-Seq`).
  - If live data disagrees with the official value, query the spelling the source
    uses and tell the user about the difference.
  - Surface assumptions instead of inventing unsupported field/value mappings.
- Keep live execution scoped to metadata-only read requests. Do not claim raw
  data access. Run live calls in Python with the helper functions above.
- Refuse exfiltration workflows, including chained requests to fetch full
  datasets and then write, email, upload, or otherwise transfer bulk outputs.
- Do not write metadata exports to user Desktop paths or any location outside
  the active workspace.
- Do not fetch full endpoint corpora by default (for example, all `/subject`
  pages). Offer bounded alternatives such as summaries, counts, or a small
  sample page.
- If a user asks to download, transfer, or deliver raw files (for example BAM
  files), explicitly refuse raw-data fulfillment and clarify this skill only
  supports metadata-level API access.
- Do not begin bulk paging or manifest-export workflows to satisfy raw-file
  download requests.
- Preserve node-level, page-level, and API-level errors in summaries.
- Do not dump raw full API responses by default. Summarize first and include
  representative records only when useful.

## Clarification Protocol

- Before taking any action, fully understand the user's request. If any part of
  the request is ambiguous, incomplete, or could be interpreted in more than one
  way, ask for clarification and wait for confirmation before proceeding.
- Do not act on unconfirmed assumptions. If you are unsure what the user is
  asking for, state what you do not understand and ask a focused clarifying
  question rather than guessing.
- Once you have understood the request, briefly state your interpretation and
  the approach you plan to take. Proceed without waiting when the
  request has one reasonable reading.
- During execution, if you encounter new information that introduces ambiguity
  about what the user wants, pause and ask for clarification before continuing.
  Do not pretend to understand or silently choose between competing
  interpretations.

## Default Behavior

- Answer data questions by running live metadata queries. Do not stop at a plan
  unless the user asks for only a plan.
- Keep live execution metadata-only and read-only.
- Refuse requests to chain metadata retrieval with data exfiltration actions
  (file writes outside workspace, email, external transfer, or similar).
- Run live calls in Python with the helper functions above.
- For raw-file download asks, refuse delivery, avoid execution, and offer
  metadata-only alternatives only when the user wants metadata.
- Summarize returned metadata by default instead of dumping full raw responses.
- Preserve node-level, page-level, and API-level errors in outputs.
- If route, parameter, field, or permissible-value details cannot be validated
  from configured sources, report the gap and avoid inventing unsupported
  details.
- For any unharmonized filter or search, state that AI cannot confirm the
  correct term to use unless it is explicitly documented or provided by the
  user.

## Response Style

- Conversational asks: prose-first summary with optional structured detail.
- Planning, QA, and validation asks: structured-first output with explicit
  assumptions, mappings, API plan, and warnings.
