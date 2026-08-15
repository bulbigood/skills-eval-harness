from pathlib import Path

import pytest

from skills_eval_harness.cli import _codex_auth_args, _required_credentials, parser
from skills_eval_harness.models import load_config

ROOT = Path(__file__).resolve().parents[1]


def test_codex_auth_cli_supports_api_key_and_explicit_chatgpt_modes(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        parser().parse_args(["run", "--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    assert "--codex-auth {api-key,chatgpt}" in help_text
    assert "--codex-auth-json" in help_text
    assert "--judge-auth {api-key,chatgpt}" in help_text


def test_harbor_receives_only_generic_staged_auth_path() -> None:
    staged = Path("/tmp/skills-eval-auth-random/auth.json")
    assert _codex_auth_args(None) == []
    assert _codex_auth_args(staged) == [
        "--ae",
        "CODEX_AUTH_JSON_PATH=/tmp/skills-eval-auth-random/auth.json",
    ]


def test_subscription_worker_and_judge_require_no_platform_api_key() -> None:
    config = load_config(ROOT / "evals/config.yaml")
    assert _required_credentials(config, "codex", "chatgpt", "chatgpt") == set()
    assert _required_credentials(config, "codex", "chatgpt", "api-key") == {"OPENAI_API_KEY"}
    assert _required_credentials(config, "codex", "api-key", "chatgpt") == {"OPENAI_API_KEY"}
