from pathlib import Path

import pytest

from skills_eval_harness.fixtures import materialize_fixture, materialized_fixture_path


def test_core_read_fixture_materializes_expected_documents_and_schema(tmp_path: Path) -> None:
    source = tmp_path / "source"
    (source / "graph").mkdir(parents=True)
    (source / ".iwe").mkdir()
    (source / "graph/existing.md").write_text("# Existing\n", encoding="utf-8")
    (source / ".iwe/config.toml").write_text("[document]\n", encoding="utf-8")
    destination = tmp_path / "materialized"

    materialize_fixture(source, destination, "pkm-demo-core-read")

    assert (destination / "graph/existing.md").read_text() == "# Existing\n"
    assert "Coordinates the release." in (destination / "graph/core-alpha.md").read_text()
    assert "Records the direct implementation checklist." in (
        destination / "graph/core-beta.md"
    ).read_text()
    assert "blue-lantern handoff" in (destination / "graph/core-gamma.md").read_text()
    assert '[schemas.core]\nmatch = "core-*"' in (
        destination / ".iwe/config.toml"
    ).read_text()
    assert (destination / ".iwe/schemas/core.yaml").is_file()


def test_api_project_fixture_adds_project_frontmatter(tmp_path: Path) -> None:
    source = tmp_path / "source"
    (source / "graph").mkdir(parents=True)
    (source / "graph/api-integration.md").write_text(
        "# API Integration\n\nShip it.\n",
        encoding="utf-8",
    )
    destination = tmp_path / "materialized"

    materialize_fixture(source, destination, "pkm-demo-api-project")

    assert (destination / "graph/api-integration.md").read_text() == (
        "---\ntype: project\n---\n\n# API Integration\n\nShip it.\n"
    )


def test_materialized_fixture_path_is_scoped_to_sealed_root(tmp_path: Path) -> None:
    expected = tmp_path / "inputs/materialized-fixtures/pkm-demo-core-read/graph/core-beta.md"
    assert materialized_fixture_path(
        tmp_path, "pkm-demo-core-read", "graph/core-beta.md"
    ) == expected
    with pytest.raises(ValueError, match="escapes"):
        materialized_fixture_path(tmp_path, "pkm-demo-core-read", "../../../secret")
