from hashlib import sha256
from pathlib import Path


def test_immutable_report_archive_matches_checksum_manifest() -> None:
    root = Path(__file__).parents[1] / "reports"
    lines = (root / "archive-sha256.txt").read_text().splitlines()
    assert len(lines) == 7
    manifested = set()
    for line in lines:
        digest, name = line.split("  ", 1)
        manifested.add(name)
        assert sha256((root / name).read_bytes()).hexdigest() == digest
    archived = {
        path.name for path in root.glob("skills-eval-production-ab-*-v[1-7].md")
    }
    expected = {
        f"skills-eval-production-ab-20260816-v{revision}.md" for revision in range(1, 8)
    }
    assert archived == expected == manifested
