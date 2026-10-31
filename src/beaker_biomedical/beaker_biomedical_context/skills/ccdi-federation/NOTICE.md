# Notice

This skill is adapted from `skills/ccdi-federation-ai-copilot` in
https://github.com/CBIIT/ccdi-federation-ai (commit 4cfb8e8, version 1.0.1), licensed
under the Apache License 2.0. See `LICENSE`.

Changes: added `scripts/ccdi_helpers.py` and the rules for source failures, ignored filters,
and live spec and value checks in `SKILL.md`; made live queries the default; refreshed
`references/openapi.yml` to v1.3.0; added `diagnosis_category` and raised the timeout
in `scripts/ccdi_client.py`; removed `agents/openai.yaml`; renamed the skill from `ccdi-federation-ai-copilot` to `ccdi-federation`.
