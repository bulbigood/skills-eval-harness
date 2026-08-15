from __future__ import annotations

import re
import shutil
from pathlib import Path

from harbor.models.task.config import TaskConfig

from skills_eval_harness.dataset import SKILL_LOAD_PATTERN, generate_dataset
from skills_eval_harness.hashing import sha256_tree
from skills_eval_harness.models import load_config, load_suite

ROOT = Path(__file__).resolve().parents[1]


def fixture_inputs(tmp_path: Path) -> tuple[Path, dict[str, Path]]:
    runtime = tmp_path / "iwe"
    shutil.copy2("/bin/true", runtime)
    fixture = tmp_path / "pkm-demo"
    fixture.mkdir()
    (fixture / "note.md").write_text("# Demo\n", encoding="utf-8")
    return runtime, {"pkm-demo": fixture}


def test_generated_task_is_valid_separate_sandbox_and_pinned_image(tmp_path: Path) -> None:
    runtime, fixtures = fixture_inputs(tmp_path)
    suite = load_suite(ROOT / "evals/suites/skill-guidance-ab.yaml")
    dataset = generate_dataset(
        root=tmp_path / "datasets",
        suite=suite.model_copy(update={"scenarios": ("summarize-one-topic",)}),
        config=load_config(ROOT / "evals/config.yaml"),
        catalog_path=ROOT / "evals/scenarios/iwe.yaml",
        fixture_roots=fixtures,
        runtime=runtime,
        arm="skill",
        agent="codex",
    )
    task = dataset / "summarize-one-topic--sample-001"
    parsed = TaskConfig.model_validate_toml((task / "task.toml").read_text())
    assert parsed.verifier.environment_mode.value == "separate"
    assert parsed.environment.network_mode.value == "public"
    assert parsed.agent.network_mode.value == "allowlist"
    assert parsed.agent.allowed_hosts == list(load_config(ROOT / "evals/config.yaml").container.agent_hosts["codex"])
    assert parsed.verifier.environment.network_mode.value == "no-network"
    dockerfile = (task / "environment/Dockerfile").read_text()
    assert "@sha256:" in dockerfile
    verifier = (task / "tests/verify.py").read_text()
    assert "setup_tool_calls" in verifier
    assert "skill_load=re.compile(" in verifier
    assert "auth.json" not in sha256_tree(task)
    assert (task / "manifest.json").is_file()


def test_skill_load_classifier_excludes_only_the_bounded_skill_read() -> None:
    with_workdir = 'const r = await tools.exec_command({cmd:"sed -n \'1,240p\' /root/.agents/skills/iwe-v18/SKILL.md",workdir:"/workspace",yield_time_ms:10000,max_output_tokens:12000}); text(r.output);\n'
    without_workdir = 'const r = await tools.exec_command({cmd:"sed -n \'1,240p\' /root/.agents/skills/iwe-v18/SKILL.md",yield_time_ms:10000,max_output_tokens:20000}); text(r.output);\n'
    multiline = with_workdir.replace("}); text", "});\ntext")
    compound = with_workdir.replace("SKILL.md\"", "SKILL.md && iwe status\"")
    assert re.fullmatch(SKILL_LOAD_PATTERN, with_workdir)
    assert re.fullmatch(SKILL_LOAD_PATTERN, without_workdir)
    assert re.fullmatch(SKILL_LOAD_PATTERN, multiline)
    assert not re.fullmatch(SKILL_LOAD_PATTERN, compound)


def test_pair_generation_is_byte_symmetric_except_arm_metadata(tmp_path: Path) -> None:
    runtime, fixtures = fixture_inputs(tmp_path)
    suite = load_suite(ROOT / "evals/suites/skill-guidance-ab.yaml").model_copy(update={"scenarios": ("summarize-one-topic",)})
    config = load_config(ROOT / "evals/config.yaml")
    guided = generate_dataset(root=tmp_path / "datasets", suite=suite, config=config, catalog_path=ROOT / "evals/scenarios/iwe.yaml", fixture_roots=fixtures, runtime=runtime, arm="skill")
    control = generate_dataset(root=tmp_path / "datasets", suite=suite, config=config, catalog_path=ROOT / "evals/scenarios/iwe.yaml", fixture_roots=fixtures, runtime=runtime, arm="no-skill")
    for relative in ("instruction.md", "environment/Dockerfile", "tests/Dockerfile", "tests/test.sh", "tests/verify.py"):
        assert (guided / "summarize-one-topic--sample-001" / relative).read_bytes() == (control / "summarize-one-topic--sample-001" / relative).read_bytes()
