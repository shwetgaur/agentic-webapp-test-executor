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

function fillPromptForm(data) {
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

async function loadSample(id) {
  if (!id) return;
  const res = await fetch(`/api/v1/samples/${id}`);
  if (!res.ok) return;
  const data = await res.json();
  fillPromptForm(data);
}

async function importExcelFile(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch("/api/v1/import/excel", { method: "POST", body: form });
  const { data, raw } = await parseJsonResponse(res);
  if (!res.ok) {
    showError(data?.detail ? String(data.detail) : raw || "Excel import failed");
    return;
  }
  if (!data?.prompts?.length) {
    showError("Excel file contained no test cases.");
    return;
  }
  clearError();
  fillPromptForm(data.prompts[0]);
  showDownloadHint(
    data.count > 1
      ? `Loaded first of ${data.count} test cases from Excel.`
      : "Loaded test case from Excel."
  );
}

async function uploadSuiteJsonFile(file) {
  const text = await file.text();
  let suite;
  try {
    suite = JSON.parse(text);
  } catch {
    showError("Invalid JSON file.");
    return;
  }
  const testId = suite.suite_id || $("test_id").value.trim();
  if (!testId) {
    showError("Suite JSON must include suite_id or fill Test ID first.");
    return;
  }
  const res = await fetch("/api/v1/suites/upload", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ test_id: testId, suite }),
  });
  const { data, raw } = await parseJsonResponse(res);
  if (!res.ok) {
    showError(data?.detail ? String(data.detail) : raw || "Suite upload failed");
    return;
  }
  clearError();
  showDownloadHint(`Cached suite saved for ${testId}. You can run with Replay checked.`);
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

function showDownloadHint(msg) {
  const hint = $("download-hint");
  if (!hint) return;
  hint.textContent = msg;
  hint.classList.remove("hidden");
  setTimeout(() => hint.classList.add("hidden"), 5000);
}

function updateDownloadLinks(report) {
  const logLink = $("download-log");
  if (!logLink || !report?.run_id) return;
  logLink.href = `/api/v1/reports/${encodeURIComponent(report.run_id)}/log`;
  logLink.download = `${report.run_id}.log`;
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
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 250);
}

function screenshotUrl(path) {
  if (!path) return null;
  if (path.startsWith("/api/")) return path;
  const name = path.split(/[/\\]/).pop();
  return name ? `/api/v1/screenshots/${name}` : null;
}

/** Site URL + feature used for locator cache (from discovery traces or form). */
function locatorContextFromReport(report) {
  const traces = report.agent_traces || [];
  for (const t of traces) {
    if (t.agent !== "discovery_agent") continue;
    const hit = t.detail.match(/for '([^']+)' on (https?:\/\/\S+)/);
    if (hit) return { site_url: hit[2].replace(/[.,)]+$/, ""), feature: hit[1] };
    const scan = t.detail.match(/for feature '([^']+)':\s*(https?:\/\/\S+)/);
    if (scan) return { site_url: scan[2].replace(/,$/, ""), feature: scan[1] };
  }
  const featureEl = $("feature");
  return {
    site_url: report.site_url || $("site_url")?.value || "",
    feature: report.module || featureEl?.value || "",
  };
}

async function setupLocatorDownload(report) {
  const locatorLink = $("download-locator");
  if (!locatorLink) return;

  const ctx = locatorContextFromReport(report);
  if (!ctx.site_url || !ctx.feature) {
    locatorLink.classList.add("hidden");
    return;
  }

  try {
    const q = new URLSearchParams({ site_url: ctx.site_url, feature: ctx.feature });
    const existsRes = await fetch(`/api/v1/locators/exists?${q}`);
    if (!existsRes.ok) {
      locatorLink.classList.add("hidden");
      return;
    }
    const exists = await existsRes.json();
    if (!exists.cached) {
      locatorLink.classList.add("hidden");
      return;
    }

    locatorLink.classList.remove("hidden");
    locatorLink.onclick = async (ev) => {
      ev.preventDefault();
      try {
        const res = await fetch(`/api/v1/locators?${q}`);
        if (!res.ok) return;
        const moduleMap = await res.json();
        const filename = `${exists.cache_key || "locator_cache"}.json`;
        downloadBlob(JSON.stringify(moduleMap, null, 2), filename, "application/json");
      } catch {
        /* ignore */
      }
    };
  } catch {
    locatorLink.classList.add("hidden");
  }
}

function sumLlmTokens(llmCalls) {
  let prompt = 0;
  let completion = 0;
  let total = 0;
  for (const c of llmCalls || []) {
    prompt += c.prompt_tokens || 0;
    completion += c.completion_tokens || 0;
    total += c.total_tokens || 0;
  }
  return { prompt, completion, total };
}

function updateTokenUsageBar(report) {
  if (!report) {
    $("token-prompt").textContent = "Prompt: —";
    $("token-completion").textContent = "Completion: —";
    $("token-total").textContent = "Total: —";
    return;
  }
  const llmCalls = report.llm_calls || [];
  const sums = sumLlmTokens(llmCalls);
  const has = llmCalls.length > 0;
  $("token-prompt").textContent = has ? `Prompt: ${sums.prompt}` : "Prompt: —";
  $("token-completion").textContent = has ? `Completion: ${sums.completion}` : "Completion: —";
  $("token-total").textContent = has ? `Total: ${sums.total}` : "Total: —";
}

function renderTokenUsagePanel(report) {
  const panel = $("token-usage-panel");
  if (!panel) return;
  panel.innerHTML = "";
  const llmCalls = report.llm_calls || [];
  const sums = sumLlmTokens(llmCalls);
  if (!llmCalls.length) {
    const mode = report.execution_mode || "unknown";
    panel.innerHTML =
      `<div class="token-stat"><span>Run mode</span><strong>${mode}</strong></div>` +
      `<div class="token-stat"><span>LLM tokens</span><strong>0</strong><span>No LLM calls (direct JSON or replay).</span></div>`;
    return;
  }
  const cards = [
    ["Prompt tokens", sums.prompt],
    ["Completion tokens", sums.completion],
    ["Total tokens", sums.total],
    ["LLM calls", llmCalls.length],
  ];
  for (const [label, val] of cards) {
    const div = document.createElement("div");
    div.className = "token-stat";
    div.innerHTML = `<span>${label}</span><strong>${val}</strong>`;
    panel.appendChild(div);
  }
}

function parseSuiteJsonText(text) {
  const suite = JSON.parse(text);
  if (!suite.steps?.length) throw new Error("TestSuite JSON must include a non-empty steps array.");
  if (!suite.suite_id) throw new Error("TestSuite JSON must include suite_id.");
  return suite;
}

async function loadCachedSuiteIntoTextarea() {
  const testId = $("test_id").value.trim();
  if (!testId) {
    showError("Enter Test ID to load cached suite.");
    return;
  }
  const res = await fetch(`/api/v1/suites/${encodeURIComponent(testId)}/latest`);
  const { data, raw } = await parseJsonResponse(res);
  if (!res.ok) {
    showError(data?.detail ? String(data.detail) : raw || "No cached suite for this Test ID.");
    return;
  }
  $("suite-json").value = JSON.stringify(data, null, 2);
  clearError();
  showDownloadHint(`Loaded cached suite for ${testId}. Click Run Playwright (JSON).`);
}

async function exportPlaywrightSpec() {
  const text = $("suite-json").value.trim();
  if (!text) {
    showError("Paste or load TestSuite JSON first.");
    return;
  }
  let suite;
  try {
    suite = parseSuiteJsonText(text);
  } catch (err) {
    showError(String(err.message || err));
    return;
  }
  const res = await fetch("/api/v1/suites/export/playwright", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(suite),
  });
  if (!res.ok) {
    const { data, raw } = await parseJsonResponse(res);
    showError(data?.detail ? String(data.detail) : raw || "Export failed");
    return;
  }
  const spec = await res.text();
  downloadBlob(spec, `${suite.suite_id}_playwright.spec.ts`, "text/plain;charset=utf-8");
  clearError();
}

async function runJsonPlaywright() {
  const text = $("suite-json").value.trim();
  if (!text) {
    showError("Paste TestSuite JSON to run Playwright directly.");
    return;
  }
  let suite;
  try {
    suite = parseSuiteJsonText(text);
  } catch (err) {
    showError(String(err.message || err));
    return;
  }
  clearError();
  showLoading(true);
  $("run-json-btn").disabled = true;
  try {
    const res = await fetch("/api/v1/run/json", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ suite, headless: $("headless").checked }),
    });
    const { data, raw } = await parseJsonResponse(res);
    if (!res.ok) {
      showError(data?.detail ? String(data.detail) : raw || `Request failed (${res.status})`);
      return;
    }
    renderReport(data);
    lastMarkdown = await fetchMarkdown(data.run_id);
    const serverLog = await fetchLog(data.run_id);
    if (serverLog) lastLog = serverLog;
    showDownloadHint("Direct Playwright run complete (TestSuite JSON → executor).");
  } catch (err) {
    showError(String(err));
  } finally {
    showLoading(false);
    $("run-json-btn").disabled = false;
  }
}

function renderReport(report) {
  lastReport = report;
  updateTokenUsageBar(report);
  renderTokenUsagePanel(report);
  lastLog = renderLogFromReport(report);
  updateDownloadLinks(report);
  clearError();
  const hint = $("download-hint");
  if (hint) hint.classList.add("hidden");
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
    const shotUrl = screenshotUrl(step.screenshot_path);
    if (shotUrl) {
      const shot = document.createElement("a");
      shot.className = "step-screenshot";
      shot.href = shotUrl;
      shot.target = "_blank";
      shot.rel = "noopener";
      shot.textContent = "View failure screenshot";
      div.appendChild(shot);
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
      const metrics = [];
      if (t.duration_ms != null) metrics.push(`${t.duration_ms} ms`);
      if (t.tokens_prompt != null) metrics.push(`tokens ${t.tokens_prompt}/${t.tokens_completion || 0}`);
      const metricStr = metrics.length ? ` · ${metrics.join(" · ")}` : "";
      div.innerHTML = `<strong>${t.agent}</strong> · <code>${t.phase}</code>${metricStr} — ${t.detail}` +
        (t.timestamp ? `<div class="step-meta">${formatTs(t.timestamp)}</div>` : "");
      traces.appendChild(div);
    }
  }

  const perf = $("perf-panel");
  perf.innerHTML = "";
  const phaseTimings = report.phase_timings || [];
  const llmCalls = report.llm_calls || [];
  if (report.execution_mode === "direct_json") {
    const tag = document.createElement("div");
    tag.className = "perf-tag";
    tag.textContent = "Direct Playwright — TestSuite JSON (no agents)";
    perf.appendChild(tag);
  }
  if (phaseTimings.length || llmCalls.length || report.replay_mode) {
    if (report.replay_mode) {
      const tag = document.createElement("div");
      tag.className = "perf-tag";
      tag.textContent = "Replay mode — skipped LLM + discovery";
      perf.appendChild(tag);
    }
    if (report.suite_snapshot_path) {
      const snap = document.createElement("div");
      snap.className = "perf-meta";
      snap.textContent = `Cached suite: ${report.suite_snapshot_path}`;
      perf.appendChild(snap);
    }
    if (phaseTimings.length) {
      const table = document.createElement("table");
      table.className = "perf-table";
      table.innerHTML = "<thead><tr><th>Phase</th><th>Duration (ms)</th></tr></thead>";
      const tbody = document.createElement("tbody");
      for (const pt of [...phaseTimings].sort((a, b) => b.duration_ms - a.duration_ms)) {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${pt.phase}</td><td>${pt.duration_ms}</td>`;
        tbody.appendChild(tr);
      }
      table.appendChild(tbody);
      perf.appendChild(table);
    }
    if (llmCalls.length) {
      const llmHead = document.createElement("div");
      llmHead.className = "perf-subhead";
      llmHead.textContent = "LLM token usage";
      perf.appendChild(llmHead);
      const ltable = document.createElement("table");
      ltable.className = "perf-table";
      ltable.innerHTML =
        "<thead><tr><th>Caller</th><th>Prompt</th><th>Completion</th><th>Total</th><th>Latency (ms)</th></tr></thead>";
      const lbody = document.createElement("tbody");
      for (const c of llmCalls) {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${c.caller}</td><td>${c.prompt_tokens}</td><td>${c.completion_tokens}</td><td>${c.total_tokens}</td><td>${c.latency_ms}</td>`;
        lbody.appendChild(tr);
      }
      ltable.appendChild(lbody);
      perf.appendChild(ltable);
    }
  } else {
    perf.innerHTML = '<div class="perf-meta">No performance metrics for this run.</div>';
  }

  const suiteLink = $("download-suite");
  if (suiteLink && report.suite_snapshot_path) {
    suiteLink.classList.remove("hidden");
    suiteLink.onclick = async (ev) => {
      ev.preventDefault();
      const testId = report.suite_id;
      if (!testId) return;
      try {
        const res = await fetch(`/api/v1/suites/${encodeURIComponent(testId)}/latest`);
        if (!res.ok) return;
        const suite = await res.json();
        downloadBlob(JSON.stringify(suite, null, 2), `${testId}_suite.json`, "application/json");
      } catch {
        /* ignore */
      }
    };
  } else if (suiteLink) {
    suiteLink.classList.add("hidden");
  }

  setupLocatorDownload(report);

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

  const useReplay = $("use_replay").checked;
  const body = {
    prompt,
    headless: $("headless").checked,
    use_llm: useReplay ? false : $("use_llm").checked,
    use_discovery: useReplay ? false : $("use_discovery").checked,
    use_healer: $("use_healer").checked,
    use_replay: useReplay,
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
    const serverLog = await fetchLog(data.run_id);
    if (serverLog) lastLog = serverLog;
  } catch (err) {
    showError(String(err));
  } finally {
    showLoading(false);
  }
}

function downloadJson() {
  if (!lastReport) {
    showDownloadHint("Run a test first to download the JSON report.");
    return;
  }
  downloadBlob(JSON.stringify(lastReport, null, 2), `${lastReport.run_id}.json`, "application/json");
}

function downloadMd() {
  if (!lastReport) {
    showDownloadHint("Run a test first to download the Markdown report.");
    return;
  }
  if (!lastMarkdown) {
    showDownloadHint("Markdown report is not available for this run.");
    return;
  }
  downloadBlob(lastMarkdown, `${lastReport.run_id}.md`, "text/markdown");
}

function downloadLogSync() {
  if (!lastReport) {
    showDownloadHint("Run a test first to download the detailed log.");
    return false;
  }
  const logText = lastLog || renderLogFromReport(lastReport);
  if (!logText) {
    showDownloadHint("Could not build detailed log for this run.");
    return false;
  }
  downloadBlob(logText, `${lastReport.run_id}.log`, "text/plain;charset=utf-8");
  return true;
}

document.addEventListener("DOMContentLoaded", () => {
  checkHealth();
  updateTokenUsageBar(null);
  $("test-form").addEventListener("submit", runTest);
  $("sample-select").addEventListener("change", (e) => loadSample(e.target.value));
  $("download-json").addEventListener("click", downloadJson);
  $("download-md").addEventListener("click", downloadMd);
  $("download-log").addEventListener("click", (e) => {
    e.preventDefault();
    downloadLogSync();
  });

  const excelInput = $("excel-file");
  const excelBtn = $("import-excel-btn");
  if (excelBtn && excelInput) {
    excelBtn.addEventListener("click", () => excelInput.click());
    excelInput.addEventListener("change", () => {
      const f = excelInput.files?.[0];
      if (f) importExcelFile(f);
      excelInput.value = "";
    });
  }

  const suiteInput = $("suite-upload-file");
  const suiteBtn = $("upload-suite-btn");
  if (suiteBtn && suiteInput) {
    suiteBtn.addEventListener("click", () => suiteInput.click());
    suiteInput.addEventListener("change", () => {
      const f = suiteInput.files?.[0];
      if (f) uploadSuiteJsonFile(f);
      suiteInput.value = "";
    });
  }

  const suiteRunFile = $("suite-run-file");
  $("load-suite-json-btn")?.addEventListener("click", () => suiteRunFile?.click());
  suiteRunFile?.addEventListener("change", async () => {
    const f = suiteRunFile.files?.[0];
    if (!f) return;
    $("suite-json").value = await f.text();
    suiteRunFile.value = "";
    clearError();
  });
  $("load-cached-suite-btn")?.addEventListener("click", () => loadCachedSuiteIntoTextarea());
  $("export-playwright-btn")?.addEventListener("click", () => exportPlaywrightSpec());
  $("run-json-btn")?.addEventListener("click", () => runJsonPlaywright());
});
