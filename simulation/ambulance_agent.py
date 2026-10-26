
"""An ambulance agent: lives at a station, goes out on missions, comes back."""
from dataclasses import dataclass
from typing import Optional

IDLE, TO_SCENE, ON_SCENE, RETURNING = "idle", "to_scene", "on_scene", "returning"


@dataclass
class Ambulance:
    id: int
    station: int
    designated_area: Optional[int] = None    # only used by the plan strategy
    state: str = IDLE
    busy_time: float = 0.0
    missions: int = 0
