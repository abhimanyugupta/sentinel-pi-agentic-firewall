"use strict";

const $ = (selector) => document.querySelector(selector);
let selectedEventId = null;

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Request failed (" + response.status + ")");
  return payload;
}

function toast(message, error = false) {
  const node = $("#toast");
  node.textContent = message;
  node.classList.toggle("error", error);
  node.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => node.classList.remove("show"), 3200);
}

function label(value) {
  return String(value || "").replaceAll("_", " ");
}

function renderHighlight(target, text, spans) {
  target.replaceChildren();
  const valid = (spans || [])
    .filter((span) => Number.isInteger(span.start) && Number.isInteger(span.end) && span.start >= 0 && span.end > span.start && span.end <= text.length)
    .sort((a, b) => a.start - b.start || b.end - a.end);
  let cursor = 0;
  for (const span of valid) {
    if (span.start < cursor) continue;
    target.append(document.createTextNode(text.slice(cursor, span.start)));
    const mark = document.createElement("mark");
    mark.className = "suspicious";
    mark.title = label(span.attack_type);
    mark.textContent = text.slice(span.start, span.end);
    target.append(mark);
    cursor = span.end;
  }
  target.append(document.createTextNode(text.slice(cursor)));
}

function renderEvents(events) {
  const list = $("#eventList");
  list.replaceChildren();
  $("#eventCount").textContent = String(events.length);
  for (const event of events) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "event-button" + (selectedEventId === event.run_id ? " selected" : "");
    const top = document.createElement("div");
    top.className = "event-top";
    const name = document.createElement("span");
    name.className = "event-name";
    name.textContent = event.title;
    const kind = document.createElement("span");
    kind.className = "event-kind";
    kind.textContent = event.source.source_type.toUpperCase();
    top.append(name, kind);
    const summary = document.createElement("div");
    summary.className = "event-summary";
    summary.textContent = event.source.content;
    const state = document.createElement("div");
    state.className = "event-state" + (event.protected.unauthorized_email_executed ? " blocked" : "");
    const dot = document.createElement("i");
    dot.className = "state-dot";
    const text = document.createElement("span");
    text.textContent = event.protected.unauthorized_email_executed
      ? "UNAUTHORIZED ACTION EXECUTED"
      : event.firewall.action.toUpperCase() + " · GATE ACTIVE";
    state.append(dot, text);
    button.append(top, summary, state);
    button.addEventListener("click", () => {
      selectedEventId = event.run_id;
      renderEvents(events);
      renderEvent(event);
    });
    list.append(button);
  }
}

function renderEvent(event) {
  if (!event) return;
  const decision = event.firewall;
  const provenance = decision.provenance;
  $("#sourceType").textContent = event.source.source_type;
  $("#sourceId").textContent = event.source.source_id;
  $("#trustState").textContent = event.source.trusted ? "TRUSTED SOURCE" : "LOWER TRUST";
  renderHighlight($("#sourceContent"), event.source.content, decision.suspicious_spans);
  $("#spanCount").textContent = decision.suspicious_spans.length + " finding" + (decision.suspicious_spans.length === 1 ? "" : "s");
  $("#contentHash").textContent = provenance.content_sha256;
  $("#actionBadge").textContent = decision.action.toUpperCase();
  $("#actionBadge").className = "action-badge action-" + decision.action;
  $("#riskScore").textContent = Number(decision.risk_score).toFixed(2);
  $("#riskFill").style.width = Math.max(0, Math.min(100, Number(decision.risk_score) * 100)) + "%";
  const categories = $("#categoryList");
  categories.replaceChildren();
  if (!decision.attack_types.length) {
    const empty = document.createElement("span");
    empty.className = "category-empty";
    empty.textContent = "No indicator matched";
    categories.append(empty);
  } else {
    decision.attack_types.forEach((item) => {
      const chip = document.createElement("span");
      chip.className = "category-chip";
      chip.textContent = label(item);
      categories.append(chip);
    });
  }
  const reasons = $("#rationaleList");
  reasons.replaceChildren();
  decision.rationale.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    reasons.append(li);
  });
  $("#provenanceSource").textContent = provenance.source_type + " · " + provenance.source_id;
  $("#provenanceTrust").textContent = provenance.trusted ? "trusted" : "lower trust";
  $("#provenanceDecoded").textContent = String(provenance.decoded_payloads);

  const baseline = event.baseline;
  const protectedRun = event.protected;
  $("#baselineStatus").textContent = baseline.unauthorized_email_executed
    ? "UNAUTHORIZED EMAIL SIDE EFFECT OCCURRED"
    : "No unauthorized action executed";
  const gateDenied = protectedRun.gate_decisions.some((gate) => gate.outcome === "deny");
  $("#protectedStatus").textContent = protectedRun.unauthorized_email_executed
    ? "UNAUTHORIZED EMAIL SIDE EFFECT OCCURRED"
    : protectedRun.external_instruction_suppressed_by_firewall
      ? "CONTENT WITHHELD BY FIREWALL · " + protectedRun.gate_violations + " GATE VIOLATIONS"
      : gateDenied
        ? "ACTION DENIED BY INTENT GATE · " + protectedRun.gate_violations + " GATE VIOLATIONS"
        : "NO UNAUTHORIZED ACTION · " + protectedRun.gate_violations + " GATE VIOLATIONS";
  $("#simulationNote").textContent = "Agent trace: " + event.agent_simulation.label
    + " · live model used: no · output guard input: " + protectedRun.answer_guard_input_label;
  renderCalls($("#baselineCalls"), baseline.proposed_calls, baseline.gate_decisions);
  renderCalls($("#protectedCalls"), protectedRun.proposed_calls, protectedRun.gate_decisions);
  $("#baselineAnswer").textContent = "Baseline answer: " + baseline.answer;
  $("#baselineAnswer").className = "answer-box" + (baseline.answer_leaked_canary ? " leaked" : "");
  const outputFindings = protectedRun.answer_guard.findings || [];
  const claimFindings = outputFindings.filter((item) => item.startsWith("unverified_claim_")).length;
  const canaryFindings = outputFindings.filter((item) => item.startsWith("synthetic_canary_")).length;
  const findingSummary = outputFindings.length
    ? " · Guard redacted " + claimFindings + " unsupported claim(s), " + canaryFindings + " canary(s)"
    : " · No output findings";
  $("#protectedAnswer").textContent = "Protected answer: " + protectedRun.answer + findingSummary;
  $("#protectedAnswer").className = "answer-box" + (outputFindings.length ? " safe" : "");
  $("#intentText").textContent = event.intent.task;
  $("#allowedTools").textContent = event.intent.permitted_tools.join(" · ");
}

function renderCalls(target, calls, gates) {
  target.replaceChildren();
  calls.forEach((call, index) => {
    const row = document.createElement("div");
    row.className = "call-row";
    const tool = document.createElement("span");
    tool.className = "call-tool";
    tool.textContent = call.tool;
    const result = document.createElement("span");
    const gate = gates[index];
    result.className = "call-result" + (gate && gate.outcome !== "allow" && gate.outcome !== "bypassed" ? " denied" : "");
    result.textContent = gate
      ? gate.outcome.toUpperCase() + " · " + gate.reason
      : "No tool gate in the baseline path";
    row.append(tool, result);
    target.append(row);
  });
}

function renderMetrics(state) {
  const metrics = state.metrics;
  $("#metricScanned").textContent = String(metrics.total_cases);
  $("#metricBlocked").textContent = metrics.attacks_quarantined_or_blocked + "/" + metrics.attack_cases;
  $("#metricBlockedFoot").textContent = (metrics.attack_case_detection_rate * 100).toFixed(1)
    + "% case detection · " + (metrics.category_micro_precision * 100).toFixed(1) + "% label precision";
  const eventGateDenials = state.events.reduce((sum, event) => sum + event.protected.gate_decisions.filter((gate) => gate.outcome !== "allow" && gate.outcome !== "bypassed").length, 0);
  const invariantDenials = metrics.independent_gate_external_provenance_denials || 0;
  const gated = eventGateDenials + invariantDenials;
  $("#metricGated").textContent = String(gated);
  $("#metricGatedFoot").textContent = invariantDenials + " fixed external-provenance check(s)";
  const latency = $("#metricLatency");
  latency.replaceChildren(document.createTextNode(Number(metrics.median_latency_ms).toFixed(2)));
  const unit = document.createElement("small");
  unit.textContent = " ms";
  latency.append(unit);
  $("#metricP95").textContent = "p95 " + Number(metrics.p95_latency_ms).toFixed(2) + " ms";

  const coverage = Object.entries(metrics.per_category);
  const detected = coverage.filter(([, value]) => value.detected === value.cases).length;
  $("#coverageBadge").textContent = detected + " / 9 categories";
  const grid = $("#coverageGrid");
  grid.replaceChildren();
  const all = [
    "instruction_override", "role_change", "secret_extraction", "tool_abuse",
    "credential_theft", "context_poisoning", "multi_step_jailbreak",
    "encoded_instructions", "indirect_prompt_injection",
  ];
  for (const category of all) {
    const value = metrics.per_category[category];
    const item = document.createElement("div");
    item.className = "coverage-item" + (!value || value.detected !== value.cases ? " missing" : "");
    const name = document.createElement("strong");
    name.textContent = label(category);
    const stat = document.createElement("span");
    stat.textContent = value
      ? value.detected + "/" + value.cases + " detected" + (value.false_positive_labels ? " · " + value.false_positive_labels + " extra" : "")
      : "not in corpus";
    item.append(name, stat);
    grid.append(item);
  }
}

function renderPolicy(policy) {
  const active = policy.active_policy;
  $("#policyVersion").textContent = active.policy_id.replace("policy-", "");
  $("#policyHistory").textContent = policy.versions.length + " version" + (policy.versions.length === 1 ? "" : "s") + " recorded";
  const rollbackAvailable = Boolean(policy.rollback_available);
  $("#rollbackButton").disabled = !rollbackAvailable;
  $("#rollbackButton").style.opacity = rollbackAvailable ? "1" : ".45";
}

function renderState(state) {
  renderMetrics(state);
  renderPolicy(state.policy);
  const events = state.events;
  if (!events.some((event) => event.run_id === selectedEventId)) {
    const preferred = events.find((event) => event.scenario_id === "indirect_injection");
    selectedEventId = (preferred || events[0] || {}).run_id || null;
  }
  renderEvents(events);
  renderEvent(events.find((event) => event.run_id === selectedEventId));
  const select = $("#scenarioSelect");
  if (!select.options.length) {
    state.scenarios.forEach((scenario) => {
      const option = document.createElement("option");
      option.value = scenario.id;
      option.textContent = scenario.title;
      select.append(option);
    });
    select.value = "indirect_injection";
  }
}

async function refresh() {
  renderState(await api("/api/state"));
}

$("#replayButton").addEventListener("click", async () => {
  try {
    $("#replayButton").disabled = true;
    const payload = await api("/api/replay", { method: "POST", body: JSON.stringify({ scenario_id: $("#scenarioSelect").value }) });
    selectedEventId = payload.event.run_id;
    renderState(payload.state);
    toast("Scenario replay completed from local fixtures.");
  } catch (error) { toast(error.message, true); }
  finally { $("#replayButton").disabled = false; }
});

$("#evaluateButton").addEventListener("click", async () => {
  try {
    const payload = await api("/api/evaluate", { method: "POST", body: "{}" });
    renderState(payload.state);
    toast("Evaluation " + payload.evaluation.evaluation_id + " completed.");
  } catch (error) { toast(error.message, true); }
});

$("#candidateForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const phrase = $("#literalIndicator").value.trim();
  const category = $("#blockCategory").value;
  const proposal = {
    name: phrase ? "Literal indicator proposal" : "Escalate " + label(category),
    add_block_categories: phrase ? [] : [category],
    add_literal_indicators: phrase ? [{ phrase, attack_type: category }] : [],
  };
  try {
    const payload = await api("/api/policy/candidate", { method: "POST", body: JSON.stringify(proposal) });
    renderState(payload.state);
    const box = $("#candidateResult");
    box.hidden = false;
    box.className = "candidate-result" + (payload.candidate.accepted ? "" : " reject");
    const title = document.createElement("strong");
    const hardeningOnly = payload.candidate.candidate_classification === "policy_hardening_only";
    title.textContent = payload.candidate.accepted
      ? hardeningOnly ? "Accepted for severity hardening" : "Candidate accepted after evaluation"
      : "Candidate rejected";
    const text = document.createElement("span");
    const comparison = payload.candidate.policy_comparison || {};
    const endToEnd = payload.candidate.end_to_end || {};
    const baselineEffects = endToEnd.baseline?.protected_unauthorized_side_effects;
    const candidateEffects = endToEnd.candidate?.protected_unauthorized_side_effects;
    text.textContent = payload.candidate.reason || (hardeningOnly
      ? `Policy hardening only: ${comparison.severity_only_reclassified_cases?.length || 0} attack fixture(s) changed from quarantine to block; ${comparison.newly_contained_cases?.length || 0} newly contained. Protected unauthorized side effects: ${baselineEffects ?? "?"} before, ${candidateEffects ?? "?"} after.`
      : "Candidate passed regression checks; inspect the recorded containment, severity, task, and side-effect comparisons.");
    box.replaceChildren(title, text);
    toast(payload.candidate.accepted ? "Candidate passed its regression checks." : "Candidate did not pass its regression checks.", !payload.candidate.accepted);
  } catch (error) { toast(error.message, true); }
});

$("#rollbackButton").addEventListener("click", async () => {
  try {
    const payload = await api("/api/policy/rollback", { method: "POST", body: "{}" });
    renderState(payload.state);
    toast(payload.rollback.rolled_back ? "Previous policy restored; history preserved." : payload.rollback.reason, !payload.rollback.rolled_back);
  } catch (error) { toast(error.message, true); }
});

refresh().catch((error) => {
  toast("Local API unavailable: " + error.message, true);
});
