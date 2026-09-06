"""Validate the state-of-the-field evidence ledger using the standard library."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

EVIDENCE_PATH = Path(__file__).with_name("evidence.json")
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "reviewed_on",
    "scope",
    "status_vocabulary",
    "tools",
    "sources",
    "dimensions",
    "assessments",
}


def unique_ids(records: list[dict[str, object]], label: str) -> set[str]:
    identifiers = [record.get("id") for record in records]
    if any(
        not isinstance(identifier, str) or not identifier for identifier in identifiers
    ):
        raise ValueError(f"{label} must have non-empty string ids")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"{label} ids must be unique")
    return set(identifiers)


def validate(path: Path = EVIDENCE_PATH) -> dict[str, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = REQUIRED_TOP_LEVEL - data.keys()
    if missing:
        raise ValueError(f"missing top-level keys: {sorted(missing)}")
    tool_ids = unique_ids(data["tools"], "tools")
    source_ids = unique_ids(data["sources"], "sources")
    dimension_ids = unique_ids(data["dimensions"], "dimensions")
    statuses = set(data["status_vocabulary"])
    for source in data["sources"]:
        if source.get("tool") not in tool_ids:
            raise ValueError(f"unknown source tool: {source.get('tool')}")
        parsed = urlparse(str(source.get("url", "")))
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError(f"source URL must be HTTPS: {source.get('id')}")
        if source.get("accessed") != data["reviewed_on"]:
            raise ValueError(f"stale access date: {source.get('id')}")
        claims = source.get("claims")
        if (
            not isinstance(claims, list)
            or not claims
            or not all(isinstance(claim, str) and claim.strip() for claim in claims)
        ):
            raise ValueError(f"source needs bounded claims: {source.get('id')}")
    seen_pairs: set[tuple[str, str]] = set()
    for assessment in data["assessments"]:
        tool = assessment.get("tool")
        dimension = assessment.get("dimension")
        pair = (str(tool), str(dimension))
        if tool not in tool_ids or dimension not in dimension_ids:
            raise ValueError(f"unknown assessment target: {pair}")
        if pair in seen_pairs:
            raise ValueError(f"duplicate assessment: {pair}")
        seen_pairs.add(pair)
        if assessment.get("status") not in statuses:
            raise ValueError(f"unknown status for {pair}")
        references = assessment.get("sources")
        if not isinstance(references, list) or not references:
            raise ValueError(f"assessment needs sources: {pair}")
        unknown_sources = set(references) - source_ids
        if unknown_sources:
            raise ValueError(f"unknown sources for {pair}: {sorted(unknown_sources)}")
    expected_pairs = {
        (tool, dimension) for tool in tool_ids for dimension in dimension_ids
    }
    missing_pairs = expected_pairs - seen_pairs
    extra_pairs = seen_pairs - expected_pairs
    if missing_pairs or extra_pairs:
        raise ValueError(
            f"assessment matrix mismatch; missing={sorted(missing_pairs)}, "
            f"extra={sorted(extra_pairs)}"
        )
    return {
        "tools": len(tool_ids),
        "sources": len(source_ids),
        "dimensions": len(dimension_ids),
        "assessments": len(seen_pairs),
    }


if __name__ == "__main__":
    counts = validate()
    print(
        "state-of-field evidence valid: "
        + ", ".join(f"{name}={count}" for name, count in counts.items())
    )
