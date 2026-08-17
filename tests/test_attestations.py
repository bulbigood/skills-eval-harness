from skills_eval_harness.attestations import fallback_attestation


def call(command: str) -> dict:
    import json
    source = 'const r=await tools.exec_command({cmd:' + json.dumps(command) + '});'
    return {"source": "agent", "tool_calls": [{"arguments": {"input": source}}]}


def test_fallback_attestation_accepts_only_one_scoped_read_after_iwe() -> None:
    document = {"steps": [call("iwe retrieve graph/eval-roadmap.md"), call("sed -n '1,80p' graph/eval-roadmap.md")]}
    assert fallback_attestation(document, "graph/eval-roadmap.md") == {
        "protocol": "fallback-attestation-v1",
        "runtime_attempt_observed": True,
        "targeted_fallback_observed": True,
        "declared_path": "graph/eval-roadmap.md",
        "unrelated_post_failure_tool_call_observed": False,
    }


def test_fallback_attestation_fails_closed_on_broad_or_opaque_calls() -> None:
    document = {"steps": [call("iwe retrieve graph/eval-roadmap.md"), call("find graph -type f"), call("cat graph/eval-roadmap.md")]}
    result = fallback_attestation(document, "graph/eval-roadmap.md")
    assert result["targeted_fallback_observed"] is False
    assert result["unrelated_post_failure_tool_call_observed"] is True


def test_fallback_attestation_requires_retrieve_attempt() -> None:
    document = {"steps": [call("iwe validate graph/eval-roadmap.md"), call("cat graph/eval-roadmap.md")]}
    result = fallback_attestation(document, "graph/eval-roadmap.md")
    assert result["runtime_attempt_observed"] is False


def test_fallback_attestation_accepts_bounded_awk_but_rejects_awk_escape() -> None:
    retrieve = call("iwe retrieve graph/eval-roadmap.md")
    bounded = call("awk '/^## Status/{p=1;next}/^## /{p=0}p; END{if(p>0) print p}' graph/eval-roadmap.md")
    assert fallback_attestation({"steps": [retrieve, bounded]}, "graph/eval-roadmap.md")["targeted_fallback_observed"] is True
    escaped = call("awk 'BEGIN{print 1 > \"/tmp/leak\"}' graph/eval-roadmap.md")
    result = fallback_attestation({"steps": [retrieve, escaped]}, "graph/eval-roadmap.md")
    assert result["targeted_fallback_observed"] is False
    assert result["unrelated_post_failure_tool_call_observed"] is True
