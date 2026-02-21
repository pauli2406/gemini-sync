(function () {
  const root = document.getElementById("ops-root");
  if (!root) {
    return;
  }

  const endpoint = root.getAttribute("data-endpoint");
  const refreshMs = Number(root.getAttribute("data-refresh-ms") || "15000");
  const view = root.getAttribute("data-ops-view");
  const defaultLimitRuns = Number(root.getAttribute("data-default-limit-runs") || "25");

  const errorBanner = document.getElementById("ops-error");

  const state = {
    limitRuns: defaultLimitRuns,
    offsetRuns: 0,
    windowHours: 168,
    status: "",
    connectorId: "",
  };

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) {
      el.textContent = value;
    }
  }

  function setLink(id, href) {
    const el = document.getElementById(id);
    if (!el) {
      return;
    }

    if (!href) {
      el.setAttribute("href", "#");
      el.style.display = "none";
      return;
    }

    el.setAttribute("href", href);
    el.style.display = "inline-flex";
  }

  function formatDate(value) {
    if (!value) {
      return "n/a";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return String(value);
    }
    return date.toISOString().replace("T", " ").replace(".000Z", "Z");
  }

  function formatSeconds(value) {
    if (value === null || value === undefined) {
      return "n/a";
    }
    const total = Number(value);
    if (!Number.isFinite(total)) {
      return "n/a";
    }
    if (total < 60) {
      return `${total}s`;
    }
    const mins = Math.floor(total / 60);
    const secs = total % 60;
    return `${mins}m ${secs}s`;
  }

  function statusBadge(status) {
    const label = status || "UNKNOWN";
    const slug = label.toLowerCase();
    if (slug === "success") {
      return [label, "status-pill status-success"];
    }
    if (slug === "failed") {
      return [label, "status-pill status-failed"];
    }
    if (slug === "running") {
      return [label, "status-pill status-running"];
    }
    return [label, "status-pill status-unknown"];
  }

  function appendStatusCell(row, status) {
    const td = document.createElement("td");
    const span = document.createElement("span");
    const [label, cls] = statusBadge(status);
    span.className = cls;
    span.textContent = label;
    td.appendChild(span);
    row.appendChild(td);
  }

  function appendTextCell(row, value) {
    const td = document.createElement("td");
    td.textContent = value;
    row.appendChild(td);
  }

  function appendLinkCell(row, href, text) {
    const td = document.createElement("td");
    const link = document.createElement("a");
    link.href = href;
    link.textContent = text;
    td.appendChild(link);
    row.appendChild(td);
  }

  function appendLogLinksCell(row, links) {
    const td = document.createElement("td");
    const parts = [];

    if (links && links.splunk_url) {
      const splunk = document.createElement("a");
      splunk.href = links.splunk_url;
      splunk.textContent = "Splunk";
      splunk.target = "_blank";
      splunk.rel = "noopener noreferrer";
      parts.push(splunk);
    }

    if (links && links.kestra_url) {
      const kestra = document.createElement("a");
      kestra.href = links.kestra_url;
      kestra.textContent = "Kestra";
      kestra.target = "_blank";
      kestra.rel = "noopener noreferrer";
      parts.push(kestra);
    }

    if (parts.length === 0) {
      td.textContent = "-";
    } else {
      parts.forEach((node, index) => {
        if (index > 0) {
          const sep = document.createTextNode(" | ");
          td.appendChild(sep);
        }
        td.appendChild(node);
      });
    }

    row.appendChild(td);
  }

  function pageSummary(page) {
    if (!page || page.total_runs === 0) {
      return "No runs";
    }

    const start = page.offset_runs + 1;
    const end = page.offset_runs + page.limit_runs > page.total_runs
      ? page.total_runs
      : page.offset_runs + page.limit_runs;
    return `${start}-${end} of ${page.total_runs}`;
  }

  function updatePager(page, prevId, nextId, pageId) {
    const prev = document.getElementById(prevId);
    const next = document.getElementById(nextId);

    if (prev) {
      prev.disabled = !page || page.offset_runs <= 0;
    }
    if (next) {
      next.disabled = !page || !page.has_more;
    }

    setText(pageId, `Runs: ${pageSummary(page)}`);
  }

  function readNumberParam(params, key, fallback) {
    const raw = params.get(key);
    if (!raw) {
      return fallback;
    }
    const parsed = Number(raw);
    if (!Number.isFinite(parsed)) {
      return fallback;
    }
    return parsed;
  }

  function hydrateStateFromQuery() {
    const params = new URLSearchParams(window.location.search);
    state.limitRuns = Math.max(1, readNumberParam(params, "limit_runs", defaultLimitRuns));
    state.offsetRuns = Math.max(0, readNumberParam(params, "offset_runs", 0));

    if (view === "snapshot") {
      state.windowHours = Math.max(1, readNumberParam(params, "window_hours", 168));
      state.status = (params.get("status") || "").toUpperCase();
      state.connectorId = params.get("connector_id") || "";
    }

    if (view === "connector-detail") {
      state.status = (params.get("status") || "").toUpperCase();
    }
  }

  function updateQueryInUrl() {
    const params = buildQueryParams();
    const search = params.toString();
    const target = search ? `${window.location.pathname}?${search}` : window.location.pathname;
    window.history.replaceState(null, "", target);
  }

  function buildQueryParams() {
    const params = new URLSearchParams();

    if (view === "snapshot") {
      params.set("window_hours", String(state.windowHours));
      params.set("limit_runs", String(state.limitRuns));
      params.set("offset_runs", String(state.offsetRuns));
      if (state.status) {
        params.set("status", state.status);
      }
      if (state.connectorId) {
        params.set("connector_id", state.connectorId);
      }
      return params;
    }

    if (view === "connector-detail") {
      params.set("limit_runs", String(state.limitRuns));
      params.set("offset_runs", String(state.offsetRuns));
      if (state.status) {
        params.set("status", state.status);
      }
      return params;
    }

    return params;
  }

  function endpointWithParams() {
    if (!endpoint) {
      return "";
    }

    const params = buildQueryParams();
    const suffix = params.toString();
    return suffix ? `${endpoint}?${suffix}` : endpoint;
  }

  function renderSnapshot(payload) {
    const summary = payload.summary || {};

    setText("kpi-success-rate", `${Number(summary.success_rate_percent || 0).toFixed(1)}%`);
    setText("kpi-total-runs", String(summary.total_runs || 0));
    setText("kpi-pending", String(summary.pending_push_batches || 0));
    setText("kpi-freshness", formatSeconds(summary.freshness_lag_seconds_max));
    setText("generated-at", `Generated: ${formatDate(summary.generated_at)}`);

    const connectorsBody = document.getElementById("connectors-body");
    if (connectorsBody) {
      connectorsBody.textContent = "";
      for (const row of payload.connectors || []) {
        const tr = document.createElement("tr");
        appendLinkCell(tr, `/ops/connectors/${row.connector_id}`, row.connector_id);
        appendTextCell(tr, row.mode || "n/a");
        appendStatusCell(tr, row.last_status);
        if (row.last_run_id) {
          appendLinkCell(tr, `/ops/runs/${row.last_run_id}`, row.last_run_id);
        } else {
          appendTextCell(tr, "n/a");
        }
        appendTextCell(tr, formatSeconds(row.freshness_lag_seconds));
        appendTextCell(tr, String(row.pending_push_batches || 0));
        connectorsBody.appendChild(tr);
      }
    }

    const runsBody = document.getElementById("runs-body");
    if (runsBody) {
      runsBody.textContent = "";
      for (const run of payload.recent_runs || []) {
        const tr = document.createElement("tr");
        appendLinkCell(tr, `/ops/runs/${run.run_id}`, run.run_id);
        appendLinkCell(tr, `/ops/connectors/${run.connector_id}`, run.connector_id);
        appendStatusCell(tr, run.status);
        appendTextCell(tr, formatDate(run.started_at));
        appendTextCell(tr, formatSeconds(run.duration_seconds));
        appendTextCell(tr, String(run.upserts_count || 0));
        appendTextCell(tr, String(run.deletes_count || 0));
        appendLogLinksCell(tr, run.links);
        runsBody.appendChild(tr);
      }
    }

    updatePager(payload.runs_page, "runs-prev", "runs-next", "runs-page");
  }

  function renderConnectorDetail(payload) {
    const connector = payload.connector || {};

    setText("connector-mode", connector.mode || "n/a");
    setText("connector-status", connector.last_status || "UNKNOWN");
    setText("connector-freshness", formatSeconds(connector.freshness_lag_seconds));
    setText("connector-pending", String(connector.pending_push_batches || 0));
    setText("connector-updated-at", `Updated: ${formatDate(new Date().toISOString())}`);

    const body = document.getElementById("connector-runs-body");
    if (body) {
      body.textContent = "";
      for (const run of payload.recent_runs || []) {
        const tr = document.createElement("tr");
        appendLinkCell(tr, `/ops/runs/${run.run_id}`, run.run_id);
        appendStatusCell(tr, run.status);
        appendTextCell(tr, formatDate(run.started_at));
        appendTextCell(tr, formatDate(run.finished_at));
        appendTextCell(tr, formatSeconds(run.duration_seconds));
        appendTextCell(tr, run.error_class || "-");
        appendLogLinksCell(tr, run.links);
        body.appendChild(tr);
      }
    }

    updatePager(
      payload.runs_page,
      "connector-runs-prev",
      "connector-runs-next",
      "connector-runs-page",
    );
  }

  function renderRunDetail(payload) {
    setText("run-status", payload.status || "UNKNOWN");
    setText("run-connector", payload.connector_id || "n/a");
    setText("run-duration", formatSeconds(payload.duration_seconds));
    setText("run-started", formatDate(payload.started_at));
    setText("run-finished", formatDate(payload.finished_at));
    setText("run-error-class", payload.error_class || "-");
    setText("run-error-message", payload.error_message || "-");
    setText(
      "run-mut-counts",
      `upserts=${payload.upserts_count || 0}, deletes=${payload.deletes_count || 0}`,
    );
    setLink("run-link-splunk", payload.links ? payload.links.splunk_url : null);
    setLink("run-link-kestra", payload.links ? payload.links.kestra_url : null);
  }

  function renderPayload(payload) {
    if (view === "snapshot") {
      renderSnapshot(payload);
      return;
    }
    if (view === "connector-detail") {
      renderConnectorDetail(payload);
      return;
    }
    if (view === "run-detail") {
      renderRunDetail(payload);
    }
  }

  function bindSnapshotControls() {
    const windowSelect = document.getElementById("window-hours-filter");
    const statusSelect = document.getElementById("status-filter");
    const connectorInput = document.getElementById("connector-filter");

    if (windowSelect) {
      windowSelect.value = String(state.windowHours);
    }
    if (statusSelect) {
      statusSelect.value = state.status;
    }
    if (connectorInput) {
      connectorInput.value = state.connectorId;
    }

    const apply = document.getElementById("apply-filters");
    if (apply) {
      apply.addEventListener("click", () => {
        state.windowHours = Number(windowSelect ? windowSelect.value : state.windowHours);
        state.status = (statusSelect ? statusSelect.value : "").toUpperCase();
        state.connectorId = connectorInput ? connectorInput.value.trim() : "";
        state.offsetRuns = 0;
        updateQueryInUrl();
        refresh();
      });
    }

    const reset = document.getElementById("reset-filters");
    if (reset) {
      reset.addEventListener("click", () => {
        state.windowHours = 168;
        state.status = "";
        state.connectorId = "";
        state.offsetRuns = 0;

        if (windowSelect) {
          windowSelect.value = "168";
        }
        if (statusSelect) {
          statusSelect.value = "";
        }
        if (connectorInput) {
          connectorInput.value = "";
        }

        updateQueryInUrl();
        refresh();
      });
    }

    const prev = document.getElementById("runs-prev");
    if (prev) {
      prev.addEventListener("click", () => {
        state.offsetRuns = Math.max(0, state.offsetRuns - state.limitRuns);
        updateQueryInUrl();
        refresh();
      });
    }

    const next = document.getElementById("runs-next");
    if (next) {
      next.addEventListener("click", () => {
        state.offsetRuns += state.limitRuns;
        updateQueryInUrl();
        refresh();
      });
    }
  }

  function bindConnectorControls() {
    const statusSelect = document.getElementById("connector-status-filter");
    if (statusSelect) {
      statusSelect.value = state.status;
    }

    const apply = document.getElementById("connector-apply-filters");
    if (apply) {
      apply.addEventListener("click", () => {
        state.status = (statusSelect ? statusSelect.value : "").toUpperCase();
        state.offsetRuns = 0;
        updateQueryInUrl();
        refresh();
      });
    }

    const reset = document.getElementById("connector-reset-filters");
    if (reset) {
      reset.addEventListener("click", () => {
        state.status = "";
        state.offsetRuns = 0;
        if (statusSelect) {
          statusSelect.value = "";
        }
        updateQueryInUrl();
        refresh();
      });
    }

    const prev = document.getElementById("connector-runs-prev");
    if (prev) {
      prev.addEventListener("click", () => {
        state.offsetRuns = Math.max(0, state.offsetRuns - state.limitRuns);
        updateQueryInUrl();
        refresh();
      });
    }

    const next = document.getElementById("connector-runs-next");
    if (next) {
      next.addEventListener("click", () => {
        state.offsetRuns += state.limitRuns;
        updateQueryInUrl();
        refresh();
      });
    }
  }

  async function refresh() {
    const requestUrl = endpointWithParams();
    if (!requestUrl) {
      return;
    }

    try {
      const response = await fetch(requestUrl, {
        headers: {
          Accept: "application/json",
        },
        cache: "no-store",
      });
      if (!response.ok) {
        throw new Error(`request failed (${response.status})`);
      }
      const payload = await response.json();
      if (errorBanner) {
        errorBanner.hidden = true;
      }
      renderPayload(payload);
    } catch (error) {
      if (!errorBanner) {
        return;
      }
      errorBanner.textContent = `Unable to refresh ops data: ${String(error)}`;
      errorBanner.hidden = false;
    }
  }

  hydrateStateFromQuery();
  updateQueryInUrl();

  if (view === "snapshot") {
    bindSnapshotControls();
  }
  if (view === "connector-detail") {
    bindConnectorControls();
  }

  refresh();
  window.setInterval(refresh, refreshMs);
})();
