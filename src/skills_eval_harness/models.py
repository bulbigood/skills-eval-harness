"""Strict immutable data models for Harbor evaluation inputs and outputs."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

class Arm(StrictModel):
    id: str
    skill: bool

class Suite(StrictModel):
    schema_version: Literal[1]
    id: str
    kind: Literal["absolute", "paired"]
    default_samples: int = Field(ge=1)
    scenarios: tuple[str, ...]
    arms: tuple[Arm, ...]

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
        if self.kind == "absolute" and len(self.arms) != 1:
            raise ValueError("absolute suites require exactly one arm")
        return self

class Container(StrictModel):
    image: str
    cpus: int = Field(ge=1)
    memory_mb: int = Field(ge=256)
    storage_mb: int = Field(ge=1024)
    network_mode: Literal["allowlist"]
    agent_hosts: dict[str, tuple[str, ...]]
    verifier_network_mode: Literal["no-network"]

class Agent(StrictModel):
    harbor_name: Literal["codex", "claude-code"]
    model: str
    credential_env: Literal["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]

class Judge(StrictModel):
    provider: Literal["openai"]
    model: str
    credential_env: Literal["OPENAI_API_KEY"]
    reasoning: Literal["low", "medium", "high"]
    timeout_seconds: int = Field(ge=1)

class Execution(StrictModel):
    timeout_seconds: int = Field(ge=1)
    max_concurrency: int = Field(ge=1, le=32)
    retries: Literal[0]

class HarnessConfig(StrictModel):
    schema_version: Literal[1]
    harbor_version: Literal["0.21.0"]
    container: Container
    agents: dict[str, Agent]
    judge: Judge
    execution: Execution

    @model_validator(mode="after")
    def validate_agents(self) -> "HarnessConfig":
        if set(self.agents) != {"codex", "claude"}:
            raise ValueError("agents must declare exactly codex and claude")
        return self

def load_yaml(path: Path) -> object:
    return yaml.safe_load(path.read_text(encoding="utf-8"))

def load_suite(path: Path) -> Suite:
    return Suite.model_validate(load_yaml(path))

def load_config(path: Path) -> HarnessConfig:
    return HarnessConfig.model_validate(load_yaml(path))

load_harness_config = load_config
