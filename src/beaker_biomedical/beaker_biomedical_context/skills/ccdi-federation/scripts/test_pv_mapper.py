import importlib.util
import pathlib
import unittest
from unittest.mock import patch


MODULE_PATH = pathlib.Path(__file__).resolve().parent / "pv_mapper.py"
_SPEC = importlib.util.spec_from_file_location("pv_mapper", MODULE_PATH)
pv_mapper = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(pv_mapper)


class TestPvMapper(unittest.TestCase):
    def test_get_metadata_path_valid_endpoint(self):
        path = pv_mapper._get_metadata_path("subject")
        expected = MODULE_PATH.parent.parent / "references" / "pv" / "subject-pv-metadata.json"
        self.assertEqual(path, expected)

    def test_get_metadata_path_invalid_endpoint(self):
        with self.assertRaises(ValueError):
            pv_mapper._get_metadata_path("unknown")

    @patch.object(pv_mapper, "load_metadata")
    def test_get_controlled_fields_filters_none(self, mock_load_metadata):
        mock_load_metadata.return_value = {
            "sex": {"permissible_values": [{"value": "F"}]},
            "notes": {"permissible_values": None},
            "diagnosis": {"permissible_values": [{"value": "AML"}]},
        }
        fields = pv_mapper.get_controlled_fields("subject")
        self.assertEqual(fields, ["sex", "diagnosis"])

    @patch.object(pv_mapper, "load_metadata")
    def test_get_permissible_values(self, mock_load_metadata):
        mock_load_metadata.return_value = {
            "sex": {"permissible_values": [{"value": "F"}, {"value": "M"}]},
            "notes": {"permissible_values": None},
        }
        self.assertEqual(pv_mapper.get_permissible_values("subject", "sex"), ["F", "M"])
        self.assertIsNone(pv_mapper.get_permissible_values("subject", "notes"))
        self.assertIsNone(pv_mapper.get_permissible_values("subject", "missing"))

    @patch.object(pv_mapper, "get_permissible_values")
    def test_field_value_pair_exists(self, mock_get_permissible_values):
        mock_get_permissible_values.return_value = ["F", "M"]
        self.assertTrue(pv_mapper.field_value_pair_exists("subject", "sex", "F"))
        self.assertFalse(pv_mapper.field_value_pair_exists("subject", "sex", "X"))

        mock_get_permissible_values.return_value = None
        self.assertFalse(pv_mapper.field_value_pair_exists("subject", "sex", "F"))

    @patch.object(pv_mapper, "load_metadata")
    def test_get_field_metadata(self, mock_load_metadata):
        metadata = {"sex": {"formal_name": "Sex", "permissible_values": [{"value": "F"}]}}
        mock_load_metadata.return_value = metadata
        self.assertEqual(pv_mapper.get_field_metadata("subject", "sex"), metadata["sex"])
        self.assertIsNone(pv_mapper.get_field_metadata("subject", "missing"))


if __name__ == "__main__":
    unittest.main()
