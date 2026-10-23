"use strict";

const $ = (selector, root = document) => root.querySelector(selector);
const escapeHTML = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const icon = (name) => `<img src="/icons/${name}.svg" alt="">`;
const btn = (label, action, name, classes = "", attrs = "") =>
  `<button class="btn ${classes}" data-action="${action}" ${attrs}>${name ? icon(name) : ""}${label}</button>`;
const iconButton = (label, action, name, attrs = "") =>
  `<button class="icon-btn" data-action="${action}" title="${label}" aria-label="${label}" ${attrs}>${icon(name)}</button>`;
const tag = (label, style = "") =>
  `<span class="tag ${style}">${escapeHTML(label)}</span>`;
const date = (value) =>
  new Date(value).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
const state = {
  view: "bench",
  cases: [],
  runs: [],
  categories: [],
  selected: new Set(),
  current: null,
  focus: null,
  detailTab: "prompt",
  category: "All trials",
  query: "",
  mode: "demo",
  profile: "candidate",
  resultFilter: "all",
  compare: [],
  token: "",
  settings: {},
  active: null,
  key_available: false,
};
let toastTimer,
  polling = false;

function toast(message, error = false) {
  const el = $("#toast");
  el.textContent = message;
  el.className = `visible${error ? " error" : ""}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (el.className = ""), 5000);
}

async function api(path, data) {
  const response = await fetch(
    `/api/${path}`,
    data === undefined
      ? {}
      : {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-ForgeBench-Token": state.token,
          },
          body: JSON.stringify(data),
        },
  );
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || "The local request failed.");
  return body;
}

async function refresh() {
  const data = await api("bootstrap");
  Object.assign(state, {
    cases: data.cases,
    categories: data.categories,
    runs: data.runs,
    settings: data.settings,
    token: data.token,
    active: data.active_run,
    key_available: data.key_available,
  });
  $("#nav-count").textContent = state.cases.length;
}

function heading(title, subtitle, action = "") {
  return `<div class="page-heading"><div><h1>${title}</h1><p>${subtitle}</p></div>${action}</div>`;
}

function empty(title, body, action = "", name = "flask-conical") {
  return `<div class="empty">${icon(name)}<h3>${title}</h3><p>${body}</p>${action}</div>`;
}

function render() {
  const labels = {
    bench: "Test bench",
    library: "Trial library",
    history: "Run history",
    compare: "Compare runs",
    settings: "Model connection",
  };
  $("#crumb").textContent = labels[state.view];
  document
    .querySelectorAll("[data-view]")
    .forEach((el) =>
      el.classList.toggle("active", el.dataset.view === state.view),
    );
  const renderers = {
    bench: renderBench,
    library: renderLibrary,
    history: renderHistory,
    compare: renderCompare,
    settings: renderSettings,
  };
  $("#main").innerHTML = renderers[state.view]();
  if (["bench", "library"].includes(state.view)) renderTrials();
  if (state.view === "compare") loadComparison();
}

function stats() {
  const run = state.current;
  const values = run
    ? [
        [
          "Trials evaluated",
          `${run.completed}<span>/ ${run.total}</span>`,
          "flask-conical",
          "",
        ],
        ["Passed", run.passed, "circle-check", "good"],
        [
          "Failed / errors",
          `${run.failed}<span>/ ${run.errors}</span>`,
          "circle-x",
          "",
        ],
        [
          run.mode === "demo" ? "Data source" : "Elapsed time",
          run.mode === "demo"
            ? "<small>Demo</small>"
            : `${(run.duration_ms / 1000).toFixed(1)}<span>seconds</span>`,
          "activity",
          "",
        ],
      ]
    : [
        [
          "Trials in suite",
          `${state.cases.length}<span>ready to run</span>`,
          "flask-conical",
          "",
        ],
        [
          "Risk categories",
          `${state.categories.length}<span>evaluation areas</span>`,
          "layers",
          "",
        ],
        [
          "Saved runs",
          `${state.runs.length}<span>local only</span>`,
          "history",
          "",
        ],
        [
          "Model source",
          state.mode === "demo"
            ? "<small>Demo<span>offline fixtures</span></small>"
            : "<small>Endpoint<span>configured model</span></small>",
          "cpu",
          "",
        ],
      ];
  return `<div class="stats">${values.map(([label, value, name, cls]) => `<div class="stat"><div class="stat-label">${label}${icon(name)}</div><div class="stat-value ${cls}">${value}</div></div>`).join("")}</div>`;
}

function runStrip() {
  const run = state.current;
  if (!run) return "";
  const running = run.status === "running";
  return `<section class="run-strip" aria-label="Run progress"><div><h3>${escapeHTML(run.model)} ${tag(run.mode === "demo" ? "Synthetic demo" : run.status, run.mode === "demo" ? "demo" : "green")}</h3><p>${running ? "Running" : escapeHTML(run.status[0].toUpperCase() + run.status.slice(1))} &middot; ${run.completed} of ${run.total} trials evaluated${run.mode === "demo" ? " &middot; No model called" : ""}</p></div><div class="toolbar">${running ? `<progress value="${run.completed}" max="${run.total}" aria-label="Trial progress"></progress>${btn("Stop", "cancel", "square")}` : `${btn("Export JSON", "export", "download")}${btn("Clear view", "clear-run", "x")}`}</div></section>`;
}

function renderBench() {
  return `${heading("Test bench", "Reliability under real-world pressure.", btn("New trial", "new-trial", "plus"))}
    <div id="stats-region">${stats()}</div>${modelPanel()}<div id="run-region">${runStrip()}</div>
    <div class="bench-layout"><section class="bench-main"><div class="section-head"><div><span class="section-kicker">EVALUATION SUITE</span><h2>Reliability gauntlet <span class="count-label">${state.cases.length}</span></h2></div>${tag("Synthetic trials")}</div>${trialFilters()}<div id="trial-list"></div><div class="list-note"><span id="selection-count">${state.selected.size} selected</span><span>${icon("shield-check")}Deterministic checks</span></div></section>
    <aside class="bench-aside"><div id="detail-region">${detail()}</div></aside></div>`;
}

function trialFilters() {
  return `<div class="filterbar" aria-label="Trial categories">${["All trials", ...state.categories].map((cat) => `<button aria-pressed="${state.category === cat}" class="${state.category === cat ? "active" : ""}" data-action="category" data-category="${cat}">${cat}</button>`).join("")}</div>
    <div class="search">${icon("search")}<input id="trial-search" aria-label="Search trials" placeholder="Search trials..." value="${escapeHTML(state.query)}"></div>
    ${state.current && state.view === "bench" ? `<div class="filterbar" aria-label="Result filter">${["all", "failed", "passed", "error"].map((filter) => `<button class="${state.resultFilter === filter ? "active" : ""}" data-action="result-filter" data-filter="${filter}">${filter === "all" ? "All results" : filter[0].toUpperCase() + filter.slice(1)}</button>`).join("")}</div>` : ""}`;
}

function visibleTrials() {
  const cases =
    state.current && state.view === "bench"
      ? state.current.results.map((r) => r.case)
      : state.cases;
  return cases.filter(
    (c) =>
      (state.category === "All trials" || c.category === state.category) &&
      `${c.title} ${c.pressure} ${c.category}`
        .toLowerCase()
        .includes(state.query.toLowerCase()) &&
      (!state.current ||
        state.view !== "bench" ||
        state.resultFilter === "all" ||
        state.current.results.find((r) => r.case_id === c.id)?.status ===
          state.resultFilter),
  );
}

function renderTrials() {
  const trials = visibleTrials();
  const allSelected =
    trials.length > 0 && trials.every((c) => state.selected.has(c.id));
  $("#trial-list").innerHTML =
    `<div class="table-head"><input type="checkbox" id="select-all" aria-label="Select all visible trials" ${allSelected ? "checked" : ""}><span>Trial</span><span>${state.current && state.view === "bench" ? "Result" : "Assertions"}</span></div>` +
    (trials.length
      ? trials
          .map((c) => {
            const result =
              state.view === "bench" &&
              state.current?.results.find((r) => r.case_id === c.id);
            const icons = {
              passed: "circle-check",
              failed: "circle-x",
              error: "circle-x",
              running: "loader-circle",
              pending: "circle-dot",
              skipped: "circle-dot",
            };
            const categoryIcon =
              {
                Instructions: "shield-check",
                Grounding: "search",
                "Output contracts": "layers",
                Reasoning: "git-compare-arrows",
              }[c.category] || "flask-conical";
            return `<div class="trial-row ${state.focus === c.id ? "selected" : ""}"><input type="checkbox" data-select="${c.id}" aria-label="Select ${escapeHTML(c.title)}" ${state.selected.has(c.id) ? "checked" : ""}><button class="trial-info" data-action="inspect" data-id="${c.id}" aria-pressed="${state.focus === c.id}"><span class="trial-symbol">${icon(categoryIcon)}</span><span class="trial-text"><span class="trial-title">${escapeHTML(c.title)}</span><span class="trial-meta"><span>${escapeHTML(c.category)}</span><span class="dot"></span><span>${escapeHTML(c.pressure || "Custom trial")}</span>${c.origin === "custom" ? tag("Edited") : ""}</span></span></button><div class="trial-end ${result?.status || ""}">${result ? `${icon(icons[result.status])}<span>${result.status === "pending" ? "Queued" : result.status[0].toUpperCase() + result.status.slice(1)}</span>` : `<span class="assertion-count">${c.checks.length} check${c.checks.length === 1 ? "" : "s"}</span>${icon("chevron-right")}`}</div></div>`;
          })
          .join("")
      : '<div class="empty">No trials match these filters.</div>');
  if ($("#selection-count"))
    $("#selection-count").textContent = `${state.selected.size} selected`;
  if ($("#run-button")) {
    $("#run-button").disabled = !state.selected.size || !!state.active;
    $("#run-button").innerHTML =
      `${icon("play")}Run ${state.selected.size} trial${state.selected.size === 1 ? "" : "s"}`;
  }
}

function modelPanel() {
  return `<section class="run-setup" aria-label="Run configuration"><div class="panel-body"><div class="source-control"><span class="control-label">Source</span><div class="segmented" aria-label="Model source"><button data-action="mode" data-mode="demo" aria-pressed="${state.mode === "demo"}" class="${state.mode === "demo" ? "active" : ""}">${icon("flask-conical")}Demo fixtures</button><button data-action="mode" data-mode="endpoint" aria-pressed="${state.mode === "endpoint"}" class="${state.mode === "endpoint" ? "active" : ""}">${icon("cpu")}Model endpoint</button></div></div>
    ${state.mode === "demo" ? `<label class="field model-field"><span>Model profile</span><select id="profile"><option value="candidate" ${state.profile === "candidate" ? "selected" : ""}>Candidate / more resilient</option><option value="baseline" ${state.profile === "baseline" ? "selected" : ""}>Baseline / failure-prone</option></select></label>` : `<div class="field model-field"><span>Connected model</span><a href="#settings" class="model-link">${icon("cpu")}<strong>${escapeHTML(state.settings.model || "Configure a model")}</strong>${icon("arrow-up-right")}</a></div>`}
    <div class="run-action"><button class="btn primary run-button" id="run-button" data-action="run" ${!state.selected.size || state.active ? "disabled" : ""}>${icon("play")}Run ${state.selected.size} trials</button></div></div><div class="panel-foot"><span>${icon(state.mode === "demo" ? "flask-conical" : "shield-check")}${state.mode === "demo" ? "Demo mode. Synthetic responses, no model calls." : state.settings.allow_remote ? "Prompts will be sent to the configured remote endpoint." : "Prompts will be sent to the configured local endpoint."}</span><span>Results saved locally</span></div></section>`;
}

function detail(resultOverride = null, scope = "inspector") {
  const result =
    resultOverride ||
    state.current?.results.find((r) => r.case_id === state.focus);
  const c =
    result?.case ||
    state.cases.find((c) => c.id === state.focus) ||
    state.cases[0];
  if (!c) return "";
  const tab =
    state.detailTab === "result" && !result ? "prompt" : state.detailTab;
  const checks = (result?.checks.length ? result.checks : c.checks)
    .map(
      (check) =>
        `<div class="check-item ${check.passed === false ? "failed" : ""}"><div class="check-heading">${icon(check.passed === false ? "circle-x" : "circle-check")}<strong>${{ exact: "Exact match", contains: "Contains", not_contains: "Does not contain", json_equals: "JSON equality" }[check.type]}</strong>${check.passed !== undefined ? tag(check.passed ? "Passed" : "Failed", check.passed ? "green" : "red") : tag("Required")}</div><span class="label">EXPECTED VALUE</span><pre class="code expected">${escapeHTML(check.expected)}</pre>${check.detail ? `<small>${escapeHTML(check.detail)}</small>` : ""}</div>`,
    )
    .join("");
  return `<section class="detail"><div class="inspector-label"><span>${icon("flask-conical")}${result ? "Result evidence" : "Trial inspector"}</span>${iconButton("Edit trial", "edit-trial", "pencil", `data-id="${c.id}"`)}</div><div class="detail-title"><div class="trial-id">${escapeHTML(c.id.toUpperCase())}</div><h3>${escapeHTML(c.title)}</h3><div class="detail-tags">${tag(c.category)}${result ? tag(result.status, result.status === "passed" ? "green" : result.status === "failed" ? "red" : "") : tag(c.pressure || "Custom trial")}</div></div><div class="detail-tabs" role="tablist" aria-label="Trial details">${[
    ["prompt", "Prompt"],
    ["assertions", "Assertions"],
    ["result", "Result"],
  ]
    .map(
      ([key, label]) =>
        `<button role="tab" id="${scope}-${key}-tab" aria-controls="${scope}-panel" tabindex="${tab === key ? 0 : -1}" aria-selected="${tab === key}" data-action="detail-tab" data-tab="${key}" class="${tab === key ? "active" : ""}" ${key === "result" && !result ? "disabled" : ""}>${label}${key === "assertions" ? `<span>${c.checks.length}</span>` : ""}</button>`,
    )
    .join(
      "",
    )}</div><div class="detail-content" role="tabpanel" id="${scope}-panel" aria-labelledby="${scope}-${tab}-tab" tabindex="0">${tab === "prompt" ? `<span class="label">SYSTEM INSTRUCTION</span><pre class="code">${escapeHTML(c.system || "(none)")}</pre><span class="label">USER PROMPT</span><pre class="code">${escapeHTML(c.prompt)}</pre><div class="inspector-foot">${icon("shield-check")}Evaluated against ${c.checks.length} explicit assertion${c.checks.length === 1 ? "" : "s"}.</div>` : tab === "assertions" ? checks : `${result?.response !== null ? `<span class="label">OBSERVED RESPONSE</span><pre class="code response">${escapeHTML(result?.response)}</pre>` : ""}${result?.error ? `<div class="inline-alert">${escapeHTML(result.error)}</div>` : ""}${checks}<p class="model-note">${result?.latency_ms === null ? "Synthetic response. No model latency recorded." : `Response time: ${result?.latency_ms} ms.`}</p>`}</div></section>`;
}

function renderLibrary() {
  return `${heading("Trial library", "A repeatable set of pressures. Your criteria, visible.", btn("New trial", "new-trial", "plus"))}<div class="bench-layout"><section class="bench-main">${trialFilters()}<div id="trial-list"></div><div class="list-note"><span id="selection-count"></span>${btn("Run selected", "to-bench", "play")}</div></section><aside class="bench-aside"><div id="detail-region">${detail()}</div></aside></div>`;
}

function renderHistory() {
  return `${heading("Run history", "Every response, every check, kept on this machine.", btn("New run", "to-bench", "play"))}${state.runs.length ? `<div class="table-wrap"><table class="data-table"><thead><tr><th>MODEL / RUN</th><th>STATUS</th><th>PASSED</th><th>FAILED</th><th>ERRORS</th><th></th></tr></thead><tbody>${state.runs.map((run) => `<tr><td><strong>${escapeHTML(run.model)}</strong><span class="sub">${date(run.started_at)} &middot; ${run.id.slice(-6)}</span></td><td>${tag(run.status, run.status === "completed" ? "green" : "")}<span class="sub">${run.mode === "demo" ? "Synthetic fixture" : "Model endpoint"}</span></td><td class="mono improved">${run.passed} / ${run.total}</td><td class="mono">${run.failed}</td><td class="mono">${run.errors}</td><td>${iconButton("Open run", "open-run", "arrow-up-right", `data-id="${run.id}"`)}</td></tr>`).join("")}</tbody></table></div>` : empty("No runs yet", "Your first run will appear here with its prompts, responses, and check results.", btn("Open test bench", "to-bench", "arrow-right"), "history")}`;
}

function renderCompare() {
  const completed = state.runs.filter((run) => run.status === "completed");
  if (completed.length < 2)
    return `${heading("Compare runs", "Same trials. Different models. Inspect what changed.")}${empty("Two completed runs make a comparison", "Run both demo profiles, or compare two models against the same trials.", btn("Open test bench", "to-bench", "arrow-right"), "git-compare-arrows")}`;
  if (
    !state.compare.length ||
    state.compare.some((id) => !completed.some((r) => r.id === id))
  )
    state.compare = [completed[1].id, completed[0].id];
  const select = (index, label) =>
    `<label class="field"><span>${label}</span><select data-compare="${index}">${completed.map((run) => `<option value="${run.id}" ${state.compare[index] === run.id ? "selected" : ""}>${escapeHTML(run.model)} / ${date(run.started_at)} / ${run.id.slice(-4)}</option>`).join("")}</select></label>`;
  return `${heading("Compare runs", "Same trials. Different models. Inspect what changed.")}<div class="compare-controls">${select(0, "BASELINE")}${icon("git-compare-arrows")}${select(1, "CANDIDATE")}</div><div id="comparison">Loading comparison...</div>`;
}

async function loadComparison() {
  if (!$("#comparison")) return;
  const selection = [...state.compare];
  try {
    const a = await api(`runs/${selection[0]}`),
      b = await api(`runs/${selection[1]}`);
    if (!$("#comparison") || selection.join() !== state.compare.join()) return;
    if (a.id === b.id) {
      $("#comparison").innerHTML = empty(
        "Select two different runs",
        "A run cannot be compared with itself.",
      );
      return;
    }
    let improved = 0,
      regressed = 0,
      matched = 0;
    const ids = [
      ...new Set([...a.results, ...b.results].map((r) => r.case_id)),
    ];
    const rows = ids
      .map((id) => {
        const ar = a.results.find((r) => r.case_id === id),
          br = b.results.find((r) => r.case_id === id);
        const compatible =
          ar &&
          br &&
          ar.fingerprint === br.fingerprint &&
          ["passed", "failed"].includes(ar.status) &&
          ["passed", "failed"].includes(br.status);
        let delta = "Not comparable",
          cls = "muted";
        if (compatible) {
          matched++;
          delta = "Unchanged";
          if (ar.status !== br.status) {
            if (br.status === "passed") {
              improved++;
              delta = "Improved";
              cls = "improved";
            } else {
              regressed++;
              delta = "Regressed";
              cls = "regressed";
            }
          }
        }
        return `<tr><td>${escapeHTML((ar || br).title)}</td><td>${tag(ar?.status || "Not run", ar?.status === "passed" ? "green" : ar?.status === "failed" ? "red" : "")}</td><td>${tag(br?.status || "Not run", br?.status === "passed" ? "green" : br?.status === "failed" ? "red" : "")}</td><td class="${cls}">${delta}</td></tr>`;
      })
      .join("");
    $("#comparison").innerHTML =
      `<div class="notice">${a.mode !== b.mode ? "Mixed demo and model results: this is not a model-performance comparison. " : a.mode === "demo" ? "Synthetic demo comparison. No models were called. " : ""}${matched} unchanged trial definitions compared. <strong>${improved} improved</strong>, <strong>${regressed} regressed</strong>. Errors, skipped trials, and changed definitions are not compared.</div><div class="table-wrap"><table class="data-table"><thead><tr><th>TRIAL</th><th>BASELINE</th><th>CANDIDATE</th><th>CHANGE</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  } catch (error) {
    toast(error.message, true);
  }
}

function renderSettings() {
  const config = state.settings;
  return `${heading("Model connection", "Your endpoint. Your model. Your evidence.")}<div class="settings-grid"><form id="settings-form" class="settings-form"><h2>OpenAI-compatible endpoint</h2><p class="model-note">No model calls are made when saving this connection.</p><label class="field"><span>Base URL</span><input name="base_url" type="url" value="${escapeHTML(config.base_url)}" required maxlength="2000" placeholder="http://localhost:11434/v1"></label><label class="field"><span>Model identifier</span><input name="model" value="${escapeHTML(config.model)}" required maxlength="160" placeholder="Exact model name on your server"></label><div class="field"><span>API key</span>${tag(state.key_available ? "Available in server environment" : "Not set / optional for local servers", state.key_available ? "green" : "")}<small>FORGEBENCH_LAB_API_KEY &middot; Never stored in the browser or run history.</small></div><label class="checkbox-label"><input name="allow_remote" type="checkbox" ${config.allow_remote ? "checked" : ""}><span>I allow trial prompts to be sent to this remote HTTPS endpoint. Provider usage may incur charges.</span></label><div id="settings-error"></div><button class="btn primary" type="submit">${icon("check")}Save connection</button></form><aside class="settings-aside"><h3>Local by default</h3><p>Demo runs use bundled fixtures and make no model calls. Local endpoints keep requests on your machine. Remote endpoints receive only the trial prompts when a run is started.</p><h3>What is measured</h3><p>Explicit, deterministic assertions against model responses. A passing check is evidence about one condition, not proof of general correctness or safety.</p><h3>Request limits</h3><p>One trial at a time. Temperature 0. Up to 512 output tokens. A 45-second timeout. Stopping a run prevents new requests; an in-flight request may finish.</p></aside></div>`;
}

function openEditor(id) {
  const c = state.cases.find((c) => c.id === id) || {
    title: "",
    category: "Instructions",
    pressure: "",
    system: "",
    prompt: "",
    checks: [{ type: "exact", expected: "" }],
  };
  const dialog = $("#trial-dialog");
  dialog.innerHTML = `<form id="trial-form" data-id="${c.id || ""}"><div class="dialog-head"><h2 id="dialog-title">${c.id ? "Edit trial" : "New trial"}</h2>${iconButton("Close", "close-dialog", "x")}</div><div class="dialog-body"><label class="field"><span>Trial name</span><input name="title" required maxlength="120" value="${escapeHTML(c.title)}"></label><div class="dialog-grid"><label class="field"><span>Category</span><select name="category">${state.categories.map((cat) => `<option ${cat === c.category ? "selected" : ""}>${cat}</option>`).join("")}</select></label><label class="field"><span>Pressure</span><input name="pressure" maxlength="120" value="${escapeHTML(c.pressure)}" placeholder="e.g. Missing evidence"></label></div><label class="field"><span>System instruction</span><textarea name="system" maxlength="8000">${escapeHTML(c.system)}</textarea></label><label class="field"><span>User prompt</span><textarea name="prompt" maxlength="16000" required>${escapeHTML(c.prompt)}</textarea></label><label class="field"><span>Assertion</span><select name="check">${["exact", "contains", "not_contains", "json_equals"].map((type) => `<option value="${type}" ${type === c.checks[0].type ? "selected" : ""}>${{ exact: "Exact match", contains: "Contains", not_contains: "Does not contain", json_equals: "JSON equality" }[type]}</option>`).join("")}</select></label><label class="field"><span>Expected value</span><textarea name="expected" maxlength="8000" required>${escapeHTML(c.checks[0].expected)}</textarea></label><p class="model-note">Custom and edited trials require a model endpoint; demo responses are not invented for them.</p><div id="trial-error"></div></div><div class="dialog-actions">${c.origin === "custom" ? btn(c.id.startsWith("custom-") ? "Delete trial" : "Restore bundled trial", "delete-trial", "trash-2", "danger", `data-id="${c.id}" type="button"`) : "<span></span>"}<button type="submit" class="btn primary">${icon("check")}Save trial</button></div></form>`;
  if (!dialog.open) dialog.showModal();
  $("input[name=title]", dialog).focus();
}

async function startRun() {
  if (state.mode === "endpoint" && !state.settings.model) {
    location.hash = "settings";
    toast("Connect a model before starting a real run.");
    return;
  }
  const runButton = $("#run-button");
  if (runButton) runButton.disabled = true;
  try {
    state.current = await api("runs", {
      mode: state.mode,
      profile: state.profile,
      case_ids: [...state.selected],
    });
    state.active = state.current.id;
    state.resultFilter = "all";
    state.focus = state.current.results[0].case_id;
    render();
    toast(
      state.mode === "demo"
        ? "Demo started. Synthetic responses, no model calls."
        : "Model run started.",
    );
  } catch (error) {
    toast(error.message, true);
    if (runButton) runButton.disabled = false;
  }
}

async function poll() {
  if (!state.active || polling) return;
  polling = true;
  try {
    const run = await api(`runs/${state.active}`);
    state.current = run;
    if (run.status !== "running") {
      await refresh();
      toast(
        `Run ${run.status}: ${run.passed} passed, ${run.failed} failed, ${run.errors} errors.`,
      );
      if (state.view !== "settings") render();
    } else if (state.view === "bench") {
      $("#stats-region").innerHTML = stats();
      $("#run-region").innerHTML = runStrip();
      renderTrials();
      $("#detail-region").innerHTML = detail();
    }
  } catch (error) {
    toast("Connection lost. Runs stay on the server; reconnecting...", true);
  } finally {
    polling = false;
  }
}

document.addEventListener("click", async (event) => {
  const el = event.target.closest("[data-action]");
  if (!el) return;
  event.preventDefault();
  try {
    switch (el.dataset.action) {
      case "run":
        await startRun();
        break;
      case "cancel":
        await api(`runs/${state.active}/cancel`, {});
        toast("Stopping after the in-flight request.");
        break;
      case "new-trial":
        openEditor();
        break;
      case "edit-trial":
        openEditor(el.dataset.id);
        break;
      case "close-dialog":
        $("#trial-dialog").close();
        break;
      case "category":
        state.category = el.dataset.category;
        render();
        break;
      case "result-filter":
        state.resultFilter = el.dataset.filter;
        render();
        break;
      case "mode":
        state.mode = el.dataset.mode;
        render();
        break;
      case "to-bench":
        location.hash = "bench";
        break;
      case "inspect":
        state.focus = el.dataset.id;
        state.detailTab = state.current?.results.find(
          (r) => r.case_id === state.focus,
        )
          ? "result"
          : "prompt";
        renderTrials();
        $("#detail-region").innerHTML = detail();
        if (matchMedia("(max-width:760px)").matches) {
          const dialog = $("#trial-dialog");
          dialog.innerHTML = `<div class="dialog-head"><h2 id="dialog-title">Trial evidence</h2>${iconButton("Close", "close-dialog", "x")}</div><div class="dialog-body">${detail(null, "dialog")}</div>`;
          dialog.showModal();
        }
        break;
      case "detail-tab":
        state.detailTab = el.dataset.tab;
        $("#detail-region").innerHTML = detail();
        if ($("#trial-dialog").open && !$("#trial-form"))
          $("#trial-dialog .dialog-body").innerHTML = detail(null, "dialog");
        ($("#trial-dialog").open ? $("#trial-dialog") : $("#detail-region"))
          .querySelector(`[data-tab="${state.detailTab}"]`)
          ?.focus();
        break;
      case "clear-run":
        state.current = null;
        state.resultFilter = "all";
        render();
        break;
      case "export":
        window.location.href = `/api/runs/${state.current.id}/export`;
        break;
      case "open-run":
        state.current = await api(`runs/${el.dataset.id}`);
        state.focus = state.current.results[0]?.case_id;
        state.resultFilter = "all";
        location.hash = "bench";
        if (state.view === "bench") render();
        break;
      case "delete-trial":
        if (
          !confirm(
            "Remove this local trial edit? Bundled trials will return to their original definition.",
          )
        )
          break;
        await api("cases/delete", { id: el.dataset.id });
        $("#trial-dialog").close();
        await refresh();
        state.selected.delete(el.dataset.id);
        render();
        toast("Local trial edit removed.");
        break;
    }
  } catch (error) {
    toast(error.message, true);
  }
});

document.addEventListener("input", (event) => {
  if (event.target.id === "trial-search") {
    state.query = event.target.value;
    renderTrials();
  }
});
document.addEventListener("keydown", (event) => {
  if (!event.target.matches('.detail-tabs [role="tab"]')) return;
  if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
  event.preventDefault();
  const tabs = [
    ...event.target.parentElement.querySelectorAll("button:not(:disabled)"),
  ];
  const index = tabs.indexOf(event.target);
  const next =
    event.key === "Home"
      ? 0
      : event.key === "End"
        ? tabs.length - 1
        : (index + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) %
          tabs.length;
  const selectedTab = tabs[next].dataset.tab;
  tabs[next].click();
  const root = $("#trial-dialog").open
    ? $("#trial-dialog")
    : $("#detail-region");
  root.querySelector(`[data-tab="${selectedTab}"]`)?.focus();
});
document.addEventListener("change", (event) => {
  const el = event.target;
  if (el.dataset.select) {
    el.checked
      ? state.selected.add(el.dataset.select)
      : state.selected.delete(el.dataset.select);
    renderTrials();
  }
  if (el.id === "select-all") {
    visibleTrials().forEach((c) =>
      el.checked ? state.selected.add(c.id) : state.selected.delete(c.id),
    );
    renderTrials();
  }
  if (el.id === "profile") state.profile = el.value;
  if (el.dataset.compare !== undefined) {
    state.compare[Number(el.dataset.compare)] = el.value;
    loadComparison();
  }
});
document.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const data = new FormData(form);
  try {
    if (form.id === "settings-form") {
      state.settings = await api("settings", {
        base_url: data.get("base_url"),
        model: data.get("model"),
        allow_remote: data.get("allow_remote") === "on",
      });
      state.mode = "endpoint";
      toast("Connection saved. No model call made.");
      location.hash = "bench";
    }
    if (form.id === "trial-form") {
      const remainingChecks =
        state.cases.find((c) => c.id === form.dataset.id)?.checks.slice(1) ||
        [];
      const trial = await api("cases", {
        id: form.dataset.id || undefined,
        title: data.get("title"),
        category: data.get("category"),
        pressure: data.get("pressure"),
        system: data.get("system"),
        prompt: data.get("prompt"),
        checks: [
          { type: data.get("check"), expected: data.get("expected") },
          ...remainingChecks,
        ],
      });
      $("#trial-dialog").close();
      await refresh();
      state.focus = trial.id;
      state.selected.add(trial.id);
      if (!state.active) {
        state.current = null;
        state.resultFilter = "all";
      }
      state.query = "";
      state.category = "All trials";
      render();
      toast("Trial saved locally.");
    }
  } catch (error) {
    const target =
      form.id === "settings-form" ? $("#settings-error") : $("#trial-error");
    if (target)
      target.innerHTML = `<div class="inline-alert">${escapeHTML(error.message)}</div>`;
    else toast(error.message, true);
  }
});

function route() {
  state.view = ["bench", "library", "history", "compare", "settings"].includes(
    location.hash.slice(1),
  )
    ? location.hash.slice(1)
    : "bench";
  render();
}
window.addEventListener("hashchange", route);
async function boot() {
  try {
    await refresh();
    state.selected = new Set(state.cases.map((c) => c.id));
    state.focus = state.cases[0]?.id;
    if (state.active) state.current = await api(`runs/${state.active}`);
    route();
    setInterval(poll, 650);
  } catch (error) {
    $("#main").innerHTML = empty(
      "The local bench is unavailable",
      escapeHTML(error.message),
      btn("Retry", "reload", "rotate-ccw"),
    );
    $("[data-action=reload]").addEventListener("click", boot);
  }
}
boot();
