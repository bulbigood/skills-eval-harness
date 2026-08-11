"""Workspace lifecycle, fixture setup, and process environments."""
from __future__ import annotations

import hashlib
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVAL = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from skill_manifest import SkillSpec, verify_runtime_binary
from .scenarios import Scenario


SAFE_HOST_ENV = (
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "NO_COLOR",
    "TERM",
    "TMPDIR",
    "TZ",
)


def eval_environment(
    isolated_home: Path,
    codex_home: Path,
    shim_bin: Path,
    iwe_binary: Path,
    temporary: Path,
    agent_implementation: str = "codex",
    workspace: Path | None = None,
) -> dict[str, str]:
    env = {key: os.environ[key] for key in SAFE_HOST_ENV if key in os.environ}
    task_path = f"{shim_bin}:{iwe_binary.parent}:" + os.environ.get("PATH", "")
    temporary.mkdir(parents=True, exist_ok=True)
    shell_environment = temporary / "eval-shell-environment.sh"
    shell_environment.write_text(
        f"export PATH={shlex.quote(task_path)}\n",
        encoding="utf-8",
    )
    log_root = (workspace or temporary) / ".iwe-eval-harness"
    log_root.mkdir(parents=True, exist_ok=True)
    env.update({
        "HOME": str(isolated_home),
        "CODEX_HOME": str(codex_home),
        "PATH": task_path,
        "BASH_ENV": str(shell_environment),
        "IWE_EVAL_BLOCK_LOG": str(log_root / "blocked-tools.log"),
        "IWE_EVAL_IWE_LOG": str(log_root / "iwe-telemetry.jsonl"),
    })
    if agent_implementation == "claude":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            env["ANTHROPIC_API_KEY"] = api_key
        env["CLAUDE_CODE_SUBPROCESS_ENV_SCRUB"] = "1"
    return env


def judge_environment(
    home: Path, codex_home: Path, tool_bin: Path, agent_implementation: str = "codex"
) -> dict[str, str]:
    env = {key: os.environ[key] for key in SAFE_HOST_ENV if key in os.environ}
    env.update({
        "HOME": str(home),
        "CODEX_HOME": str(codex_home),
        "PATH": f"{tool_bin}:/usr/bin:/bin",
    })
    if agent_implementation == "claude":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            env["ANTHROPIC_API_KEY"] = api_key
        env["CLAUDE_CODE_SUBPROCESS_ENV_SCRUB"] = "1"
    return env


def ensure_fixture(config: dict, name: str, cache: Path) -> Path:
    base_name = "seventeen-centuries" if name.startswith("seventeen-centuries") else "pkm-demo"
    spec = config["fixtures"][base_name]
    target = cache / base_name
    if not target.exists():
        subprocess.run(["git", "clone", "--quiet", spec["repository"], str(target)], check=True)
    subprocess.run(["git", "-C", str(target), "fetch", "--quiet", "origin", spec["commit"]], check=True)
    actual = subprocess.run(["git", "-C", str(target), "rev-parse", spec["commit"]], text=True, capture_output=True, check=True).stdout.strip()
    if actual != spec["commit"]:
        raise RuntimeError(f"fixture pin mismatch for {base_name}: {actual}")
    subprocess.run(
        ["git", "-C", str(target), "checkout", "--quiet", "--detach", "--force", actual],
        check=True,
    )
    subprocess.run(["git", "-C", str(target), "clean", "-ffdqx"], check=True)
    head = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    if head != spec["commit"]:
        raise RuntimeError(f"fixture checkout mismatch for {base_name}: {head}")
    return target


def prepare(workspace: Path, fixture: str) -> None:
    if fixture == "pkm-demo-api-project":
        path = workspace / "graph/api-integration.md"
        path.write_text(
            "---\ntype: project\n---\n\n" + path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    elif fixture == "pkm-demo-update":
        (workspace / "graph/eval-roadmap.md").write_text(
            "---\ntype: project\nstatus: draft\n---\n\n# Evaluation Roadmap\n\n## Goals\n\nShip safely.\n\n## Status\n\nIn review.\n\n## Unrelated\n\nPreserve this exact paragraph.\n",
            encoding="utf-8",
        )
    elif fixture == "pkm-demo-extract-inline":
        (workspace / "graph/eval-plan.md").write_text(
            "# Evaluation Plan\n\nIntro.\n\n## Architecture\n\nUse a graph-aware boundary.\n\n### Storage\n\nMarkdown files.\n\n## Delivery\n\nPreserve this section.\n",
            encoding="utf-8",
        )
    elif fixture == "pkm-demo-schema":
        config = workspace / ".iwe/config.toml"
        config.write_text(config.read_text(encoding="utf-8") + '''

[templates.meeting]
key_template = "meetings/{{slug}}"
document_template = """
# {{title}}

## Attendees

{{attendees}}

## Notes

{{body}}"""

[schemas.meeting]
match = "meetings/**"
''', encoding="utf-8")
        schemas = workspace / ".iwe/schemas"
        schemas.mkdir(parents=True, exist_ok=True)
        (schemas / "meeting.yaml").write_text("""$schema: https://document-schema.org/draft/2026-06/schema
frontmatter:
  type: object
  required: [type, draft]
  properties:
    type:
      const: meeting
    draft:
      type: boolean
sections:
  - header: { pattern: ".+" }
    maxContains: 1
    sections:
      - header: { const: Attendees }
        maxContains: 1
      - header: { const: Notes }
        maxContains: 1
    additionalSections: false
additionalSections: false
""", encoding="utf-8")
    elif fixture == "pkm-demo-core-read":
        graph = workspace / "graph"
        (graph / "core-alpha.md").write_text(
            "---\ntype: project\npriority: 2\n---\n\n# Core Alpha\n\nCoordinates the release.\n\n[Core Beta](core-beta.md)\n",
            encoding="utf-8",
        )
        (graph / "core-beta.md").write_text(
            "---\ntype: note\npriority: 1\n---\n\n# Core Beta\n\nRecords the direct implementation checklist.\n",
            encoding="utf-8",
        )
        (graph / "core-gamma.md").write_text(
            "---\ntype: project\npriority: 3\n---\n\n# Core Gamma\n\nTracks the higher-priority migration. The rollout uses staged cutovers and rollback checkpoints under the blue-lantern handoff.\n",
            encoding="utf-8",
        )
        config = workspace / ".iwe/config.toml"
        config.write_text(
            config.read_text(encoding="utf-8")
            + '\n[schemas.core]\nmatch = "core-*"\n',
            encoding="utf-8",
        )
        schemas = workspace / ".iwe/schemas"
        schemas.mkdir(parents=True, exist_ok=True)
        (schemas / "core.yaml").write_text(
            "$schema: https://document-schema.org/draft/2026-06/schema\n"
            "frontmatter:\n"
            "  type: object\n"
            "  required: [type, priority]\n"
            "  properties:\n"
            "    type: { type: string }\n"
            "    priority: { type: number }\n",
            encoding="utf-8",
        )
    elif fixture == "pkm-demo-core-write":
        graph = workspace / "graph"
        documents = {
            "core-edit.md": "---\nstatus: draft\ntemporary: remove-me\n---\n\n# Core Edit\n\nBody must remain unchanged.\n",
            "core-body.md": "---\ntype: memo\nowner: Ada\n---\n\n# Old Body\n\nReplace all of this.\n",
            "core-blocks.md": "# Core Blocks\n\n## Keep\n\nPreserve.\n\n## Remove Me\n\nDelete this block.\n\n## Tail\n\nFinish.\n",
            "core-old.md": "# Core Old\n\nRename this note.\n",
            "core-referrer.md": "# Core Referrer\n\n[Core Old](core-old.md)\n",
            "core-child.md": "# Core Child\n\nReusable child text.\n",
            "core-parent.md": "# Core Parent\n\n[Core Child](core-child.md)\n",
            "core-source.md": "# Core Source\n\nAttach this note.\n",
            "core-delete.md": "# Core Delete\n\nDeletion target.\n",
            "core-delete-ref.md": "# Delete Referrer\n\n[Core Delete](core-delete.md)\n",
            "core-local-text.md": "# Core Local Text\n\n## Deployment\n\nRuns in three regions.\n\n## Operations\n\nPreserve this paragraph.\n",
            "core-block-replace.md": "# Core Block Replace\n\n## Preparation\n\nKeep snapshots.\n\n## Rollback\n\nUse the emergency procedure.\n\n## Follow-up\n\nRecord the outcome.\n",
        }
        for name, content in documents.items():
            (graph / name).write_text(content, encoding="utf-8")
        config = workspace / ".iwe/config.toml"
        config.write_text(
            config.read_text(encoding="utf-8")
            + '\n[actions.inbox]\ntype = "attach"\ntitle = "Attach to inbox"\nkey_template = "inbox"\ndocument_template = """\n# Inbox\n\n{{content}}\n"""\n',
            encoding="utf-8",
        )
    elif fixture == "pkm-demo-context-routing":
        graph = workspace / "graph"
        decisions = graph / "decisions"
        runbooks = graph / "runbooks"
        decisions.mkdir(parents=True, exist_ok=True)
        runbooks.mkdir(parents=True, exist_ok=True)
        (decisions / "queue-backpressure.md").write_text(
            "# Queue Backpressure Decision\n\n"
            "We cap queue backpressure at 500 pending jobs to protect downstream recovery time.\n",
            encoding="utf-8",
        )
        (runbooks / "payment-ledger-recovery.md").write_text(
            "# Payment Ledger Recovery\n\n"
            "1. Pause ingestion.\n"
            "2. Replay the ledger.\n"
            "3. Verify the zero-drift check.\n"
            "4. Resume ingestion.\n",
            encoding="utf-8",
        )
        docs = workspace / "docs"
        operations = workspace / "operations"
        docs.mkdir(exist_ok=True)
        operations.mkdir(exist_ok=True)
        (docs / "contributor-prerequisites.md").write_text(
            "# Contributor prerequisites\n\nPython 3.13 is required.\n",
            encoding="utf-8",
        )
        (operations / "violet-harbor-recovery.md").write_text(
            "# Violet Harbor recovery\n\nRecovery mode: single-writer.\n",
            encoding="utf-8",
        )
    elif fixture == "pkm-demo-retry-code":
        source = workspace / "src"
        tests = workspace / "tests"
        source.mkdir(exist_ok=True)
        tests.mkdir(exist_ok=True)
        (source / "__init__.py").write_text("", encoding="utf-8")
        (source / "retry.py").write_text(
            "def retry_delays(attempts):\n"
            "    return [2 ** index for index in range(attempts + 1)]\n",
            encoding="utf-8",
        )
        (tests / "test_retry.py").write_text(
            "import unittest\n\n"
            "from src.retry import retry_delays\n\n\n"
            "class RetryDelaysTest(unittest.TestCase):\n"
            "    def test_returns_one_delay_per_attempt(self):\n"
            "        cases = {0: [], 1: [1], 3: [1, 2, 4]}\n"
            "        for attempts, expected in cases.items():\n"
            "            with self.subTest(attempts=attempts):\n"
            "                self.assertEqual(retry_delays(attempts), expected)\n",
            encoding="utf-8",
        )


def install_skill(workspace: Path, skill: SkillSpec | None) -> None:
    if skill is None:
        return
    destination = workspace / ".agents/guidance"
    shutil.copytree(skill.path, destination)


def install_agents_file(
    workspace: Path,
    source: Path | None,
    context: dict[str, str] | None = None,
) -> Path | None:
    if source is None:
        return None
    destination = workspace / "AGENTS.md"
    if destination.exists():
        raise RuntimeError("worker fixture already contains AGENTS.md")
    if source.suffix == ".tmpl":
        context = context or {}
        command = [
            sys.executable,
            str(ROOT / "scripts/render_iwe_context_agents.py"),
            "--template", str(source),
            "--output", str(destination),
        ]
        for key, option in (
            ("iwe_root", "--iwe-root"),
            ("iwe_documents", "--iwe-documents"),
            ("iwe_language", "--iwe-language"),
        ):
            if key in context:
                command.extend([option, context[key]])
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=10)
    else:
        shutil.copy2(source, destination)
    return destination


def agents_file_provenance(source: Path | None) -> dict | None:
    if source is None:
        return None
    payload = source.read_bytes()
    return {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def preinjected_guidance_bytes(source: Path | None) -> int:
    provenance = agents_file_provenance(source)
    return 0 if provenance is None else provenance["bytes"]


def remove_tested_skill_for_judge(workspace: Path) -> None:
    agents = workspace / ".agents"
    if agents.exists():
        shutil.rmtree(agents)
    if agents.exists():
        raise RuntimeError("tested skill remained in judge workspace")


def create_judge_workspace(temporary: Path) -> Path:
    workspace = temporary / "judge-workspace"
    workspace.mkdir()
    if any(workspace.iterdir()):
        raise RuntimeError("judge workspace must start empty")
    return workspace


def verify_iwe_binary(skill: SkillSpec) -> Path:
    return verify_runtime_binary(skill)


def install_command_shims(
    bin_dir: Path,
    scenario: Scenario,
    real_iwe: Path,
    *,
    allow_filesystem_tools: bool = False,
) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    for source in (EVAL / "shims").iterdir():
        if source.is_file():
            if (
                (
                    allow_filesystem_tools
                    or scenario.skill_activation == "forbidden"
                    or scenario.allow_broad_fallback
                )
                and source.name in {"grep", "rg", "find"}
            ):
                continue
            target = bin_dir / source.name
            shutil.copy2(source, target)
            target.chmod(0o755)

    iwe_shim = bin_dir / "iwe"
    iwe_shim.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, pathlib, subprocess, sys\n"
        f"REAL = {str(real_iwe)!r}\n"
        f"MODE = {scenario.iwe_mode!r}\n"
        f"MAX_OUTPUT = {scenario.max_output_bytes!r}\n"
        "ARGS = sys.argv[1:]\n"
        "def finish(code, stdout=b'', stderr=b''):\n"
        "    raw_stdout_bytes = len(stdout)\n"
        "    if raw_stdout_bytes > MAX_OUTPUT:\n"
        "        stdout = stdout[:MAX_OUTPUT]\n"
        "        stderr += b'\\neval shim: stdout exceeded configured budget and was truncated\\n'\n"

        "    count = None\n"
        "    try:\n"
        "        value = json.loads(stdout.decode('utf-8'))\n"
        "        count = len(value) if isinstance(value, list) else None\n"
        "    except (UnicodeDecodeError, json.JSONDecodeError):\n"
        "        pass\n"
        "    record = {'args': ARGS, 'exit_code': code, "
        "'stdout_bytes': raw_stdout_bytes, 'emitted_stdout_bytes': len(stdout), "
        "'stderr_bytes': len(stderr), "
        "'result_count': count, 'stdout': stdout.decode('utf-8', errors='replace'), "
        "'stderr': stderr.decode('utf-8', errors='replace')}\n"
        "    log = os.environ.get('IWE_EVAL_IWE_LOG')\n"
        "    if log:\n"
        "        with open(log, 'a', encoding='utf-8') as handle:\n"
        "            handle.write(json.dumps(record, separators=(',', ':')) + '\\n')\n"
        "    sys.stdout.buffer.write(stdout)\n"
        "    sys.stderr.buffer.write(stderr)\n"
        "    raise SystemExit(code)\n"
        "if MODE == 'unavailable':\n"
        "    finish(127, stderr=b'iwe: command not found\\n')\n"
        "completed = subprocess.run([REAL, *ARGS], capture_output=True)\n"
        "finish(completed.returncode, completed.stdout, completed.stderr)\n",
        encoding="utf-8",
    )
    iwe_shim.chmod(0o755)


def assert_workspace_ready(workspace: Path, guidance_path: Path | None = None) -> None:
    """Fail before model calls when the prepared workspace cannot be used reliably."""
    try:
        resolved_workspace = workspace.resolve(strict=True)
    except FileNotFoundError as exc:
        raise RuntimeError(f"prepared workspace is missing: {workspace}") from exc
    if not resolved_workspace.is_dir() or not os.access(resolved_workspace, os.R_OK | os.X_OK):
        raise RuntimeError(f"prepared workspace is not readable: {resolved_workspace}")
    if guidance_path is None:
        return
    try:
        resolved_guidance = guidance_path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise RuntimeError(f"installed guidance is not readable: {guidance_path}") from exc
    if not resolved_guidance.is_relative_to(resolved_workspace):
        raise RuntimeError("installed guidance escaped the prepared workspace")
    if not resolved_guidance.is_file() or not os.access(resolved_guidance, os.R_OK):
        raise RuntimeError(f"installed guidance is not readable: {resolved_guidance}")
