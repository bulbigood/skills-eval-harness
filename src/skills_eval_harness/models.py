"""Strict immutable data models for Harbor evaluation inputs and outputs."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def validate_run_id(value: object) -> str:
    if type(value) is not str or not RUN_ID.fullmatch(value):
        raise ValueError("run_id must be a portable 1-128 character identifier")
    return value

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

class Arm(StrictModel):
    id: str
    skill: bool
    role: Literal["control", "treatment"] | None = None

class Suite(StrictModel):
    schema_version: Literal[1]
    id: str
    kind: Literal["absolute", "paired"]
    default_samples: int = Field(ge=1)
    scenarios: list[str]
    arms: list[Arm]

    @field_validator("schema_version", "default_samples", mode="before")
    @classmethod
    def reject_boolean_integers(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("integer fields do not accept booleans")
        return value

    @model_validator(mode="after")
    def validate_identity(self) -> "Suite":
        values = (self.id, *(a.id for a in self.arms), *self.scenarios)
        if any(not ID.fullmatch(value) for value in values):
            raise ValueError("suite, arm, and scenario IDs must be lowercase kebab-case")
        if len(self.scenarios) != len(set(self.scenarios)):
            raise ValueError("duplicate scenario IDs")
        arm_ids = [arm.id for arm in self.arms]
        if len(arm_ids) != len(set(arm_ids)):
            raise ValueError("duplicate arm IDs")
        if self.kind == "paired" and len(self.arms) != 2:
            raise ValueError("paired suites require exactly two arms")
        if self.kind == "paired" and {arm.role for arm in self.arms} != {"control", "treatment"}:
            raise ValueError("paired suites require exactly one control and one treatment arm")
        if self.kind == "paired" and any(arm.skill != (arm.role == "treatment") for arm in self.arms):
            raise ValueError("paired treatment must enable the skill and control must disable it")
        if self.kind == "absolute" and len(self.arms) != 1:
            raise ValueError("absolute suites require exactly one arm")
        if self.kind == "absolute" and self.arms[0].role is not None:
            raise ValueError("absolute suite arm must not declare a paired role")
        return self

class Container(StrictModel):
    image: str
    cpus: int = Field(ge=1)
    memory_mb: int = Field(ge=256)
    storage_mb: int = Field(ge=1024)
    network_mode: Literal["allowlist"]
    agent_hosts: dict[str, list[str]]
    verifier_network_mode: Literal["no-network"]

class Agent(StrictModel):
    harbor_name: Literal["codex", "claude-code"]
    model: str
    credential_env: Literal["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]

class Judge(StrictModel):
    model: str
    credential_env: Literal["OPENAI_API_KEY"]
    reasoning: Literal["low", "medium", "high"]
    timeout_seconds: int = Field(ge=1)

class Execution(StrictModel):
    timeout_seconds: int = Field(ge=1)
    global_concurrency: int = Field(ge=1, le=32)
    retries: Literal[0]

class HarnessConfig(StrictModel):
    schema_version: Literal[1]
    harbor_version: Literal["0.21.0"]
    container: Container
    agents: dict[str, Agent]
    judge: Judge
    execution: Execution
    runtimes: dict[str, str]
    skill_repositories: list[str]

    @field_validator("schema_version", mode="before")
    @classmethod
    def reject_boolean_schema_version(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("schema_version does not accept booleans")
        return value

    @model_validator(mode="after")
    def validate_agents(self) -> "HarnessConfig":
        if set(self.agents) != {"codex", "claude"}:
            raise ValueError("agents must declare exactly codex and claude")
        if set(self.runtimes) != {"0.18.0"} or any(
            re.fullmatch(r"[0-9a-f]{64}", digest) is None for digest in self.runtimes.values()
        ):
            raise ValueError("runtimes must bind exactly the supported version to a SHA-256 digest")
        if not self.skill_repositories or any(not value.startswith("https://") for value in self.skill_repositories):
            raise ValueError("skill repository registry must contain canonical HTTPS URLs")
        return self

def load_yaml(path: Path) -> object:
    return yaml.safe_load(path.read_text(encoding="utf-8"))

def load_suite(path: Path) -> Suite:
    return Suite.model_validate(load_yaml(path))

def load_config(path: Path) -> HarnessConfig:
    return HarnessConfig.model_validate(load_yaml(path))


def scenario_family(scenario: dict) -> str:
    families = scenario["command_families"]
    return "+".join(sorted(families)) if families else "no-command"
