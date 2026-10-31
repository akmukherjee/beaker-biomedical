import json
import pathlib
from typing import Optional


def _get_metadata_path(endpoint_type: str) -> pathlib.Path:
    """Get the absolute path to the metadata JSON file for a given endpoint type.

    Args:
        endpoint_type: One of 'file', 'sample', or 'subject'

    Returns:
        Path to the metadata JSON file
    """
    script_dir = pathlib.Path(__file__).resolve().parent
    pv_dir = script_dir.parent / 'references' / 'pv'
    
    metadata_files = {
        'file': 'file-pv-metadata.json',
        'sample': 'sample-pv-metadata.json',
        'subject': 'subject-pv-metadata.json',
    }
    
    if endpoint_type not in metadata_files:
        raise ValueError(f"Unknown endpoint type: {endpoint_type}. Must be one of: {list(metadata_files.keys())}")
    
    return pv_dir / metadata_files[endpoint_type]


def load_metadata(endpoint_type: str) -> dict:
    """Load the metadata JSON file for a given endpoint type.

    Args:
        endpoint_type: One of 'file', 'sample', or 'subject'

    Returns:
        Dictionary containing field metadata with permissible values
    """
    path = _get_metadata_path(endpoint_type)
    with open(path, 'r') as f:
        return json.load(f)


def get_controlled_fields(endpoint_type: str) -> list[str]:
    """Get list of all controlled fields (fields with permissible values) for an endpoint type.

    Args:
        endpoint_type: One of 'file', 'sample', or 'subject'

    Returns:
        List of field names that have permissible values defined
    """
    metadata = load_metadata(endpoint_type)
    return [
        field for field, info in metadata.items()
        if info.get('permissible_values') is not None
    ]


def get_permissible_values(endpoint_type: str, field: str) -> Optional[list[str]]:
    """Get permissible values for a specific field from metadata.

    Args:
        endpoint_type: One of 'file', 'sample', or 'subject'
        field: The field name to get permissible values for

    Returns:
        List of permissible values (as strings) or None if field has no permissible values
    """
    metadata = load_metadata(endpoint_type)
    
    if field not in metadata:
        return None
    
    pv_list = metadata[field].get('permissible_values')
    if pv_list is None:
        return None
    
    return [pv['value'] for pv in pv_list]


def field_value_pair_exists(endpoint_type: str, field: str, value: str) -> bool:
    """Confirm that a field/value pair exists in the source metadata.

    Args:
        endpoint_type: One of 'file', 'sample', or 'subject'
        field: The field name
        value: The value to verify

    Returns:
        True if the field/value pair exists in metadata, False otherwise
    """
    permissible_values = get_permissible_values(endpoint_type, field)
    
    if permissible_values is None:
        return False
    
    return value in permissible_values


def get_field_metadata(endpoint_type: str, field: str) -> Optional[dict]:
    """Get full metadata for a specific field including formal name, description, and permissible values.

    Args:
        endpoint_type: One of 'file', 'sample', or 'subject'
        field: The field name

    Returns:
        Dictionary with field metadata or None if field not found
    """
    metadata = load_metadata(endpoint_type)
    return metadata.get(field)
