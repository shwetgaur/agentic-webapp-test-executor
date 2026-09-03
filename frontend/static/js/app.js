/** Agentic Test Executor — web UI */

let lastReport = null;
let lastMarkdown = null;
let lastLog = null;

const $ = (id) => document.getElementById(id);

async function checkHealth() {
  const badge = $("health-badge");
  try {
    const res = await fetch("/health");
    const data = await res.json();
    badge.textContent = data.status === "ok" ? "API Online" : "Degraded";
    badge.className = "badge badge-ok";
  } catch {
    badge.textContent = "API Offline";
    badge.className = "badge badge-muted";
  }
}

async function loadSample(id) {
  if (!id) return;
  const res = await fetch(`/api/v1/samples/${id}`);
  if (!res.ok) return;
  const data = await res.json();
  $("test_id").value = data.test_id || "";
  $("site_url").value = data.site_url || "";
  $("feature").value = data.feature || "";
  $("test_name").value = data.test_name || "";
  $("objective").value = data.objective || "";
  $("expected_outcome").value = data.expected_outcome || "";
  $("environment").value = data.environment || "develop";
  $("owner_team").value = data.owner_team || "";
  $("steps").value = (data.steps || []).join("\n");
}

function buildPrompt() {
  const steps = $("steps").value
    .split("\n")
    .map((s) => s.trim())
    .filter(Boolean);

  const prompt = {
    test_id: $("test_id").value.trim(),
    site_url: $("site_url").value.trim(),
    feature: $("feature").value.trim(),
    test_name: $("test_name").value.trim(),
    objective: $("objective").value.trim(),
    expected_outcome: $("expected_outcome").value.trim(),
    environment: $("environment").value,
    steps,
  };

  const owner = $("owner_team").value.trim();
  if (owner) prompt.owner_team = owner;
  return prompt;
}

function showLoading(on) {
  $("loading").classList.toggle("hidden", !on);
  $("run-btn").disabled = on;
}

function showError(msg) {
  $("error-box").textContent = msg;
  $("error-box").classList.remove("hidden");
  $("result-content").classList.add("hidden");
  $("result-empty").classList.add("hidden");
}

function clearError() {
  $("error-box").classList.add("hidden");
}

function formatTs(iso) {
  if (!iso) return "n/a";
  try {
    const d = new Date(iso);
    return d.toISOString().replace("T", " ").replace("Z", " UTC");
  } catch {
    return iso;
  }
}

function formatTsLog(iso) {
  if (!iso) return "n/a";
  try {
    const d = new Date(iso);
    return d.toISOString().replace(/\.\d{3}Z$/, (m) => m.slice(0, 4) + "Z");
  } catch {
    return iso;
  }
}

function renderLogFromReport(report) {
  const s = report.summary || {};
  const lines = [
    "=".repeat(80),
    `TEST RUN LOG — ${report.run_id}`,
    `Suite: ${report.suite_name || report.suite_id} (${report.suite_id})`,
    `Module / Feature: ${report.module || "n/a"}`,
    `Site URL: ${report.site_url || "n/a"}`,
    `Environment: ${report.environment || "n/a"}`,
    `Objective: ${report.objective || "n/a"}`,
    `Expected Outcome: ${report.expected_outcome || "n/a"}`,
    `Status: ${(report.status || "").toUpperCase()}`,
    `Run started:  ${formatTsLog(report.started_at)}`,
    `Run finished: ${formatTsLog(report.finished_at)}`,
    `Total duration: ${report.duration_ms} ms`,
    `Summary: ${s.passed ?? 0} passed / ${s.failed ?? 0} failed / ${s.skipped ?? 0} skipped (total ${s.total ?? 0})`,
    "=".repeat(80),
    "",
  ];

  const traces = report.agent_traces || [];
  if (traces.length) {
    lines.push("--- Agent Pipeline ---", "");
    for (const t of traces) {
      lines.push(`[${formatTsLog(t.timestamp)}] ${t.agent}.${t.phase} — ${t.detail}`);
    }
    lines.push("");
  }

  lines.push("--- Step Execution (timestamped) ---", "");
  for (const step of report.steps || []) {
    lines.push(
      `[${formatTsLog(step.started_at)}] STEP ${step.step_id} START  ${step.action}  ${step.description || ""}`.trimEnd()
    );
    const parts = [
      `status=${step.status}`,
      `duration=${step.duration_ms ?? 0}ms`,
      `finished=${formatTsLog(step.finished_at)}`,
    ];
    if (step.expected) parts.push(`expected=${step.expected}`);
    if (step.actual) parts.push(`actual=${step.actual}`);
    if (step.error) parts.push(`error=${step.error}`);
    if (step.screenshot_path) parts.push(`screenshot=${step.screenshot_path}`);
    lines.push(`[${formatTsLog(step.finished_at)}] STEP ${step.step_id} END    ${parts.join(" | ")}`);
    lines.push("");
  }

  const n = report.notify || {};
  lines.push(
    "--- Notification ---",
    `Triggered: ${n.triggered ?? false}`,
    `Team: ${n.team || "n/a"}`,
    `Channel: ${n.channel || "n/a"}`,
    `Ticket: ${n.ticket_id || "n/a"}`,
    "",
    "=".repeat(80),
    `END OF LOG — ${report.run_id}`,
    "=".repeat(80),
    ""
  );
  return lines.join("\n");
}

function downloadBlob(content, filename, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

function renderReport(report) {
  lastReport = report;
  clearError();
  $("result-empty").classList.add("hidden");
  $("result-content").classList.remove("hidden");
  $("result-hint").textContent = `Last run: ${report.run_id}`;

  const passed = report.status === "passed";
  const banner = $("status-banner");
  banner.textContent = passed ? "PASSED" : "FAILED";
  banner.className = `status-banner ${passed ? "status-pass" : "status-fail"}`;

  $("run-id").textContent = report.run_id;
  $("duration").textContent = `${report.duration_ms} ms`;
  $("summary").textContent = `${report.summary.passed} passed / ${report.summary.failed} failed / ${report.summary.skipped} skipped`;

  const stepList = $("step-list");
  stepList.innerHTML = "";
  for (const step of report.steps || []) {
    const div = document.createElement("div");
    const st = step.status;
    div.className = `step-item step-${st === "passed" ? "pass" : st === "skipped" ? "skip" : "fail"}`;
    const icon = st === "passed" ? "✓" : st === "skipped" ? "○" : "✗";
    const timing =
      step.started_at || step.duration_ms != null
        ? `<div class="step-meta">${formatTs(step.started_at)} → ${formatTs(step.finished_at)} · ${step.duration_ms ?? 0} ms</div>`
        : "";
    div.innerHTML = `<strong>${icon} ${step.step_id}</strong> · ${step.action}<br>${step.description || ""}${timing}`;
    if (step.error) {
      const err = document.createElement("div");
      err.className = "step-error";
      err.textContent = step.error;
      div.appendChild(err);
    }
    stepList.appendChild(div);
  }

  const traces = $("agent-traces");
  traces.innerHTML = "";
  const agentTraces = report.agent_traces || [];
  if (!agentTraces.length) {
    traces.innerHTML = '<div class="trace-item">Legacy run (no agent traces).</div>';
  } else {
    for (const t of agentTraces) {
      const div = document.createElement("div");
      div.className = "trace-item";
      div.innerHTML = `<strong>${t.agent}</strong> · <code>${t.phase}</code> — ${t.detail}` +
        (t.timestamp ? `<div class="step-meta">${formatTs(t.timestamp)}</div>` : "");
      traces.appendChild(div);
    }
  }

  const notify = report.notify || {};
  const nbox = $("notify-box");
  if (notify.triggered) {
    nbox.className = "notify-box notify-alert";
    nbox.textContent = `Alert sent → ${notify.team} | Ticket: ${notify.ticket_id}`;
  } else {
    nbox.className = "notify-box notify-ok";
    nbox.textContent = "No failure notification (test passed or notify disabled).";
  }
}

async function fetchMarkdown(runId) {
  const res = await fetch(`/api/v1/reports/${runId}/markdown`);
  if (res.ok) return res.text();
  return null;
}

async function fetchLog(runId) {
  const res = await fetch(`/api/v1/reports/${runId}/log`);
  if (res.ok) return res.text();
  return null;
}

async function parseJsonResponse(res) {
  const text = await res.text();
  if (!text) return { data: null, raw: "" };
  try {
    return { data: JSON.parse(text), raw: text };
  } catch {
    return { data: null, raw: text };
  }
}

async function runTest(e) {
  e.preventDefault();
  clearError();
  showLoading(true);

  const prompt = buildPrompt();
  const useAgents = $("use_agents").checked;

  const body = {
    prompt,
    headless: $("headless").checked,
    use_llm: $("use_llm").checked,
    use_discovery: $("use_discovery").checked,
    use_healer: $("use_healer").checked,
  };

  const url = useAgents ? "/api/v1/run/agents" : "/api/v1/run/structured";

  if (!useAgents) {
    body.use_agents = false;
  }

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const { data, raw } = await parseJsonResponse(res);
    if (!res.ok) {
      const detail = data?.detail;
      const message = detail
        ? (typeof detail === "string" ? detail : JSON.stringify(detail, null, 2))
        : raw || `Request failed (${res.status})`;
      showError(message);
      return;
    }
    if (!data) {
      showError(raw || "Empty response from server");
      return;
    }
    renderReport(data);
    lastMarkdown = await fetchMarkdown(data.run_id);
    lastLog = await fetchLog(data.run_id);
  } catch (err) {
    showError(String(err));
  } finally {
    showLoading(false);
  }
}

function downloadJson() {
  if (!lastReport) {
    showError("Run a test first to download the JSON report.");
    return;
  }
  downloadBlob(JSON.stringify(lastReport, null, 2), `${lastReport.run_id}.json`, "application/json");
}

function downloadMd() {
  if (!lastReport) {
    showError("Run a test first to download the Markdown report.");
    return;
  }
  if (!lastMarkdown) {
    showError("Markdown report is not available for this run.");
    return;
  }
  downloadBlob(lastMarkdown, `${lastReport.run_id}.md`, "text/markdown");
}

async function downloadLog() {
  if (!lastReport) {
    showError("Run a test first to download the detailed log.");
    return;
  }

  let logText = lastLog;
  if (!logText) {
    logText = await fetchLog(lastReport.run_id);
  }
  if (!logText) {
    logText = renderLogFromReport(lastReport);
  }

  if (!logText) {
    showError("Could not build detailed log for this run.");
    return;
  }

  lastLog = logText;
  clearError();
  downloadBlob(logText, `${lastReport.run_id}.log`, "text/plain;charset=utf-8");
}

document.addEventListener("DOMContentLoaded", () => {
  checkHealth();
  $("test-form").addEventListener("submit", runTest);
  $("sample-select").addEventListener("change", (e) => loadSample(e.target.value));
  $("download-json").addEventListener("click", downloadJson);
  $("download-md").addEventListener("click", downloadMd);
  $("download-log").addEventListener("click", downloadLog);
});
