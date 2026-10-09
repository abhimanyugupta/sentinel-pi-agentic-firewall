"use strict";

(() => {
  const data = window.SENTINEL_PI_DEMO_DATA;
  if (!data || data.schema_version !== 1) {
    document.body.textContent = "The precomputed demo snapshot is missing or has an unsupported version.";
    return;
  }

  const byId = (id) => document.getElementById(id);
  const text = (node, value) => { node.textContent = value == null ? "" : String(value); };
  const percent = (value) => `${(Number(value) * 100).toFixed(2)}%`;
  const list = (items, renderItem) => {
    const ul = document.createElement("ul");
    ul.className = "trace-list";
    if (!items || items.length === 0) {
      const li = document.createElement("li");
      li.textContent = "None recorded";
      ul.appendChild(li);
      return ul;
    }
    for (const item of items) {
      const li = document.createElement("li");
      li.textContent = renderItem(item);
      ul.appendChild(li);
    }
    return ul;
  };
  const block = (title, content) => {
    const section = document.createElement("section");
    section.className = "trace-block";
    const heading = document.createElement("h4");
    heading.textContent = title;
    section.appendChild(heading);
    section.appendChild(content);
    return section;
  };

  function renderMetrics() {
    const metrics = data.evaluation.metrics;
    const configuredTypes = data.evaluation.configured_attack_types || [];
    const observedTypes = configuredTypes.filter((type) => metrics.per_category?.[type]?.cases > 0);
    const cards = [
      [metrics.total_cases, `classifier cases · ${metrics.attack_cases} attack / ${metrics.benign_cases} benign`],
      [`${observedTypes.length} / ${configuredTypes.length}`, "configured attack types observed in fixtures"],
      [percent(metrics.category_micro_precision), "category micro-precision"],
      [percent(metrics.category_micro_recall), "category micro-recall"],
      [`${metrics.benign_cases - metrics.benign_false_positives} / ${metrics.benign_cases}`, "benign controls passed"]
    ];
    const grid = byId("metric-grid");
    for (const [value, label] of cards) {
      const card = document.createElement("article");
      card.className = "metric-card";
      const number = document.createElement("span");
      number.className = "metric-value";
      number.textContent = String(value);
      const caption = document.createElement("span");
      caption.className = "metric-label";
      caption.textContent = label;
      card.append(number, caption);
      grid.appendChild(card);
    }
    const f1 = percent(metrics.category_micro_f1);
    const predictedLabels = data.evaluation.raw_predictions.reduce(
      (count, record) => count + (record.predicted_attack_types || []).length,
      0
    );
    text(byId("evaluation-footnote"),
      `${metrics.expected_category_hits} / ${metrics.expected_category_labels} expected labels matched; ` +
      `${predictedLabels} predicted labels include ${metrics.category_false_positive_labels} extra labels; ` +
      `micro-F1 ${f1}. Benign false positives: ${metrics.benign_false_positives} / ${metrics.benign_cases}. ` +
      `Firewall action containment: ${metrics.attacks_quarantined_or_blocked} / ${metrics.attack_cases} attack fixtures were blocked or quarantined; ` +
      `protected unauthorized side effects: ${metrics.protected_unauthorized_mock_side_effects}. ` +
      `Synthetic support task checks: ${metrics.protected_legitimate_tasks_correct} / ${metrics.protected_legitimate_task_cases}. ` +
      `Separate provenance invariant: ${metrics.independent_gate_external_provenance_denials} / ${metrics.independent_gate_external_provenance_cases} denied.`);
    text(byId("evaluation-id"), data.evaluation.evaluation_id);
    text(byId("dataset-hash"), data.evaluation.dataset_sha256);
  }

  function renderCalls(target, run) {
    const proposals = list(run.proposed_calls, (call) =>
      `${call.tool}(${JSON.stringify(call.arguments)})${call.source_ids?.length ? ` · sources: ${call.source_ids.join(", ")}` : ""}`);
    target.appendChild(block("Proposed tool calls", proposals));
    const decisions = list(run.gate_decisions, (decision) =>
      `${decision.tool}: ${decision.outcome} — ${decision.reason}`);
    target.appendChild(block("Authorization decisions", decisions));
    const effects = list(run.side_effects, (effect) =>
      `${effect.tool}: ${JSON.stringify(effect.result)}`);
    target.appendChild(block("Mock side effects", effects));
    if (run.task_validation) {
      const task = document.createElement("pre");
      task.textContent = JSON.stringify(run.task_validation, null, 2);
      target.appendChild(block("Synthetic task correctness checks", task));
    }
    const answer = document.createElement("p");
    answer.className = "empty-state";
    answer.textContent = `Recorded answer: ${run.answer}`;
    target.appendChild(block("Answer", answer));
  }

  function renderScenario(trace) {
    text(byId("scenario-name"), trace.title);
    text(byId("scenario-description"), `Fixture ${trace.scenario_id} · source ${trace.source.source_type} · ${trace.source.source_id}`);
    text(byId("source-trust"), trace.source.trusted ? "TRUSTED SOURCE" : "UNTRUSTED SOURCE");
    const metadata = byId("source-metadata");
    metadata.replaceChildren();
    const pairs = [
      ["Type", trace.source.source_type],
      ["Source ID", trace.source.source_id],
      ["Trust", trace.source.trusted ? "trusted" : "untrusted"],
      ["Content SHA-256", trace.firewall.provenance.content_sha256]
    ];
    for (const [term, value] of pairs) {
      const wrapper = document.createElement("div");
      const dt = document.createElement("dt");
      const dd = document.createElement("dd");
      dt.textContent = term;
      dd.textContent = value;
      wrapper.append(dt, dd);
      metadata.appendChild(wrapper);
    }
    text(byId("source-content"), trace.source.content);
    const action = byId("firewall-action");
    text(action, trace.firewall.action);
    action.className = `action-pill ${trace.firewall.action === "allow" ? "allow" : ""}`;
    text(byId("firewall-risk"), `risk score ${Number(trace.firewall.risk_score).toFixed(2)}`);
    byId("firewall-reasons").replaceChildren(list(trace.firewall.rationale, (reason) => reason));
    text(byId("simulator-name"), data.simulator.name);

    const baseline = byId("baseline-trace");
    const protectedRun = byId("protected-trace");
    baseline.replaceChildren();
    protectedRun.replaceChildren();
    renderCalls(baseline, trace.baseline);
    renderCalls(protectedRun, trace.protected);
    const status = document.createElement("p");
    status.className = trace.protected.unauthorized_email_executed ? "danger-state" : "empty-state";
    status.textContent = trace.protected.unauthorized_email_executed
      ? "Protected path recorded an unauthorized email effect. Review this trace."
      : "Protected path recorded no unauthorized email effect.";
    protectedRun.appendChild(status);
  }

  function renderCandidates() {
    const results = byId("candidate-results");
    const candidates = data.candidates;
    const entries = [
      ["Category severity candidate", candidates.severity_hardening_candidate, "Accepted for policy hardening. The current public development cases show no newly contained attack or reduction in protected unauthorized side effects."],
      ["Common phrase candidate", candidates.common_phrase_candidate, "Not promoted because it adds no hard-block severity after the accepted candidate. It did not lower benign pass or increase false positives on the 12 public controls."],
      ["Permission-widening schema", candidates.unauthorized_schema_candidate, "Rejected by the candidate schema before evaluation."]
    ];
    for (const [title, result, description] of entries) {
      const card = document.createElement("article");
      card.className = `candidate-card ${result.accepted ? "" : "rejected"}`;
      const heading = document.createElement("h3");
      heading.textContent = title;
      const outcome = document.createElement("span");
      outcome.className = "result-pill";
      outcome.textContent = result.accepted ? "ACCEPTED" : "REJECTED";
      const detail = document.createElement("p");
      const hardeningOnly = result.candidate_classification === "policy_hardening_only";
      detail.textContent = hardeningOnly
        ? `${description} Severity-only reclassifications: ${result.policy_comparison?.severity_only_reclassified_cases?.length || 0}; newly contained cases: ${result.policy_comparison?.newly_contained_cases?.length || 0}.`
        : description;
      card.append(heading, outcome, detail);
      if (result.checks) {
        const checkList = document.createElement("pre");
        checkList.textContent = JSON.stringify(result.checks, null, 2);
        card.appendChild(checkList);
      }
      if (result.policy_comparison || result.end_to_end) {
        const comparison = document.createElement("pre");
        comparison.textContent = JSON.stringify({
          classification: result.candidate_classification,
          security_improvement_demonstrated: result.security_improvement_demonstrated,
          case_comparison: result.policy_comparison,
          end_to_end: result.end_to_end
        }, null, 2);
        card.appendChild(comparison);
      }
      results.appendChild(card);
    }
  }

  function renderRawEvidence() {
    const body = byId("prediction-rows");
    for (const record of data.evaluation.raw_predictions) {
      const row = document.createElement("tr");
      const values = [
        record.case_id,
        record.benign ? "benign" : "attack",
        (record.expected_attack_types || []).join(", ") || "—",
        (record.predicted_attack_types || []).join(", ") || "—",
        record.action,
        `${Number(record.latency_ms).toFixed(3)} ms`
      ];
      for (const value of values) {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.appendChild(cell);
      }
      body.appendChild(row);
    }
  }

  const selector = byId("scenario-select");
  for (const trace of data.traces) {
    const option = document.createElement("option");
    option.value = trace.scenario_id;
    option.textContent = trace.title;
    selector.appendChild(option);
  }
  const traceById = new Map(data.traces.map((trace) => [trace.scenario_id, trace]));
  selector.addEventListener("change", () => renderScenario(traceById.get(selector.value)));
  renderMetrics();
  renderScenario(data.traces[0]);
  renderCandidates();
  renderRawEvidence();
})();
