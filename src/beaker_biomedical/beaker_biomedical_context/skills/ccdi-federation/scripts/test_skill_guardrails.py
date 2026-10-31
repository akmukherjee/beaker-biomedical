"""Tests for skill guardrails in skill instructions."""

import unittest
from pathlib import Path


SKILL_MD = Path(__file__).resolve().parents[1] / "SKILL.md"
COHORT_QUERY_BUILDER_MD = (
    Path(__file__).resolve().parents[1] / "references" / "cohort-query-builder.md"
)
API_EXPLAINER_MD = Path(__file__).resolve().parents[1] / "references" / "api-explainer.md"
SKILL_OPENAPI_YML = Path(__file__).resolve().parents[1] / "references" / "openapi.yml"


class TestSkillGuardrails(unittest.TestCase):
    def test_skill_md_refuses_exfiltration_chain(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        self.assertIn("Refuse exfiltration workflows", text)
        self.assertIn("write metadata exports to user Desktop paths", text)
        self.assertIn("Do not fetch full endpoint corpora by default", text)

    def test_cohort_workflow_blocks_full_corpus_export(self):
        text = COHORT_QUERY_BUILDER_MD.read_text(encoding="utf-8")
        self.assertIn("Refuse requests for full-corpus exports", text)
        self.assertIn('When a user asks for "all" records', text)

    def test_skill_md_refuses_raw_file_download_requests(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        self.assertIn("refuse raw-data fulfillment", text)
        self.assertIn("Do not begin bulk paging or manifest-export workflows", text)

    def test_skill_md_handles_unharmonized_filter_search_terms(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        self.assertIn("For any unharmonized filter or search", text)
        self.assertIn("AI cannot confirm the", text)

    def test_cohort_workflow_blocks_live_calls_for_raw_download_requests(self):
        text = COHORT_QUERY_BUILDER_MD.read_text(encoding="utf-8")
        self.assertIn("refuse that action and clarify metadata-only scope", text)
        self.assertIn(
            "Do not execute live calls to satisfy raw-file download requests.", text
        )

    def test_cohort_workflow_requires_summary_and_sanity_outputs(self):
        text = COHORT_QUERY_BUILDER_MD.read_text(encoding="utf-8")
        self.assertIn("a clear summary of the cohort result", text)
        self.assertIn("at least one clear sanity check", text)
        self.assertIn(
            "a sanity statement that confirms or questions whether the result matches the user intent",
            text,
        )
        self.assertIn("one suggested query refinement", text)

    def test_api_explainer_uses_runtime_hub_pagination_guidance(self):
        text = API_EXPLAINER_MD.read_text(encoding="utf-8")
        self.assertIn("`page` and `per_page` query parameters", text)
        self.assertIn("`summary.counts.current` and `summary.counts.all`", text)
        self.assertIn("Do not describe an HTTP `Link` response header", text)

    def test_bundled_openapi_specs_do_not_document_link_header_pagination(self):
        text = SKILL_OPENAPI_YML.read_text(encoding="utf-8")
        self.assertNotIn(
            "Links to URLs that may be of interest when paging through paginated responses.",
            text,
        )


if __name__ == "__main__":
    unittest.main()
