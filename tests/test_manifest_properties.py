from __future__ import annotations

import copy

from hypothesis import given, settings
from hypothesis import strategies as st

from modelstamp._manifest import Manifest
from modelstamp.exceptions import ManifestError

JSON_SCALAR = st.none() | st.booleans() | st.integers() | st.text()
JSON_VALUE = st.recursive(
    JSON_SCALAR,
    lambda children: (
        st.lists(children, max_size=5)
        | st.dictionaries(st.text(max_size=20), children, max_size=5)
    ),
    max_leaves=20,
)
VALID_MANIFEST = {
    "schema_version": 1,
    "artifact": {"filename": "model.pkl", "sha256": "0" * 64, "size_bytes": 1},
    "serialization": {"backend": "pickle"},
    "model": {"class": "Model", "module": "example"},
    "environment": {
        "python_version": "3.13.0",
        "python_implementation": "CPython",
        "platform": "test",
        "created_at": "2026-08-20T00:00:00+00:00",
        "packages": {},
    },
    "relevant_packages": [],
    "metadata": {},
}


@given(JSON_VALUE)
@settings(max_examples=300, deadline=None)
def test_arbitrary_json_never_raises_an_unexpected_exception(value):
    try:
        Manifest.from_dict(value)
    except ManifestError:
        pass


@given(
    st.sampled_from(
        [
            "schema_version",
            "artifact",
            "serialization",
            "model",
            "environment",
            "relevant_packages",
            "metadata",
        ]
    ),
    JSON_VALUE,
)
@settings(max_examples=200, deadline=None)
def test_mutating_a_required_manifest_field_is_safely_handled(field, replacement):
    data = copy.deepcopy(VALID_MANIFEST)
    data[field] = replacement
    try:
        Manifest.from_dict(data)
    except ManifestError:
        pass
