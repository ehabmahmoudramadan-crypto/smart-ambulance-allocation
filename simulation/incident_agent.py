"""An emergency call."""
from dataclasses import dataclass
from typing import Optional

CRITICAL, URGENT, NORMAL = 1, 2, 3          # smaller number = served first


@dataclass
class Incident:
    id: int
    area: int                 # index of the area where it happens
    time: float               # minute at which the call arrives
    priority: int             # 1 critical, 2 urgent, 3 normal
    service: float            # minutes spent on scene (pre-drawn so runs are comparable)
    dispatched_at: Optional[float] = None
    arrived_at: Optional[float] = None
    ambulance_id: Optional[int] = None
    fallback: bool = False    # served by an ambulance not designated to this area

    @property
    def wait(self):           # minutes waiting for a free ambulance
        return None if self.dispatched_at is None else self.dispatched_at - self.time

    @property
    def response(self):       # call -> ambulance on scene
        return None if self.arrived_at is None else self.arrived_at - self.time
