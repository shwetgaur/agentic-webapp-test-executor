/** Agentic Test Executor — web UI */

let lastReport = null;
let lastMarkdown = null;

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
    div.innerHTML = `<strong>${icon} ${step.step_id}</strong> · ${step.action}<br>${step.description || ""}`;
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
      div.innerHTML = `<strong>${t.agent}</strong> · <code>${t.phase}</code> — ${t.detail}`;
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
  } catch (err) {
    showError(String(err));
  } finally {
    showLoading(false);
  }
}

function downloadJson() {
  if (!lastReport) return;
  const blob = new Blob([JSON.stringify(lastReport, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${lastReport.run_id}.json`;
  a.click();
}

function downloadMd() {
  if (!lastMarkdown) return;
  const blob = new Blob([lastMarkdown], { type: "text/markdown" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${lastReport.run_id}.md`;
  a.click();
}

document.addEventListener("DOMContentLoaded", () => {
  checkHealth();
  $("test-form").addEventListener("submit", runTest);
  $("sample-select").addEventListener("change", (e) => loadSample(e.target.value));
  $("download-json").addEventListener("click", downloadJson);
  $("download-md").addEventListener("click", downloadMd);
});
