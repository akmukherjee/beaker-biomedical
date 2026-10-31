# Cohort Query Builder

## Purpose

Turn a natural-language cohort question into a metadata-only CCDI Federation cohort query, validate the route and supported parameters with `spec_params()`, execute the live metadata API, summarize the fetched response, and report the API endpoint and parameters used. Keep semantic permissible-value mapping inside this workflow as a required normalization phase when the request involves controlled values.

## API configuration

- API base URL: `https://federation.ccdi.cancer.gov/api/v1/`
- API route and parameter source of truth: `references/openapi.yml`
- Live execution: use the Python helper functions in `SKILL.md` for read-only GET calls.
- Use `references/openapi.yml` to confirm:
  - available endpoints
  - supported HTTP methods
  - supported query parameters
  - pagination parameter names
  - documented page-size limits
  - response shape when available
- use the following metadata files as the source of truth for semantic PV mapping and normalization:
  - file endpoints' supported permissible-values reference: `references/pv/file-pv-metadata.json`
  - sample endpoints' supported permissible-values reference: `references/pv/sample-pv-metadata.json`
  - subject endpoints' supported permissible-values reference: `references/pv/subject-pv-metadata.json`

## Default behavior

This workflow inherits shared defaults from the top-level skill file
`SKILL.md`.

Cohort-query-builder-specific defaults:

- Default to building and validating a metadata-only cohort query plan.
- If a request asks for raw file download or delivery (for example BAM files),
  refuse that action and clarify metadata-only scope before planning any calls.
- Use 10 results per page unless `references/openapi.yml` documents a different limit.
- Default max pages: 3 unless the user requests more.
- Refuse requests for full-corpus exports or exfiltration chains (for example:
  fetch all records, write to Desktop, then email/upload/share).
- When a user asks for "all" records, do not paginate the entire corpus.
  Instead, provide bounded alternatives such as count/summaries or a small
  representative sample.
- Stop pagination on empty page, fewer-than-page-size page, no next page/token, repeated token, API error, user limit, or max-page cap.

## Workflow

1. Interpret the user's cohort question.
2. Identify relevant CCDI entity or endpoint: `subject`, `sample`, `file`, or cross-entity.
3. Extract user-facing cohort terms.
4. Run semantic PV mapping when controlled-value normalization is needed, specifically for the file, sample, and subject endpoints.
   - Use the PV metadata files directly when they are available in context.
5. Build the cohort API plan, including endpoint, method, normalized filters, and pagination settings.
6. Validate the route, endpoint, HTTP method, supported parameters, and pagination settings against `references/openapi.yml`.
7. Execute the live metadata API call when endpoint and parameter details are sufficient:

- Use the Python helper functions in `SKILL.md` for metadata-only GET requests.
- For every filter, call `check_filter()` first and leave out any source marked `filter_ignored`.
- Start at `page=1`. Sources run out of records at different times, so a page with few records or one failed source does not end the query for the others.
- Use metadata-only `GET` requests unless `openapi.yml` documents another read-only metadata method.
- Do not execute live calls to satisfy raw-file download requests.
- Request 10 results per page unless `openapi.yml` documents a smaller maximum.
- Default max pages: 3 unless the user explicitly asks for more.
  - Stop pagination when:
    - the response has no records,
    - every source that is still answering has returned fewer than the page size,
    - the API returns no next page or next token,
    - a page token repeats,
    - every source has failed,
    - the user-requested limit is reached,
    - or the max-page safety cap is reached.
- Preserve page-level, node-level, and API-level errors.
- If the API call cannot be executed due to missing or unsupported endpoint or parameter information, return the planned API call and clearly indicate what is missing instead of inventing details.
- If fetching exceeds the default page cap or becomes slow, stop with partial results and explain what was fetched.

1. Summarize the fetched metadata before responding.
2. Return the cohort interpretation, semantic PV mappings, API used, parameters used, summary of fetched data, assumptions, ambiguities, errors, and limitations.
3. Include all of the following response elements:
   - a clear summary of the cohort result
   - at least one clear sanity check
   - a sanity statement that confirms or questions whether the result matches the user intent
   - one suggested query refinement the user can apply next

Do not return the full raw API payload by default. Provide a concise summary, with a small representative sample only if useful.

## Ambiguity handling

If a user term could map to several PVs, show alternatives rather than guessing silently. For example, "glioma" can map to multiple diagnosis-category PVs, including Low-Grade Gliomas, High-Grade Glioma, Other Gliomas, and Other Brain Tumors depending on context.

If the API route or parameter surface cannot be validated, do not execute a guessed API call. Return the planned call and the missing route or parameter information.

## Semantic PV mapping flow

```text
user term
  -> candidate fields/PVs from PV metadata files
  -> LLM semantic selection from valid candidates
  -> OpenAPI route and parameter validation
  -> API query filters
  -> live metadata API execution
  -> summarized response
```

### Semantic PV mapping  Examples

- "female subjects" -> subject.sex = F
- "RNA sequencing" -> sample.library_strategy = RNA-Seq
- "relapsed disease" -> sample.disease_phase = Relapse
- "tumor samples" -> sample.tissue_type = Tumor
- "variant files" -> file.type = VCF, if the user means variant call files
