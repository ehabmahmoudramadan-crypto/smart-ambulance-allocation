"""Dispatch strategies for the simulation (task 14: Dispatcher Agent).

The engine calls a dispatcher through this small interface:

    select(incident, ambulances) -> (ambulance, fallback) | None
    reserve(ambulance, area)     # called right after select, when the ambulance leaves
    release(ambulance, area)     # called when the ambulance is back at its station
    travel(ambulance, area)      # driving minutes (from the cost matrix)
    closed_uses, max_load        # counters used by the constraint audit

Two strategies, both obey the same two constraints:

  * GreedyDispatcher  ("nearest idle"): dynamic rule - send the closest free ambulance.
  * PlanDispatcher    ("plan / MODI"):  static rule - send a free ambulance that the optimal
                                        plan designated to this area; if none is free,
                                        fall back to the nearest free one.

Constraints (defined once in data/data.json and passed in by the engine):
  * closed road (station -> area): never used.
  * route capacity (station -> area, k): at most k ambulances of that station may be on a
    mission to that area at the same time (from dispatch until they are back home).

Rules that make every decision explicit and repeatable:
  * only IDLE ambulances can be chosen, so a busy ambulance is never given a second call;
  * ties on distance are broken by ambulance id, so the same seed gives the same result;
  * if no ambulance is allowed, select() returns None and the call keeps waiting.
"""
from simulation.ambulance_agent import IDLE


class BaseDispatcher:
    def __init__(self, cost_matrix, closed=(), caps=()):
        self.cost = cost_matrix
        self.closed = {(i, j) for i, j in closed}
        self.caps = {(i, j): k for i, j, k in caps}
        self.load = {}            # (station, area) -> ambulances on a mission right now
        self.max_load = {}        # (station, area) -> peak of `load` (for the audit)
        self.closed_uses = 0      # times a closed road was used: must stay 0
        self.active = set()       # ids of ambulances currently on a mission

    # ----------------------------------------------------------- queries
    def travel(self, amb, area):
        return self.cost[amb.station][area]

    def _usable(self, amb, area):
        """Idle, road open, and the route is not at its capacity."""
        if amb.state != IDLE or amb.id in self.active:
            return False
        route = (amb.station, area)
        if route in self.closed:
            return False
        cap = self.caps.get(route)
        return cap is None or self.load.get(route, 0) < cap

    def _nearest(self, ambulances, area):
        """Closest ambulance by driving time; ties go to the lowest id."""
        return min(ambulances, key=lambda a: (self.cost[a.station][area], a.id), default=None)

    # ----------------------------------------------------------- updates
    def reserve(self, amb, area):
        if amb.id in self.active:
            raise RuntimeError(f"ambulance {amb.id} is already on a mission")
        route = (amb.station, area)
        if route in self.closed:
            self.closed_uses += 1
        self.active.add(amb.id)
        self.load[route] = self.load.get(route, 0) + 1
        self.max_load[route] = max(self.max_load.get(route, 0), self.load[route])

    def release(self, amb, area):
        self.active.discard(amb.id)
        route = (amb.station, area)
        self.load[route] = self.load.get(route, 0) - 1

    def select(self, incident, ambulances):
        raise NotImplementedError


class GreedyDispatcher(BaseDispatcher):
    """Dynamic policy: the closest allowed idle ambulance, from any station."""

    def select(self, incident, ambulances):
        usable = [a for a in ambulances if self._usable(a, incident.area)]
        pick = self._nearest(usable, incident.area)
        return None if pick is None else (pick, False)


class PlanDispatcher(BaseDispatcher):
    """Static policy: ambulances designated to the area first, else the nearest idle one.

    `fallback` is True when the chosen ambulance was not designated to the call's area.
    """

    def select(self, incident, ambulances):
        usable = [a for a in ambulances if self._usable(a, incident.area)]
        own = [a for a in usable if a.designated_area == incident.area]
        pick = self._nearest(own, incident.area)
        if pick is not None:
            return pick, False
        pick = self._nearest(usable, incident.area)
        return None if pick is None else (pick, True)
