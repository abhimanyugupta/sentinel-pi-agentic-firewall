# SENTINEL PI Product Specification

## Mission
Deliver the strongest defensible, reproducible prototype for ET AI Hackathon: Agentic Edition, Problem 2: Agentic Cybersecurity — Prompt Injection Firewall. Prioritize the protected end-to-end demonstration over unverified breadth.

## Core claim
SENTINEL PI preserves untrusted-content provenance, surfaces attack indicators, protects a synthetic final answer, and enforces original user intent at an independent deterministic tool boundary. Candidate mitigations are evaluated against malicious and benign development fixtures before activation. This is a bounded offline prototype, not a claim to eliminate prompt injection.

## Users and threat model
The primary reviewer is a security judge evaluating whether an agent can safely use lower-trust content while proposing tool actions. Inputs may be user text, retrieved web pages, documents, APIs, email, or code containing direct or indirect malicious instructions. Attackers may attempt instruction override, role change, secret extraction, tool abuse, credential theft, context poisoning, multi-step jailbreaks, encoded instructions, or indirect prompt injection. The detector may miss an attack or flag benign text; authorization must therefore be independently checked at the tool boundary.

No real customer data, credentials, external email, production system, external target, or arbitrary execution is in scope.

## Required layers
1. **Untrusted-content firewall:** accept bounded text envelopes, preserve source identity, trust status, source hash and suspicious spans, and normalize supported text without executing it.
2. **Structured classifier seam:** separate bounded preprocessing and deterministic offline rules from a strict injectable classifier contract. Invalid or unavailable classification must quarantine, never silently allow.
3. **Answer integrity:** detect the planted canary and fixture-labeled unsupported claims in the final answer. The prototype must not present those unsupported claims as verified facts. The lexical claim guard is scenario evidence, not general semantic verification.
4. **Intent-bound authorization:** bind calls to a typed original-user-intent contract including allowed tools, exact argument shape, allowed records/destinations, sensitive-data restrictions, approval state and call budgets. A deterministic gate rechecks immediately before each side effect and returns allow, deny, or require-approval; pending approval never triggers a side effect.
5. **Synthetic agent workflow:** use only fictional customer support tools: search_customer, create_ticket, and send_email in an in-memory mock runtime.
6. **Baseline and protected paths:** replay the same content-triggered attack against an isolated unprotected baseline, where it causes one unauthorized mock action; the protected firewall withholds blocked/quarantined content before the proposal parser while legitimate work completes. A separate gate invariant checks external-source actions when content screening is bypassed or missed.
7. **Candidate-mitigation loop:** candidates use a restricted schema and cannot edit tool permission or active policy directly. Evaluate each in isolation against public attack and benign fixtures plus fixed safety invariants. Preserve versioned evidence and rollback history.
8. **Evaluation:** compute category outcomes, raw predictions, fixture hashes, attack containment, benign pass rate, false positives, latency, tool-gate violations, canary leaks, unsupported-answer claims and before/after outcomes from real runs.
9. **Presentation:** deliver a local dashboard, reproducible commands, architecture, evaluation method, honest F/D self-assessment, 2–4 minute demo script and pitch content.

## Scope and claim boundary
The public development corpus is a regression set, not a blind benchmark. The Problem 2 rubric defines F1 as at least two attack types, F2 as at least five, and F3 as at least seven. All nine configured categories have public fixture-level observations, so F3 is supportable as feature coverage for this prototype. The defensible depth self-assessment is D1: text-oriented inputs and acceptable outputs on a majority of this finite public replay set. The small, known corpus does not establish D2's high degree of demonstrable reliability; D3 is unsupported because there is no heterogeneous multimodal input. Do not claim universal prevention, production readiness, live-model performance, autonomous learning, or semantic truth verification. (Official basis: ET AI Hackathon Detailed Problem Statements, Problem 2, pp. 7–8.)
The agent workflow is a deterministic, content-triggered offline simulator for reproducible fixtures. It is not a live model and its outputs are not evidence of model behavior.

## Definition of Done
- [x] Legitimate synthetic customer search and ticket workflow completes.
- [x] The isolated baseline simulator derives an unauthorized mock email proposal from malicious fixture text; the protected firewall withholds block/quarantine content before the proposal parser.
- [x] A separate provenance-sensitive gate invariant denies an otherwise permitted side-effect proposal sourced from untrusted external content, with no mock side effect.
- [x] The protected path keeps the legitimate ticket and reports zero tool-gate violations.
- [x] A permitted tool that requires missing approval returns `require_approval` and produces no side effect.
- [x] Answer-contamination fixture demonstrates baseline canary and unsupported-claim exposure, then protected redaction.
- [x] Candidate changes are tested against attack containment, policy severity, benign controls, end-to-end side effects, task correctness, and the fixed gate invariant. The public accepted category candidate is explicitly classified as policy hardening only because it changes five quarantine decisions to block without containing a new attack.
- [x] Automated standard-library tests run without a network or API key.
- [x] Documented CLI and loopback web dashboard run locally.
- [x] Dashboard metrics and traces derive from reproducible executions.
- [x] Setup, architecture, evaluation, demo script, pitch content, and curated export package are present.
- [x] Final clean-room run, complete verification, generated archive inspection, and privacy review are recorded in STATUS.md.

## Constraints
- Keep all project artifacts in this directory and preserve parent workspace materials.
- Use synthetic fixtures and mock side effects only.
- No unapproved package installation or download; prefer Python standard library.
- Keep personal details, credentials, private/blind evaluation cases, and local machine paths out of tracked files and export archives.
- External changes require explicit, action-specific human authorization. Deployment, public release, repository visibility changes, spending, production credential access, and external submission remain out of scope for this prototype.

## Deadline
Target submission readiness before 2026-10-11 23:59 IST. Reserve time for a clean local run, regression checks, demo rehearsal, and human submission review.
