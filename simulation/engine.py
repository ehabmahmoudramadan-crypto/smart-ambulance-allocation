"""Discrete-event simulation of a day of emergency calls.

Both strategies see exactly the same calls (same arrival times, areas,
priorities and on-scene durations), so the comparison is paired and fair.
"""
import heapq
import itertools
import math
import random
import statistics
from dataclasses import replace

from simulation.ambulance import Ambulance, IDLE, ON_SCENE, RETURNING, TO_SCENE
from simulation.dispatcher import GreedyDispatcher, PlanDispatcher
from simulation.incident import Incident

ARRIVAL, ARRIVE_SCENE, CLEARED, HOME = range(4)
PRIORITY_MIX = ([1, 2, 3], [0.2, 0.3, 0.5])
SERVICE_RANGE = (20.0, 40.0)                 # minutes on scene
TARGET_MINUTES = 20.0                        # "fast enough" response threshold


# ---------------------------------------------------------------- set-up
def generate_incidents(demand, incidents_per_hour, hours, seed):
    """Poisson arrivals; the area is drawn in proportion to the area's demand."""
    rng = random.Random(seed)
    rate = incidents_per_hour / 60.0
    out, t = [], 0.0
    while True:
        t += rng.expovariate(rate)
        if t > hours * 60:
            return out
        out.append(Incident(
            id=len(out),
            area=rng.choices(range(len(demand)), weights=demand)[0],
            time=t,
            priority=rng.choices(*PRIORITY_MIX)[0],
            service=rng.uniform(*SERVICE_RANGE)))


def fleet_greedy(supply):
    amb = []
    for i, s in enumerate(supply):
        amb += [Ambulance(id=len(amb) + k, station=i) for k in range(s)]
    return amb


def fleet_from_plan(plan):
    amb = []
    for i, row in enumerate(plan):
        for j, q in enumerate(row):
            amb += [Ambulance(id=len(amb) + k, station=i, designated_area=j) for k in range(q)]
    return amb


# ------------------------------------------------------------ simulation
class Simulation:
    def __init__(self, ambulances, dispatcher, incidents):
        self.ambulances = ambulances
        self.dispatcher = dispatcher
        self.incidents = incidents
        self.queue = []
        self.max_queue = 0
        self.end_time = 0.0

    def run(self):
        seq = itertools.count()
        events = [(i.time, next(seq), ARRIVAL, None, i) for i in self.incidents]
        heapq.heapify(events)
        push = lambda t, kind, a, inc: heapq.heappush(events, (t, next(seq), kind, a, inc))
        d = self.dispatcher

        while events:
            now, _, kind, amb, inc = heapq.heappop(events)
            self.end_time = now
            if kind == ARRIVAL:
                self.queue.append(inc)
                self.max_queue = max(self.max_queue, len(self.queue))
            elif kind == ARRIVE_SCENE:
                inc.arrived_at = now
                amb.state = ON_SCENE
                push(now + inc.service, CLEARED, amb, inc)
            elif kind == CLEARED:
                amb.state = RETURNING
                push(now + d.travel(amb, inc.area), HOME, amb, inc)
            else:                                           # HOME
                amb.state = IDLE
                amb.busy_time += now - inc.dispatched_at
                amb.missions += 1
                d.release(amb, inc.area)
            self._dispatch(now, push)
        return self

    def _dispatch(self, now, push):
        if not self.queue:
            return
        idle = sum(a.state == IDLE for a in self.ambulances)
        if not idle:                                   # everybody busy: nothing to decide
            return
        self.queue.sort(key=lambda i: (i.priority, i.time, i.id))
        waiting = []
        for inc in self.queue:
            pick = self.dispatcher.select(inc, self.ambulances) if idle else None
            if pick is None:
                waiting.append(inc)
                continue
            idle -= 1
            amb, fallback = pick
            amb.state = TO_SCENE
            self.dispatcher.reserve(amb, inc.area)
            inc.dispatched_at, inc.ambulance_id, inc.fallback = now, amb.id, fallback
            push(now + self.dispatcher.travel(amb, inc.area), ARRIVE_SCENE, amb, inc)
        self.queue = waiting


# --------------------------------------------------------------- metrics
def _percentile(sorted_vals, p):
    return sorted_vals[max(0, math.ceil(p * len(sorted_vals)) - 1)]


def summarize(sim, horizon_minutes, n_areas):
    done = [i for i in sim.incidents if i.response is not None]
    resp = sorted(i.response for i in done)
    crit = [i.response for i in done if i.priority == 1]
    by_area = {}
    for j in range(n_areas):
        r = [i.response for i in done if i.area == j]
        by_area[j] = statistics.fmean(r) if r else None
    span = max(sim.end_time, horizon_minutes)
    return {
        "incidents": len(sim.incidents),
        "unserved": len(sim.incidents) - len(done),
        "mean_response": statistics.fmean(resp),
        "median_response": statistics.median(resp),
        "p90_response": _percentile(resp, 0.90),
        "max_response": resp[-1],
        "within_target_pct": 100 * sum(r <= TARGET_MINUTES for r in resp) / len(resp),
        "critical_mean_response": statistics.fmean(crit) if crit else None,
        "mean_wait": statistics.fmean(i.wait for i in done),
        "max_queue": sim.max_queue,
        "fallback_pct": 100 * sum(i.fallback for i in done) / len(done),
        "utilization_pct": 100 * sum(a.busy_time for a in sim.ambulances)
                           / (len(sim.ambulances) * span),
        "by_area": by_area,
    }


def simulate_once(strategy, ds, closed, caps, plan, incidents, hours):
    """Run one strategy on (a private copy of) the given incidents."""
    inc = [replace(i) for i in incidents]
    if strategy == "greedy":
        sim = Simulation(fleet_greedy(ds["supply"]),
                         GreedyDispatcher(ds["cost_matrix"], closed, caps), inc)
    elif strategy == "plan":
        sim = Simulation(fleet_from_plan(plan),
                         PlanDispatcher(ds["cost_matrix"], closed, caps), inc)
    else:
        raise ValueError(f"unknown strategy {strategy!r}")
    sim.run()
    out = summarize(sim, hours * 60, len(ds["demand"]))
    out["audit"] = {"closed_uses": sim.dispatcher.closed_uses,
                    "max_load": {k: v for k, v in sim.dispatcher.max_load.items()}}
    return out


# ------------------------------------------------------------ comparison
def _mean_ci(values):
    values = [v for v in values if v is not None]
    if not values:
        return {"mean": None, "ci": None}
    m = statistics.fmean(values)
    ci = 1.96 * statistics.stdev(values) / math.sqrt(len(values)) if len(values) > 1 else 0.0
    return {"mean": m, "ci": ci}


METRICS = ["mean_response", "median_response", "p90_response", "max_response",
           "within_target_pct", "critical_mean_response", "mean_wait",
           "max_queue", "fallback_pct", "utilization_pct", "unserved"]


def run_comparison(ds, closed, caps, plan, incidents_per_hour=48, hours=24,
                   reps=10, seed=2026):
    runs = {"greedy": [], "plan": []}
    for r in range(reps):
        incidents = generate_incidents(ds["demand"], incidents_per_hour, hours, seed + r)
        for s in runs:
            runs[s].append(simulate_once(s, ds, closed, caps, plan, incidents, hours))

    summary = {s: {m: _mean_ci([r[m] for r in rs]) for m in METRICS} for s, rs in runs.items()}
    n_areas = len(ds["demand"])
    per_area = {s: [statistics.fmean([v for v in (r["by_area"][j] for r in rs) if v is not None] or [0])
                    for j in range(n_areas)] for s, rs in runs.items()}

    def paired(metric):             # greedy minus plan, same incident streams
        return _mean_ci([g[metric] - p[metric] for g, p in zip(runs["greedy"], runs["plan"])])

    audit = {}
    for s, rs in runs.items():
        peak = {}
        for r in rs:
            for k, v in r["audit"]["max_load"].items():
                peak[k] = max(peak.get(k, 0), v)
        audit[s] = {
            "closed_uses": sum(r["audit"]["closed_uses"] for r in rs),
            "capped_routes": [{"route": f'{ds["stations"][i]} \u2192 {ds["areas"][j]}',
                               "max_load": peak.get((i, j), 0), "cap": k}
                              for i, j, k in caps]}

    return {
        "params": {"incidents_per_hour": incidents_per_hour, "hours": hours, "reps": reps,
                   "seed": seed, "target_minutes": TARGET_MINUTES,
                   "incidents_per_run": round(statistics.fmean(r["incidents"] for r in runs["greedy"]))},
        "summary": summary,
        "per_area": per_area,
        "difference_greedy_minus_plan": {m: paired(m) for m in
                                         ("mean_response", "p90_response", "within_target_pct")},
        "audit": audit,
    }


def replay(strategy, ds, closed, caps, plan, incidents_per_hour, hours, seed):
    """One run as a list of missions (for the live replay in the UI)."""
    inc = generate_incidents(ds["demand"], incidents_per_hour, hours, seed)
    fleet = fleet_greedy(ds["supply"]) if strategy == "greedy" else fleet_from_plan(plan)
    disp = (GreedyDispatcher if strategy == "greedy" else PlanDispatcher)(ds["cost_matrix"], closed, caps)
    sim = Simulation(fleet, disp, inc).run()
    st = {a.id: a.station for a in fleet}
    out = []
    for i in sim.incidents:
        s = st[i.ambulance_id]
        back = i.arrived_at + i.service + ds["cost_matrix"][s][i.area]
        out.append({"id": i.id, "area": i.area, "station": s, "priority": i.priority,
                    "call": round(i.time, 1), "dispatch": round(i.dispatched_at, 1),
                    "arrive": round(i.arrived_at, 1), "clear": round(i.arrived_at + i.service, 1),
                    "home": round(back, 1)})
    return out
