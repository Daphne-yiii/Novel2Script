# src/novel2script/models.py

from __future__ import annotations
from dataclasses import dataclass
from typing import List

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
    speech_style: dict[str, str]


@dataclass(frozen=True)
class Location:
    id: str
    name: str
    description: str
   
    atmosphere: str

@dataclass(frozen=True)
class StoryAnalysis:
    characters: List[Character]
    locations: List[Location]
    timeline: List[str]
    major_events: List[str]
    tone: str
    conflicts: list[str]
    story_bible: dict
    foreshadowing_ledger: list[dict]
    canon_facts: list[dict]
    rhythm_plan: dict
    coverage_report: dict


@dataclass(frozen=True)
class ScenePlan:
    id: str
    order: int
    source_chapters: List[str]
    location_id: str
    time_of_day: str
    interior_exterior: str
    purpose: str
    plot_function: str
    intensity: int
    character_ids: list[str]
    rewrite_strategy: list[str]


@dataclass(frozen=True)
class AdaptationPlan:
    scenes: List[ScenePlan]
