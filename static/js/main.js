(() => {
  "use strict";

  const API = {
    data: "/api/data",
    solve: "/api/solve",
    health: "/api/health"
  };

  const state = {
    data: null,
    result: null,
    simulationTimer: null,
    simulationIndex: 0,
    simulationPaused: false
  };

  const $ = (selector, root = document) =>
    root.querySelector(selector);

  const $$ = (selector, root = document) =>
    Array.from(root.querySelectorAll(selector));

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    })[char]);
  }

  function formatNumber(value, digits = 2) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
      return "—";
    }

    return number.toLocaleString(undefined, {
      maximumFractionDigits: digits
    });
  }

  async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
      ...options,
      headers: {
        Accept: "application/json",
        ...(options.headers || {})
      }
    });

    let result = {};

    try {
      result = await response.json();
    } catch {
      result = {};
    }

    if (!response.ok) {
      throw new Error(
        result.error ||
        result.message ||
        `Request failed: ${response.status}`
      );
    }

    return result;
  }

  function showFeedback(message, type = "info") {
    const element = $("#input-feedback");

    if (element) {
      element.textContent = message;
      element.dataset.type = type;
    }
  }

  function setText(selector, value) {
    const element = $(selector);

    if (element) {
      element.textContent = value;
    }
  }

  function showToast(message) {
    let toast = $("#app-toast");

    if (!toast) {
      toast = document.createElement("div");
      toast.id = "app-toast";

      toast.style.cssText =
        "position:fixed;right:16px;bottom:16px;" +
        "padding:12px 16px;background:#172033;color:white;" +
        "border-radius:8px;z-index:9999;max-width:90%;";

      document.body.appendChild(toast);
    }

    toast.textContent = message;
    toast.hidden = false;

    clearTimeout(showToast.timer);

    showToast.timer = setTimeout(() => {
      toast.hidden = true;
    }, 4000);
  }

  function renderStats(data) {
    const totalAmbulances = (data.supply || [])
      .reduce((sum, value) => sum + Number(value || 0), 0);

    setText("#total-ambulances", totalAmbulances);
    setText("#total-areas", (data.areas || []).length);
    setText("#total-stations", (data.stations || []).length);

    const costs = (data.cost_matrix || []).flat().map(Number);

    if (costs.length) {
      const average =
        costs.reduce((sum, value) => sum + value, 0) /
        costs.length;

      setText("#average-response-time", formatNumber(average));
    }
  }

  function renderSupplyTable(data) {
    const table = $("#supply-table");

    if (!table) return;

    table.innerHTML = `
      <thead>
        <tr>
          ${data.stations.map(station =>
            `<th>${escapeHtml(station)}</th>`
          ).join("")}
        </tr>
      </thead>
      <tbody>
        <tr>
          ${data.stations.map((station, index) => `
            <td>
              <input
                type="number"
                min="0"
                step="1"
                required
                aria-label="Supply ${escapeHtml(station)}"
                value="${Number(data.supply[index])}"
              >
            </td>
          `).join("")}
        </tr>
      </tbody>
    `;
  }

  function renderDemandTable(data) {
    const table = $("#demand-table");

    if (!table) return;

    table.innerHTML = `
      <thead>
        <tr>
          ${data.areas.map(area =>
            `<th>${escapeHtml(area)}</th>`
          ).join("")}
        </tr>
      </thead>
      <tbody>
        <tr>
          ${data.areas.map((area, index) => `
            <td>
              <input
                type="number"
                min="0"
                step="1"
                required
                aria-label="Demand ${escapeHtml(area)}"
                value="${Number(data.demand[index])}"
              >
            </td>
          `).join("")}
        </tr>
      </tbody>
    `;
  }

  function renderCostMatrix(data) {
    const table = $("#cost-matrix-table");

    if (!table) return;

    const closedRoutes = new Set(
      (data.closed_routes || []).map(route =>
        `${route.from}|${route.to}`
      )
    );

    table.innerHTML = `
      <thead>
        <tr>
          <th>Station</th>
          ${data.areas.map(area =>
            `<th>${escapeHtml(area)}</th>`
          ).join("")}
        </tr>
      </thead>

      <tbody>
        ${data.stations.map((station, i) => `
          <tr>
            <th>${escapeHtml(station)}</th>

            ${data.areas.map((area, j) => {
              const isClosed = closedRoutes.has(
                `${station}|${area}`
              );

              if (isClosed) {
                return `<td title="Closed route">✕</td>`;
              }

              return `
                <td>
                  <input
                    class="cost-input"
                    type="number"
                    min="0"
                    step="any"
                    required
                    aria-label="Cost ${escapeHtml(station)} to ${escapeHtml(area)}"
                    value="${Number(data.cost_matrix[i][j])}"
                    data-station-index="${i}"
                    data-area-index="${j}"
                  >
                </td>
              `;
            }).join("")}
          </tr>
        `).join("")}
      </tbody>
    `;
  }

  function renderConstraints(data) {
    const element = $("#constraints-list");

    if (!element) return;

    const closedRoutes = data.closed_routes || [];
    const capacities = data.route_capacities || [];

    const items = [
      ...closedRoutes.map(route =>
        `<li>Closed route: ${escapeHtml(route.from)} → ${escapeHtml(route.to)}</li>`
      ),
      ...capacities.map(route =>
        `<li>Capacity: ${escapeHtml(route.from)} → ${escapeHtml(route.to)}, maximum ${Number(route.max)}</li>`
      )
    ];

    element.innerHTML = items.length
      ? items.join("")
      : "<li>No route restrictions.</li>";
  }

  function renderAllData(data) {
    state.data = data;

    renderStats(data);
    renderSupplyTable(data);
    renderDemandTable(data);
    renderCostMatrix(data);
    renderConstraints(data);
  }

  function renderAllocationTable(
    allocation,
    stations,
    areas
  ) {
    const table = $("#allocation-matrix-table");

    if (!table || !Array.isArray(allocation)) return;

    table.innerHTML = `
      <thead>
        <tr>
          <th>Station / Area</th>
          ${areas.map(area =>
            `<th>${escapeHtml(area)}</th>`
          ).join("")}
          <th>Total</th>
        </tr>
      </thead>

      <tbody>
        ${allocation.map((row, i) => {
          const total = row.reduce(
            (sum, value) => sum + Number(value || 0),
            0
          );

          return `
            <tr>
              <th>${escapeHtml(stations[i] || `S${i + 1}`)}</th>

              ${row.map(value => `
                <td class="${Number(value) > 0 ? "allocation-positive" : ""}">
                  ${formatNumber(value, 0)}
                </td>
              `).join("")}

              <td><strong>${formatNumber(total, 0)}</strong></td>
            </tr>
          `;
        }).join("")}
      </tbody>
    `;
  }

  function renderMap(allocation, stations, areas) {
    const element = $("#allocation-map");

    if (!element || !Array.isArray(allocation)) return;

    const routes = [];

    allocation.forEach((row, i) => {
      row.forEach((quantity, j) => {
        if (Number(quantity) > 0) {
          routes.push(`
            <div class="allocation-map-item">
              <span>${escapeHtml(stations[i])}</span>
              <span>→</span>
              <span>${escapeHtml(areas[j])}</span>
              <strong>${formatNumber(quantity, 0)}</strong>
            </div>
          `);
        }
      });
    });

    element.innerHTML = routes.length
      ? routes.join("")
      : "<p>No allocation data available.</p>";
  }

  function renderResult(result) {
    state.result = result;

    const stations =
      result.problem?.stations || state.data?.stations || [];

    const areas =
      result.problem?.areas || state.data?.areas || [];

    const initial = result.initial;
    const optimal = result.optimal;
    const comparison = result.comparison;

    setText(
      "#vam-cost",
      initial ? formatNumber(initial.cost, 0) : "Unavailable"
    );

    setText(
      "#modi-cost",
      optimal ? formatNumber(optimal.cost, 0) : "Unavailable"
    );

    const saving =
      comparison?.saving ??
      (initial && optimal
        ? initial.cost - optimal.cost
        : null);

    setText(
      "#savings-value",
      saving === null ? "—" : formatNumber(saving, 0)
    );

    setText(
      "#savings-percent",
      comparison?.saving_percent != null
        ? `${formatNumber(comparison.saving_percent)}%`
        : "—"
    );

    if (optimal?.allocation) {
      renderAllocationTable(
        optimal.allocation,
        stations,
        areas
      );

      renderMap(
        optimal.allocation,
        stations,
        areas
      );
    }

    const stepsElement = $("#vam-steps");

    if (stepsElement) {
      const steps = initial?.steps || [];

      stepsElement.innerHTML = steps.length
        ? `<ol>${steps.map(step => `
            <li>
              ${escapeHtml(step.station)} →
              ${escapeHtml(step.area)}:
              ${formatNumber(step.quantity, 0)} ambulance(s),
              unit cost ${formatNumber(step.unit_cost)}
            </li>
          `).join("")}</ol>`
        : "<p>No VAM steps returned.</p>";
    }

    const warningsElement = $("#solver-warnings");

    if (warningsElement) {
      const warnings = result.warnings || [];

      warningsElement.innerHTML = warnings.length
        ? `<ul>${warnings.map(warning =>
            `<li>${escapeHtml(warning)}</li>`
          ).join("")}</ul>`
        : "<p>No warnings.</p>";
    }

    const details = $("#solution-details");

    if (details) {
      details.innerHTML = `
        <p>
          <strong>Solver:</strong>
          ${escapeHtml(optimal?.solver || optimal?.method || "—")}
        </p>

        <p>
          <strong>Iterations:</strong>
          ${formatNumber(optimal?.iterations, 0)}
        </p>

        <p>
          <strong>Optimality confirmed:</strong>
          ${optimal?.is_optimal === true
            ? "Yes"
            : optimal?.is_optimal === false
              ? "No"
              : "Not reported"}
        </p>
      `;
    }

    if (result.meta?.elapsed_ms != null) {
      setText(
        "#solve-time",
        `${formatNumber(result.meta.elapsed_ms)} ms`
      );
    }
  }

  function readTableValues(selector, expectedCount, label) {
    const table = $(selector);

    const inputs = table
      ? $$('input[type="number"]', table)
      : [];

    if (inputs.length !== expectedCount) {
      throw new Error(
        `${label}: expected ${expectedCount} values, found ${inputs.length}.`
      );
    }

    return inputs.map((input, index) => {
      if (input.value.trim() === "") {
        throw new Error(`${label}: value ${index + 1} is empty.`);
      }

      const value = Number(input.value);

      if (!Number.isFinite(value) || value < 0) {
        throw new Error(
          `${label}: values must be non-negative numbers.`
        );
      }

      if (label !== "Cost matrix" && !Number.isInteger(value)) {
        throw new Error(
          `${label}: values must be whole numbers.`
        );
      }

      return value;
    });
  }

  function buildSolvePayload() {
    const data = state.data;

    if (!data) {
      throw new Error("Project data has not loaded.");
    }

    const supply = readTableValues(
      "#supply-table",
      data.stations.length,
      "Supply"
    );

    const demand = readTableValues(
      "#demand-table",
      data.areas.length,
      "Demand"
    );

    const closedRoutes = data.closed_routes || [];

    const expectedCosts =
      data.stations.length * data.areas.length -
      closedRoutes.length;

    const costs = readTableValues(
      "#cost-matrix-table",
      expectedCosts,
      "Cost matrix"
    );

    const costMatrix = [];
    let index = 0;

    for (let i = 0; i < data.stations.length; i++) {
      costMatrix[i] = [];

      for (let j = 0; j < data.areas.length; j++) {
        const closed = closedRoutes.some(route =>
          route.from === data.stations[i] &&
          route.to === data.areas[j]
        );

        costMatrix[i][j] = closed ? 0 : costs[index++];
      }
    }

    const totalSupply = supply.reduce(
      (sum, value) => sum + value,
      0
    );

    const totalDemand = demand.reduce(
      (sum, value) => sum + value,
      0
    );

    if (totalSupply !== totalDemand) {
      throw new Error(
        `Total supply (${totalSupply}) must equal total demand (${totalDemand}).`
      );
    }

    return {
      stations: data.stations,
      areas: data.areas,
      supply,
      demand,
      cost_matrix: costMatrix,
      current_distribution: data.current_distribution,
      closed_routes: closedRoutes,
      route_capacities: data.route_capacities || []
    };
  }

  async function runOptimization() {
    const button = $("#run-optimization-btn");

    if (button) {
      button.disabled = true;
    }

    showFeedback("Running optimization...", "info");

    try {
      const payload = buildSolvePayload();

      const result = await apiRequest(API.solve, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      renderResult(result);

      showFeedback(
        "Optimization completed successfully.",
        "success"
      );

      $("#results")?.scrollIntoView({
        behavior: "smooth",
        block: "start"
      });
    } catch (error) {
      showFeedback(error.message, "error");
      showToast(error.message);
    } finally {
      if (button) {
        button.disabled = false;
      }
    }
  }

  function loadSampleData() {
    if (!state.data) return;

    renderAllData(state.data);

    showFeedback(
      "Sample data loaded successfully.",
      "success"
    );
  }

  function toggleManualInput() {
    const panel =
      $("#manual-input-panel") ||
      $("#manual-input-form");

    if (!panel) {
      showToast("Manual input panel was not found in the HTML.");
      return;
    }

    panel.hidden = !panel.hidden;
  }

  function filterTables(query) {
    const search = query.trim().toLowerCase();

    $$("table tbody tr").forEach(row => {
      row.hidden =
        Boolean(search) &&
        !row.textContent.toLowerCase().includes(search);
    });
  }

  function stopSimulation() {
    if (state.simulationTimer) {
      clearInterval(state.simulationTimer);
      state.simulationTimer = null;
    }
  }

  function simulationTick() {
    if (state.simulationPaused) return;

    const allocation = state.result?.optimal?.allocation;

    if (!allocation) {
      stopSimulation();
      addSimulationEvent(
        "Run optimization before starting the simulation."
      );
      return;
    }

    const stations =
      state.result.problem?.stations || state.data.stations;

    const areas =
      state.result.problem?.areas || state.data.areas;

    const trips = [];

    allocation.forEach((row, i) => {
      row.forEach((quantity, j) => {
        for (let k = 0; k < Number(quantity); k++) {
          trips.push({
            station: stations[i],
            area: areas[j]
          });
        }
      });
    });

    if (state.simulationIndex >= trips.length) {
      stopSimulation();
      addSimulationEvent("Simulation completed.");
      return;
    }

    const trip = trips[state.simulationIndex++];

    addSimulationEvent(
      `Trip ${state.simulationIndex}: ${trip.station} → ${trip.area}`
    );
  }

  function addSimulationEvent(message) {
    const element = $("#simulation-events");

    if (!element) return;

    const item = document.createElement("li");
    item.textContent = message;

    element.prepend(item);
  }

  function startSimulation() {
    stopSimulation();

    state.simulationIndex = 0;
    state.simulationPaused = false;

    const events = $("#simulation-events");

    if (events) {
      events.innerHTML = "";
    }

    const speed = Math.max(
      1,
      Number($("#simulation-speed")?.value || 1)
    );

    setText("#simulation-speed-value", `${speed}x`);

    addSimulationEvent("Simulation started.");

    simulationTick();

    state.simulationTimer = setInterval(
      simulationTick,
      Math.max(150, 1200 / speed)
    );
  }

  function pauseSimulation() {
    state.simulationPaused = !state.simulationPaused;

    const button = $("#simulation-pause");

    if (button) {
      button.textContent = state.simulationPaused
        ? "Resume"
        : "Pause";
    }

    addSimulationEvent(
      state.simulationPaused
        ? "Simulation paused."
        : "Simulation resumed."
    );
  }

  function resetSimulation() {
    stopSimulation();

    state.simulationIndex = 0;
    state.simulationPaused = false;

    const events = $("#simulation-events");

    if (events) {
      events.innerHTML = "";
    }

    const button = $("#simulation-pause");

    if (button) {
      button.textContent = "Pause";
    }

    addSimulationEvent("Simulation reset.");
  }

  function bindEvents() {
    $("#run-optimization-btn")
      ?.addEventListener("click", runOptimization);

    $("#load-sample-btn")
      ?.addEventListener("click", loadSampleData);

    $("#manual-input-btn")
      ?.addEventListener("click", toggleManualInput);

    $("#global-search")
      ?.addEventListener("input", event => {
        filterTables(event.target.value);
      });

    $("#simulation-start")
      ?.addEventListener("click", startSimulation);

    $("#simulation-pause")
      ?.addEventListener("click", pauseSimulation);

    $("#simulation-reset")
      ?.addEventListener("click", resetSimulation);

    $("#simulation-speed")
      ?.addEventListener("change", () => {
        const speed = $("#simulation-speed");

        setText(
          "#simulation-speed-value",
          `${speed.value}x`
        );

        if (state.simulationTimer) {
          startSimulation();
        }
      });

    $("#settings-reset-btn")
      ?.addEventListener("click", async () => {
        try {
          const data = await apiRequest(API.data);

          renderAllData(data);

          showFeedback(
            "Project data reloaded.",
            "success"
          );
        } catch (error) {
          showToast(error.message);
        }
      });
  }

  async function init() {
    bindEvents();

    try {
      const data = await apiRequest(API.data);

      renderAllData(data);

      showFeedback(
        "Project data loaded. You can run optimization.",
        "success"
      );
    } catch (error) {
      showFeedback(
        `Could not load project data: ${error.message}`,
        "error"
      );

      showToast(error.message);
    }

    try {
      await apiRequest(API.health);
    } catch {
      // The health check is optional.
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();


