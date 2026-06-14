"""Tests for jsonld_enricher.py — schema.org JSON-LD enrichment and validation."""

import json
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "scripts" / "python"))

from jsonld_enricher import enrich_file, process_directory, DIRECTORY_MAP

# --- enrich_file ---


class TestEnrichFile:
    def test_enrich_missing_context_and_type(self, tmp_path):
        """Inject @context and @type into a plain JSON file."""
        filepath = tmp_path / "test.json"
        filepath.write_text(json.dumps({"value": 42}))

        result = enrich_file(str(filepath), DIRECTORY_MAP["predictions"])
        assert result is True

        data = json.loads(filepath.read_text())
        assert data["@context"] == "https://schema.org"
        assert data["@type"] == "Observation"
        assert data["value"] == 42  # original field preserved

    def test_skip_already_enriched(self, tmp_path):
        """File with correct @context and @type should pass without changes."""
        filepath = tmp_path / "test.json"
        original = {
            "@context": "https://schema.org",
            "@type": "Observation",
            "value": 42,
        }
        filepath.write_text(json.dumps(original))

        result = enrich_file(str(filepath), DIRECTORY_MAP["predictions"])
        assert result is True

        data = json.loads(filepath.read_text())
        assert data == original  # unchanged

    def test_validate_only_fail(self, tmp_path):
        """--validate-only should reject missing @context."""
        filepath = tmp_path / "test.json"
        filepath.write_text(json.dumps({"value": 42}))

        result = enrich_file(
            str(filepath), DIRECTORY_MAP["predictions"], validate_only=True
        )
        assert result is False

    def test_validate_only_pass(self, tmp_path):
        """--validate-only should pass already enriched files."""
        filepath = tmp_path / "test.json"
        filepath.write_text(
            json.dumps(
                {"@context": "https://schema.org", "@type": "Observation", "value": 42}
            )
        )

        result = enrich_file(
            str(filepath), DIRECTORY_MAP["predictions"], validate_only=True
        )
        assert result is True

    def test_not_a_json_object(self, tmp_path):
        """JSON arrays should be skipped, not fail."""
        filepath = tmp_path / "test.json"
        filepath.write_text(json.dumps([1, 2, 3]))

        result = enrich_file(str(filepath), DIRECTORY_MAP["predictions"])
        assert result is True  # skipped

    def test_invalid_json(self, tmp_path):
        """Invalid JSON should return False."""
        filepath = tmp_path / "test.json"
        filepath.write_text("not json")

        result = enrich_file(str(filepath), DIRECTORY_MAP["predictions"])
        assert result is False

    def test_file_not_found(self):
        """Non-existent file should return False."""
        result = enrich_file("/nonexistent/path.json", DIRECTORY_MAP["predictions"])
        assert result is False

    @pytest.mark.parametrize(
        "directory", ["predictions", "market-data", "validation", "reports"]
    )
    def test_all_directory_types(self, tmp_path, directory):
        """Each directory type should get its correct @type."""
        filepath = tmp_path / "test.json"
        filepath.write_text(json.dumps({"value": 42}))

        enrich_file(str(filepath), DIRECTORY_MAP[directory])
        data = json.loads(filepath.read_text())
        assert data["@context"] == "https://schema.org"
        assert data["@type"] == DIRECTORY_MAP[directory]["@type"]


# --- process_directory ---


class TestProcessDirectory:
    def test_process_empty_directory(self, tmp_path):
        """No JSON files should result in 0 failures."""
        failures = process_directory(str(tmp_path))
        assert failures == 0

    def test_process_mixed_directory(self, tmp_path):
        """Mix of enriched, non-enriched, and non-JSON files."""
        workdir = tmp_path / "predictions"
        workdir.mkdir()

        # Already enriched
        (workdir / "already.json").write_text(
            json.dumps({"@context": "https://schema.org", "@type": "Observation"})
        )
        # Needs enrichment
        (workdir / "plain.json").write_text(json.dumps({"value": 1}))
        # Not a JSON object (array)
        (workdir / "array.json").write_text(json.dumps([1, 2, 3]))
        # Non-JSON file (should be ignored)
        (workdir / "notes.txt").write_text("hello")

        failures = process_directory(str(workdir), validate_only=False)
        assert failures == 0

        # Verify plain.json was enriched
        data = json.loads((workdir / "plain.json").read_text())
        assert data["@context"] == "https://schema.org"

    def test_directory_not_found(self):
        failures = process_directory("/nonexistent")
        assert failures == 0

    def test_directory_not_mapped(self, tmp_path):
        """Directories not in DIRECTORY_MAP should be skipped."""
        failures = process_directory(str(tmp_path))
        assert failures == 0
