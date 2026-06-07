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
    traits: List[str]
   
    visual_anchor: str 
   
    speech_style: str

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
    conflicts: List[str]

@dataclass(frozen=True)
class ScenePlan:
    id: str
    order: int
    source_chapters: List[str]
    location_id: str
    time_of_day: str
    interior_exterior: str
    purpose: str
    character_ids: List[str]
    rewrite_strategy: List[str]
    
    subtext_conflict: str
    
    visual_narrative_plan: str

@dataclass(frozen=True)
class AdaptationPlan:
    scenes: List[ScenePlan]
