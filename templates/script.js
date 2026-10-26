(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const API = location.port === "5000" ? "" : "http://127.0.0.1:5000";
  const E = (t, x, c) => { const n = document.createElement(t); if (x !== undefined) n.textContent = x; if (c) n.className = c; return n; };
  const SV = (t, a) => { const n = document.createElementNS("http://www.w3.org/2000/svg", t); for (const k in a) n.setAttribute(k, a[k]); return n; };
  const post = async (u, b) => { const r = await fetch(API + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) }); const j = await r.json(); if (!r.ok) throw new Error(j.error || r.status); return j; };
  const err = (m) => { $("error").textContent = m || ""; $("error").hidden = !m; };
  const fail = (e) => err(e instanceof TypeError ? "Cannot reach the server. Start it from the project folder with: python run.py" : e.message);
  let S = null, view = "optimal";

  const closedAt = (i, j) => S.closed.some(([a, b]) => a === i && b === j);
  const capAt = (i, j) => (S.caps.find(([a, b]) => a === i && b === j) || [])[2];

  function chips(id, labels, vals) {
    const box = $(id); box.replaceChildren();
    labels.forEach((l, k) => { const s = E("span"); s.append(E("small", l), E("b", String(vals[k]))); box.append(s); });
  }
  function head(t, first, cols, last) {
    const tr = E("tr"); tr.append(E("th", first)); cols.forEach((c) => tr.append(E("th", c))); if (last) tr.append(E("th", last)); t.append(tr);
  }

  function renderData() {
    chips("t-supply", S.stations, S.supply); chips("t-demand", S.areas, S.demand);
    const t = $("t-cost"); t.replaceChildren(); head(t, "", S.areas);
    S.cost_matrix.forEach((row, i) => { const tr = E("tr"); tr.append(E("th", S.stations[i]));
      row.forEach((c, j) => { const td = E("td", String(c)); if (closedAt(i, j)) td.className = "x"; else if (capAt(i, j) !== undefined) td.className = "c"; tr.append(td); }); t.append(tr); });
    $("k-amb").textContent = S.supply.reduce((a, b) => a + b, 0);
    $("k-areas").textContent = S.areas.length; $("k-st").textContent = S.stations.length;
  }

  function renderPlan() {
    const plan = S[view], x = plan.allocation, t = $("t-plan"); t.replaceChildren(); head(t, "Station \\ Area", S.areas, "Supply");
    S.stations.forEach((s, i) => { const tr = E("tr"); tr.append(E("th", s));
      x[i].forEach((q, j) => { const cap = capAt(i, j), cl = closedAt(i, j);
        const td = E("td", cl && !q ? "\u2715" : cap !== undefined ? `${q}/${cap}` : q ? String(q) : "-");
        td.className = cl ? "x" : cap !== undefined ? "c" : q ? "u" : "z"; tr.append(td); });
      tr.append(E("td", `${x[i].reduce((a, b) => a + b, 0)}/${S.supply[i]}`, "t")); t.append(tr); });
    const f = E("tr", undefined, "tot"); f.append(E("th", "Demand"));
    S.areas.forEach((_, j) => f.append(E("td", `${x.reduce((a, r) => a + r[j], 0)}/${S.demand[j]}`))); f.append(E("td", `${plan.cost}`)); t.append(f);
  }

  function renderResults() {
    $("c-vam").textContent = S.initial.cost; $("c-modi").textContent = S.optimal.cost;
    const gain = (100 * (S.initial.cost - S.optimal.cost) / S.initial.cost).toFixed(1);
    $("c-note").textContent = `\u2713 ${gain}% better than VAM` + (S.current ? ` \u00b7 ${S.saving_percent}% below current plan (${S.current.cost})` : "");
    $("a-vam").textContent = `Initial solution with cost ${S.initial.cost}`;
    $("a-modi").textContent = `Optimal solution with cost ${S.optimal.cost} (${S.optimal.iterations} iterations)`;
    const x = S.optimal.allocation, sum = (a) => a.reduce((p, q) => p + q, 0);
    const rowsOk = x.every((r, i) => sum(r) === S.supply[i]), colsOk = S.areas.every((_, j) => x.reduce((a, r) => a + r[j], 0) === S.demand[j]);
    const closedUse = S.closed.reduce((a, [i, j]) => a + x[i][j], 0), capOk = S.caps.every(([i, j, k]) => x[i][j] <= k);
    const items = [[sum(S.supply) === sum(S.demand), `Total supply equals total demand (${sum(S.supply)} = ${sum(S.demand)})`],
      [rowsOk && colsOk, "All row and column sums are satisfied"], [x.flat().every((v) => Number.isInteger(v) && v >= 0), "All allocations are non-negative integers"],
      [closedUse === 0, `Closed roads carry ${closedUse} ambulances`], [capOk, "All route capacities are respected"]];
    const ul = $("insights"); ul.replaceChildren(); items.forEach(([ok, t]) => ul.append(E("li", t, ok ? "" : "bad")));
    renderPlan();
  }

  // ---- map ------------------------------------------------------------
  let dots = null;
  function drawMap(m, withDots) {
    m.replaceChildren();
    const P = (c) => ({ x: c[0], y: c[1] }), st = S.station_coords.map(P), ar = S.area_coords.map(P), x = S.optimal.allocation;
    x.forEach((row, i) => row.forEach((q, j) => { if (q > 0) m.append(SV("line", { x1: st[i].x, y1: st[i].y, x2: ar[j].x, y2: ar[j].y, stroke: capAt(i, j) !== undefined ? "#d97706" : "#16a34a", "stroke-width": 0.12 + 0.07 * q, "stroke-dasharray": "0.6 0.5", opacity: 0.75 })); }));
    S.closed.forEach(([i, j]) => { const a = st[i], b = ar[j], mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
      m.append(SV("line", { x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke: "#e11d48", "stroke-width": 0.14, "stroke-dasharray": "0.3 0.4" }));
      const t = SV("text", { x: mx, y: my + 0.7, "text-anchor": "middle", "font-size": 2, fill: "#e11d48", "font-weight": 700 }); t.textContent = "\u2715"; m.append(t); });
    ar.forEach((p, j) => { m.append(SV("circle", { cx: p.x, cy: p.y, r: 0.9, fill: "#e11d48" })); const t = SV("text", { x: p.x, y: p.y - 1.3, "text-anchor": "middle", "font-size": 1.3, fill: "#8a1230", "font-weight": 700 }); t.textContent = S.areas[j]; m.append(t); });
    st.forEach((p, i) => { m.append(SV("rect", { x: p.x - 1, y: p.y - 1, width: 2, height: 2, rx: 0.5, fill: "#2563eb" })); const t = SV("text", { x: p.x, y: p.y + 0.45, "text-anchor": "middle", "font-size": 1.15, fill: "#fff", "font-weight": 700 }); t.textContent = S.stations[i].slice(1); m.append(t); });
    if (withDots) { dots = SV("g", {}); m.append(dots); }
  }
  const renderMap = () => { drawMap($("map"), false); drawMap($("map-sim"), true); };

  // ---- performance ----------------------------------------------------
  function renderPerf(r) {
    const g = r.summary.greedy, p = r.summary.plan, f = (o, d = 1) => o.mean.toFixed(d);
    const t = $("t-perf"); t.replaceChildren();
    const h = E("tr"); ["", "Nearest idle", "Plan (MODI)"].forEach((x) => h.append(E("th", x))); t.append(h);
    [["Mean response (min)", "mean_response"], ["90th percentile (min)", "p90_response"], ["Within 20 min (%)", "within_target_pct"], ["Fleet utilization (%)", "utilization_pct"]]
      .forEach(([l, k]) => { const tr = E("tr"); tr.append(E("td", l), E("td", f(g[k])), E("td", f(p[k]))); t.append(tr); });
    $("k-resp").textContent = `${f(p.mean_response)} min`; $("k-resp-n").textContent = `plan \u00b7 nearest idle ${f(g.mean_response)} min`;
    const d = r.difference_greedy_minus_plan.mean_response;
    $("verdict").textContent = Math.abs(d.mean) <= d.ci ? "No significant difference between the strategies." :
      `${d.mean < 0 ? "Nearest idle" : "Plan"} is faster by ${Math.abs(d.mean).toFixed(2)} \u00b1 ${d.ci.toFixed(2)} min. Closed-road uses: ${r.audit.plan.closed_uses}; ${r.audit.plan.capped_routes.map((c) => `${c.route} peak ${c.max_load}/${c.cap}`).join(", ")}.`;
  }

  // ---- live replay ----------------------------------------------------
  let missions = [], evs = [], pos = 0, clock = 0, running = false, last = 0;
  const hhmm = (m) => { m = Math.floor(m) % 1440; return `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`; };
  const PRI = { 1: "Critical", 2: "High", 3: "Normal" };
  function prepare(data) {
    missions = data.missions; evs = [];
    missions.forEach((m) => { evs.push([m.call, `Incident reported at ${S.areas[m.area]} (${PRI[m.priority]} priority)`, "call"], [m.dispatch, `Ambulance ${S.stations[m.station]} assigned to ${S.areas[m.area]}`], [m.home, `Ambulance ${S.stations[m.station]} returned to station`]); });
    evs.sort((a, b) => a[0] - b[0]); reset();
  }
  function reset() { running = false; clock = 0; pos = 0; $("events").replaceChildren(); $("clock").textContent = "00:00"; dots && dots.replaceChildren(); $("sim-state").textContent = missions.length ? "Ready" : "Loading\u2026"; }
  function frame(ts) {
    if (!running) return;
    const dt = (ts - last) / 1000; last = ts; clock += dt * 6 * +$("sim-speed").value;
    while (pos < evs.length && evs[pos][0] <= clock) { const li = E("li", undefined, evs[pos][2]); li.append(E("b", hhmm(evs[pos][0])), document.createTextNode(evs[pos][1])); $("events").prepend(li); if ($("events").children.length > 7) $("events").lastChild.remove(); pos++; }
    $("clock").textContent = hhmm(clock); dots.replaceChildren();
    missions.forEach((m) => { if (clock < m.dispatch || clock >= m.home) return;
      const a = S.station_coords[m.station], b = S.area_coords[m.area]; let f = 1;
      if (clock < m.arrive) f = (clock - m.dispatch) / (m.arrive - m.dispatch); else if (clock >= m.clear) f = 1 - (clock - m.clear) / (m.home - m.clear);
      dots.append(SV("circle", { cx: a[0] + (b[0] - a[0]) * f, cy: a[1] + (b[1] - a[1]) * f, r: 0.55, fill: "#16a34a", stroke: "#fff", "stroke-width": 0.15 })); });
    if (clock > missions[missions.length - 1].home) { running = false; $("sim-state").textContent = "Finished"; return; }
    requestAnimationFrame(frame);
  }
  async function loadReplay() { try { prepare(await post("/api/simulate/run", { strategy: $("sim-strat").value, hours: 6 })); } catch (e) { fail(e); } }
  $("b-start").onclick = () => { if (!missions.length || running) return; if (clock > missions[missions.length - 1].home) reset(); running = true; last = performance.now(); $("sim-state").textContent = "Running"; requestAnimationFrame(frame); };
  $("b-pause").onclick = () => { running = false; $("sim-state").textContent = "Paused"; };
  $("b-reset").onclick = reset;
  $("sim-strat").onchange = loadReplay;
  $("sim-speed").oninput = () => { $("sim-x").textContent = `${$("sim-speed").value}x`; };

  // ---- boot -----------------------------------------------------------
  document.querySelectorAll("#tabs button").forEach((b) => b.onclick = () => { document.querySelectorAll("#tabs button").forEach((x) => x.classList.toggle("on", x === b)); view = b.dataset.v; if (S) renderPlan(); });
  const links = [...document.querySelectorAll("nav a")];
  const PAGES = ["home", "data", "results", "sim", "reports"];
  function route() {
    const h = location.hash.slice(1), id = PAGES.includes(h) ? h : "home";
    document.querySelectorAll(".page").forEach((p) => p.classList.toggle("on", p.id === `p-${id}`));
    links.forEach((a) => a.classList.toggle("on", a.getAttribute("href") === `#${id}`));
    window.scrollTo(0, 0);
  }
  addEventListener("hashchange", route); route();

  async function sysStatus(ok, perfOk) {
    const ul = $("sys"); ul.replaceChildren();
    [["Backend API", ok], ["Optimization Engine", !!S], ["Simulation Engine", perfOk], ["Frontend Interface", true]].forEach(([n, g]) => ul.append(E("li", `${n} \u2013 ${g ? "Operational" : "Unavailable"}`, g ? "" : "bad")));
    $("status").textContent = ok ? "All systems operational" : "Server unreachable"; $("status").parentElement.className = `pill ${ok ? "ok" : "bad"}`;
  }

  async function run() {
    const btn = $("run"); btn.disabled = true; btn.textContent = "Solving\u2026"; err("");
    let ok = false, perfOk = false;
    try {
      S = await post("/api/solve"); ok = true;
      renderData(); renderResults(); renderMap();
      const r = await post("/api/simulate", { reps: 10 }); renderPerf(r); perfOk = true;
      await loadReplay();
    } catch (e) { fail(e); }
    finally { btn.disabled = false; btn.textContent = "Run Optimization"; sysStatus(ok, perfOk); }
  }
  $("run").onclick = run; run();
})();
