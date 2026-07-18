from __future__ import annotations

from enum import StrEnum, auto
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class IslandStatus(StrEnum):
    WORKING = auto()
    VERIFYING = auto()
    WAITING = auto()
    BLOCKED = auto()
    PAUSED = auto()
    COMPLETED = auto()


class ControlAction(StrEnum):
    PAUSE = auto()
    STOP = auto()
    FOCUS_VIBE = auto()


class Criterion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    done: bool = False
    progress: str | None = None


class IslandState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["island_state"] = "island_state"
    goal: str
    state: IslandStatus
    detail: str = ""
    criteria: list[Criterion] = Field(default_factory=list)
    iteration: str | None = None
    elapsed: str | None = None
    cost: float | None = None
    budget: float | None = None
    evidence: list[str] = Field(default_factory=list)


class ControlMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["control"] = "control"
    action: ControlAction


def encode_jsonl(message: IslandState | ControlMessage) -> str:
    return message.model_dump_json() + "\n"


def parse_island_state(line: str) -> IslandState:
    return IslandState.model_validate_json(line)


def parse_control(line: str) -> ControlMessage:
    return ControlMessage.model_validate_json(line)
