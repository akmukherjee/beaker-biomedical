# API Explainer

## Purpose

Explain CCDI Federation API endpoints, parameters, response shapes, metadata fields, permissible values, relationships, pagination, and errors in clear user-facing language.

Use `spec_params()` for route and parameter validation; it reads the latest spec, with `references/openapi.yml` as the fallback. Use the bundled PV metadata files for permissible-value meanings, and check live data with `live_values()` when a value's real use matters; the CCDI Federation API wiki is supplementary context only.

This skill is for explanation and onboarding. It helps users understand how the API works before or after they run metadata queries.

## API configuration

- API host: `https://federation.ccdi.cancer.gov/`
- API version base path: `/api/v1/`
- Route and parameter source of truth: `references/openapi.yml`
- Permissible-value descriptions: bundled PV metadata files (see below). The CCDI Federation API wiki (`https://github.com/CBIIT/ccdi-federation-api/wiki`) may be consulted for background context only — it does not override bundled PV metadata.
- Explain only metadata-level API behavior.
- Do not claim raw data access.

Use `openapi.yml` to confirm:

- available endpoints
- supported HTTP methods
- required and optional parameters
- parameter names and types
- pagination behavior
- response schema or response examples when available
- documented errors and status codes

For federation hub paginated collection endpoints, explain pagination in terms of
the `page` and `per_page` query parameters plus each node's
`summary.counts.current` and `summary.counts.all` values in the aggregated JSON
response body. Do not describe an HTTP `Link` response header for hub
pagination unless bundled documentation is explicitly updated to match runtime
behavior.

Use the following bundled PV metadata files for permissible values:

- `references/pv/subject-pv-metadata.json`
- `references/pv/sample-pv-metadata.json`
- `references/pv/file-pv-metadata.json`

## Default behavior

This workflow inherits shared defaults from the top-level skill file
`SKILL.md`.

API-explainer-specific defaults:

- When the user asks how an endpoint works, explain endpoint purpose, method,
  path, parameters, pagination, response shape, and common use cases.
- When the user asks about a field, explain the field meaning, entity context,
  expected value type, controlled-value status, and known relationships.
- When the user asks about a permissible value, explain the exact PV, field,
  entity, meaning, description, caDSR reference when available, and similar
  alternatives when relevant.

## Workflow

1. Identify the user's explanation target:
   - endpoint
   - parameter
   - response field
   - permissible value
   - full API response
   - error message
   - pagination behavior
   - subject/sample/file relationship
   - harmonized vs unharmonized metadata

2. Consult `references/openapi.yml` when endpoint, method, route, parameter, pagination, or response-shape details are needed.

3. If the user asks about metadata fields or permissible values, use the bundled PV metadata files:
   - `references/pv/subject-pv-metadata.json`
   - `references/pv/sample-pv-metadata.json`
   - `references/pv/file-pv-metadata.json`

4. For broader permissible-value background and narrative context, the CCDI Federation API wiki may be consulted:
   - `https://github.com/CBIIT/ccdi-federation-api/wiki`
   - **The wiki is supplementary context only.** Do not use it to override the bundled PV files.

5. Explain the API behavior in user-facing language:
   - what the endpoint is for
   - what kind of metadata it returns
   - what filters or query parameters it supports
   - how pagination works
   - what the key response fields mean
   - what permissible values mean in context
   - what assumptions or limitations apply

6. If the user provided a response payload:
   - identify the endpoint if possible
   - summarize record counts and key fields
   - explain nested structures
   - identify missing or null fields
   - explain controlled-value fields when relevant
   - explain per-node or per-page errors
   - distinguish empty results from API errors

7. If the user asks for an example request:
   - build a documented request using the base path and supported parameters
   - include method, endpoint, query parameters, and a short explanation
   - do not invent unsupported parameters

8. If the user asks to run or test the API:
   - use the Python helper functions in `SKILL.md`
   - use metadata-only read requests
   - summarize the returned metadata
   - report endpoint, method, parameters, pagination, returned records, and errors
   - avoid long-running or full-export behavior unless explicitly requested

## Explanation rules

- Use `references/openapi.yml` as the source of truth for routes and parameters.
- Use bundled PV metadata files (`references/pv/*.json`) for controlled-value explanation. The CCDI Federation API wiki is supplementary context only and does not override the bundled PV files.
- Do not invent routes, parameters, fields, response schemas, or permissible values.
- Clearly distinguish:
  - endpoint behavior
  - query parameters
  - response fields
  - harmonized metadata
  - unharmonized metadata
  - controlled values
  - free-text fields
  - missing metadata
  - API errors
  - empty results
- Keep explanations concise first, then add structured details when useful.
- If a field exists in multiple entity contexts, specify the entity: `subject`, `sample`, or `file`.
- If the API docs are incomplete, say so and provide the safest known interpretation.

## Permissible value explanation

Use this section when the user asks what a field value means, what values are allowed for a field, why a submitted value is invalid, or how user language relates to CCDI controlled values.

Permissible values are controlled values defined for specific CCDI metadata fields. They help standardize metadata across federation nodes.

**Bundled PV metadata files hold permissible-value descriptions:**

- `references/pv/subject-pv-metadata.json`
- `references/pv/sample-pv-metadata.json`
- `references/pv/file-pv-metadata.json`

For narrative background, the CCDI Federation API wiki may be referenced:

`https://github.com/CBIIT/ccdi-federation-api/wiki`

The wiki is supplementary context only. When bundled PV metadata files are available, always use them as the authoritative source. Do not use web search or the wiki to override the bundled PV files. Live API data and the live spec are allowed for checking which values are really in use.

## PV Explanation Responsibilities

When explaining a permissible value, include:

- The endpoint/entity: subject, sample, or file
- The field name
- The exact permissible value
- The user-facing meaning
- The PV description, if available
- The caDSR formal name or link, if available
- Whether the value is controlled or free text
- Similar or easily confused alternatives, when relevant

Do not invent permissible values. If a value is not present in the PV metadata, say it is not validated as a supported PV.

## Harmonized vs. Unharmonized Metadata

- Harmonized metadata uses standardized CCDI fields and controlled values when available.

- Unharmonized metadata may preserve source-node wording, legacy field names, or original submitted values.

- Do not treat unharmonized values as equivalent to controlled PVs unless a mapping is documented or clearly supported.
