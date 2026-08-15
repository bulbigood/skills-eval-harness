"""Generate self-contained Harbor v1.1 task datasets."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from harbor.models.task.config import TaskConfig

from .hashing import atomic_write, canonical_json, sha256_file, sha256_tree
from .models import HarnessConfig, Suite, load_yaml

SKILL_LOAD_PATTERN = r'''^const r = await tools\.exec_command\(\{cmd:"sed -n '1,[0-9]+p' /root/\.agents/skills/[a-zA-Z0-9_.-]+/SKILL\.md",(?:workdir:"/workspace",)?yield_time_ms:[0-9]+,max_output_tokens:[0-9]+\}\);[ \n]*text\(r\.output\);\n$'''

VERIFIER = r'''#!/usr/bin/env python3
import hashlib, json, os, re
from pathlib import Path

def tree(root):
    rows=[]
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        if path.is_symlink():
            target=path.resolve()
            if not target.is_relative_to(root.resolve()):
                raise ValueError(f"escaping symlink: {path}")
        if path.is_file():
            rows.append({"path":path.relative_to(root).as_posix(),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"bytes":path.stat().st_size})
    return rows

trajectory=Path("/logs/agent/trajectory.json")
if not trajectory.is_file():
    raise ValueError("missing declared agent trajectory")
document=json.loads(trajectory.read_text(encoding="utf-8"))
if not isinstance(document,dict) or not isinstance(document.get("steps"),list):
    raise ValueError("malformed ATIF trajectory")
workspace=Path("/workspace")
manifest=tree(workspace)
before=json.loads(Path("/tests/before-tree.json").read_text(encoding="utf-8"))
policy=json.loads(Path("/tests/policy.json").read_text(encoding="utf-8"))
def collect_tools(value):
    if isinstance(value,dict):
        own=value.get("tool_calls",[]) if isinstance(value.get("tool_calls"),list) else []
        nested=[]
        for key,item in value.items():
            if key != "tool_calls": nested.extend(collect_tools(item))
        return own+nested
    if isinstance(value,list):
        return [call for item in value for call in collect_tools(item)]
    return []
skill_load=re.compile(SKILL_LOAD_PATTERN)
def is_skill_load(call):
    if not isinstance(call,dict) or call.get("function_name") != "exec": return False
    arguments=call.get("arguments")
    return isinstance(arguments,dict) and set(arguments)=={"input"} and isinstance(arguments["input"],str) and skill_load.fullmatch(arguments["input"]) is not None
all_tool_calls=collect_tools(document)
setup_tool_calls=sum(is_skill_load(call) for call in all_tool_calls)
tool_calls=len(all_tool_calls)-setup_tool_calls
unchanged=manifest==before
failures=[]
if policy["read_only"] and not unchanged: failures.append("read-only scenario modified workspace")
hard_max=policy.get("hard_max_task_tool_calls")
if hard_max is not None and tool_calls>hard_max: failures.append("hard tool-call maximum exceeded")
payload={"workspace":manifest,"baseline_unchanged":unchanged,"tool_calls":tool_calls,"setup_tool_calls":setup_tool_calls,"total_tool_calls":len(all_tool_calls),"failures":failures,"trajectory_sha256":hashlib.sha256(trajectory.read_bytes()).hexdigest()}
Path("/logs/verifier/workspace-manifest.json").write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8")
Path("/logs/verifier/mechanical.json").write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8")
Path("/logs/verifier/reward.json").write_text(json.dumps({"infrastructure":0.0 if failures else 1.0}),encoding="utf-8")
'''
VERIFIER = VERIFIER.replace("SKILL_LOAD_PATTERN", repr(SKILL_LOAD_PATTERN), 1)

TEST_SH = "#!/bin/sh\nset -eu\npython3 /tests/verify.py\n"

def _copy(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination) if destination.is_dir() else destination.unlink()
    if source.is_dir():
        shutil.copytree(source, destination, symlinks=False)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

def _tree_manifest(root: Path) -> list[dict[str, object]]:
    return [
        {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path), "bytes": path.stat().st_size}
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
    ]

def scenario_map(path: Path) -> dict[str, dict]:
    document = load_yaml(path)
    if document.get("schema_version") != 2 or not isinstance(document.get("scenarios"), list):
        raise ValueError("scenario catalog must use schema_version 2")
    scenarios = {item["id"]: item for item in document["scenarios"]}
    if len(scenarios) != len(document["scenarios"]):
        raise ValueError("duplicate scenario IDs")
    return scenarios

def task_toml(*, name: str, fixture: str, config: HarnessConfig, agent: str) -> str:
    c = config.container
    return f'''schema_version = "1.4"
artifacts = ["/workspace", "/logs/agent/trajectory.json"]

[task]
name = "iwe/{name}"
description = "IWE skill evaluation: {name}"
authors = []

[metadata]
fixture = "{fixture}"
harness_protocol = "iwe-harbor-v1"

[agent]
timeout_sec = 1800.0
network_mode = "allowlist"
allowed_hosts = {json.dumps(list(c.agent_hosts[agent]))}

[verifier]
timeout_sec = 300.0
environment_mode = "separate"

[environment]
build_timeout_sec = 600.0
cpus = {c.cpus}
memory_mb = {c.memory_mb}
storage_mb = {c.storage_mb}
gpus = 0
network_mode = "public"
mcp_servers = []

[verifier.environment]
build_timeout_sec = 600.0
cpus = {c.cpus}
memory_mb = {c.memory_mb}
storage_mb = {c.storage_mb}
gpus = 0
network_mode = "no-network"
mcp_servers = []
'''

def generate_dataset(*, root: Path, suite: Suite, config: HarnessConfig, catalog_path: Path, fixture_roots: dict[str, Path], runtime: Path, arm: str, agent: str = "codex", samples: int = 1, agents_template: bytes | None = None) -> Path:
    if arm not in {item.id for item in suite.arms}:
        raise ValueError(f"unknown arm {arm!r}")
    if agent not in config.agents or samples < 1:
        raise ValueError("unknown agent or invalid sample count")
    scenarios = scenario_map(catalog_path)
    missing = sorted(set(suite.scenarios) - set(scenarios))
    if missing:
        raise ValueError(f"suite references unknown scenarios: {missing}")
    output = root / suite.id / arm
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for scenario_id in suite.scenarios:
        scenario = scenarios[scenario_id]
        fixture_name = scenario["fixture"]
        fixture_root = fixture_roots.get(fixture_name) or fixture_roots.get("pkm-demo" if fixture_name.startswith("pkm-demo") else fixture_name)
        if fixture_root is None or not fixture_root.is_dir():
            raise ValueError(f"missing materialized fixture {fixture_name!r}")
        for sample in range(1, samples + 1):
            task_id = f"{scenario_id}--sample-{sample:03d}"
            task = output / task_id
            (task / "environment/payload/workspace").mkdir(parents=True)
            (task / "tests").mkdir(parents=True)
            _copy(fixture_root, task / "environment/payload/workspace")
            if agents_template is not None:
                (task / "environment/payload/workspace/AGENTS.md").write_bytes(agents_template)
            _copy(runtime, task / "environment/payload/usr/local/bin/iwe")
            (task / "environment/payload/usr/local/bin/iwe").chmod(0o755)
            image = config.container.image
            (task / "environment/Dockerfile").write_text(f"FROM {image}\nCOPY payload/ /\nWORKDIR /workspace\n", encoding="utf-8")
            (task / "tests/Dockerfile").write_text(f"FROM {image}\nCOPY . /tests/\n", encoding="utf-8")
            (task / "tests/verify.py").write_text(VERIFIER, encoding="utf-8")
            (task / "tests/test.sh").write_text(TEST_SH, encoding="utf-8")
            (task / "tests/test.sh").chmod(0o755)
            write_capability = any(str(capability).startswith("write.") for capability in scenario.get("capabilities", []))
            runtime_policy = scenario.get("runtime") or {}
            efficiency = scenario.get("efficiency") or {}
            hard_max = runtime_policy.get("hard_max_task_tool_calls")
            if hard_max is None and efficiency.get("task_tool_calls"):
                hard_max = efficiency["task_tool_calls"][1]
            atomic_write(task / "tests/before-tree.json", canonical_json(_tree_manifest(task / "environment/payload/workspace")))
            atomic_write(task / "tests/policy.json", canonical_json({"read_only": not write_capability, "hard_max_task_tool_calls": hard_max}))
            (task / "instruction.md").write_text(f"Work offline.\n\nRequest:\n{scenario['request']}\n", encoding="utf-8")
            text = task_toml(name=task_id, fixture=fixture_name, config=config, agent=agent)
            TaskConfig.model_validate_toml(text)
            (task / "task.toml").write_text(text, encoding="utf-8")
            manifest = {"protocol": "iwe-harbor-v1", "scenario_id": scenario_id, "sample": sample, "fixture_sha256": sha256_tree(fixture_root), "runtime_sha256": sha256_file(runtime), "task_sha256": sha256_tree(task)}
            atomic_write(task / "manifest.json", canonical_json(manifest))
    return output
