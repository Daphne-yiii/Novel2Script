from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chapter:
    id: str
    title: str
    order: int
    text: str
    summary: str


@dataclass(frozen=True)
class Character:
    id: str
    name: str
    role: str
    description: str
    traits: list[str]


@dataclass(frozen=True)
class Location:
    id: str
    name: str
    description: str


@dataclass(frozen=True)
class StoryAnalysis:
    characters: list[Character]
    locations: list[Location]
    timeline: list[str]
    major_events: list[str]
    tone: str
    conflicts: list[str]


@dataclass(frozen=True)
class ScenePlan:
    id: str
    order: int
    source_chapters: list[str]
    location_id: str
    time_of_day: str
    interior_exterior: str
    purpose: str
    character_ids: list[str]
    rewrite_strategy: list[str]


@dataclass(frozen=True)
class AdaptationPlan:
    scenes: list[ScenePlan]
