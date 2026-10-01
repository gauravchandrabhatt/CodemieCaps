const $ = (selector) => document.querySelector(selector);
const templates = {
  analysis: "Enhancement: clarify ownership and due dates. Gap: the existing tracker does not show approval status or an auditable decision trail. Opportunity: add a visible SDLC pipeline with explicit human review gates.",
  planning: "Epic: Improve delivery transparency.\nStory: As a reviewer, I can approve or reject each assistant-produced phase with a note.\nAcceptance: the next phase remains locked until approval; decisions are recorded with actor and timestamp.",
  design: "Design: Single-project dashboard, SQLite persistence, FastAPI JSON API, and a vanilla JavaScript client. Workflow stages are ordered records; audit events are append-only. Human review is the only transition that unlocks the next stage.",
  development: "Implementation plan: persist work items, stages, and audit events in SQLite; expose validated REST endpoints; render workflow and backlog; record reviewer decisions. Integrations are represented as explicit artifacts, not simulated external calls.",
  "code-review": "Review checklist: validate workflow stage ordering, reject invalid transitions, preserve reviewer identity and notes, validate user input, and verify audit events. Human reviewer should inspect changes before accepting this phase.",
  testing: "Acceptance: health endpoint returns OK; work items persist; a review decision is audited; approval unlocks exactly one next phase; rejected work can be resubmitted; later phases cannot be reviewed early.",
  deployment: "Local deployment: run the FastAPI service on 127.0.0.1:8000 with a persistent SQLite database. Docker Compose is also available. Verify /api/health before demoing the workflow.",
  documentation: "Deliverables: README, product requirements, architecture and data model, design notes, wireframe, implementation plan, Gherkin scenarios, and automated test results are maintained alongside the code."
};
let currentWorkflow;
let toastTimer;

function showToast(message, isError = false) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("visible"), 3000);
}

async function request(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}

function renderStages(workflow) {
  const list = $("#stage-list");
  list.replaceChildren();
  workflow.stages.forEach((stage, index) => {
    const row = document.createElement("button");
    row.type = "button";
    row.className = `stage-row ${stage.status}${stage.key === workflow.current_stage ? " selected" : ""}`;
    row.disabled = stage.key !== workflow.current_stage;
    const indicator = stage.status === "approved" ? "✓" : stage.status === "in_review" ? "◷" : stage.status === "rejected" ? "!" : String(index + 1).padStart(2, "0");
    row.innerHTML = `<span class="stage-number">${indicator}</span><span class="stage-copy"><strong></strong><small></small></span><span class="stage-status"></span>`;
    row.querySelector("strong").textContent = stage.title;
    row.querySelector("small").textContent = stage.persona;
    row.querySelector(".stage-status").textContent = stage.status.replace("_", " ");
    list.append(row);
  });
}

function renderReview(workflow) {
  const card = $("#review-card");
  const stage = workflow.stages.find((item) => item.key === workflow.current_stage);
  if (!stage) {
    card.innerHTML = '<div class="complete-state"><span>✦</span><h3>All phases complete</h3><p>The full workflow has been approved. Every decision remains in the audit trail.</p></div>';
    return;
  }
  const reviewing = stage.status === "in_review";
  const rejected = stage.status === "rejected";
  card.innerHTML = `<div class="review-top"><span class="review-tag">${reviewing ? "HUMAN REVIEW REQUIRED" : rejected ? "REVISION REQUESTED" : "NEXT PHASE"}</span><span class="review-step">PHASE ${String(stage.position).padStart(2, "0")} / 08</span></div><h3></h3><p class="review-persona"></p><label class="field-label" for="artifact">${reviewing ? "Assistant artifact · edit before deciding" : "Draft artifact · review before submission"}</label><textarea id="artifact" rows="6" maxlength="12000"></textarea><label class="field-label" for="review-note">${reviewing ? "Reviewer note (required)" : ""}</label>${reviewing ? '<textarea id="review-note" rows="2" maxlength="2000" placeholder="Add a short review note…"></textarea>' : ""}<div class="review-actions">${reviewing ? '<button class="button reject" id="reject-stage">Request changes</button><button class="button primary" id="approve-stage">Approve phase →</button>' : '<button class="button primary full" id="submit-stage">Submit for human review →</button>'}</div><p class="review-foot">Approving unlocks only the next phase. Decisions are recorded.</p>`;
  card.querySelector("h3").textContent = stage.title;
  card.querySelector(".review-persona").textContent = `${stage.persona} · ${stage.status === "in_review" ? `submitted by assistant` : "human gate"}`;
  $("#artifact").value = stage.artifact || templates[stage.key] || "Add the phase artifact here…";
  if (reviewing) {
    $("#approve-stage").addEventListener("click", () => decide(stage, "approve"));
    $("#reject-stage").addEventListener("click", () => decide(stage, "reject"));
  } else {
    $("#submit-stage").addEventListener("click", () => submit(stage));
  }
}

async function decide(stage, decision) {
  const note = $("#review-note").value.trim();
  if (note.length < 3) return showToast("Add a review note (at least 3 characters).", true);
  try {
    await request(`/api/workflow/stages/${stage.key}/decision`, { method: "POST", body: JSON.stringify({ decision, actor: "Human reviewer", note, artifact: $("#artifact").value.trim() }) });
    showToast(decision === "approve" ? "Phase approved. The next phase is unlocked." : "Changes requested. The phase can be revised and resubmitted.");
    await refresh();
  } catch (error) { showToast(error.message, true); }
}

async function submit(stage) {
  const artifact = $("#artifact").value.trim();
  if (artifact.length < 3) return showToast("Add an artifact before requesting review.", true);
  try {
    await request(`/api/workflow/stages/${stage.key}/submit`, { method: "POST", body: JSON.stringify({ artifact, actor: "Assistant draft" }) });
    showToast("Submitted. Waiting for a human decision.");
    await refresh();
  } catch (error) { showToast(error.message, true); }
}

function renderBacklog(items) {
  const list = $("#backlog-list");
  list.replaceChildren();
  if (!items.length) { list.innerHTML = '<p class="empty-copy">No items yet. Add an enhancement to get started.</p>'; return; }
  items.forEach((item) => {
    const row = document.createElement("article");
    row.className = "backlog-row";
    row.innerHTML = '<span class="item-key"></span><span class="item-main"><strong></strong><small></small></span><span class="priority"></span>';
    row.querySelector(".item-key").textContent = item.key;
    row.querySelector(".item-main strong").textContent = item.title;
    row.querySelector(".item-main small").textContent = `${item.item_type} · ${item.status}`;
    const priority = row.querySelector(".priority");
    priority.textContent = item.priority;
    priority.className = `priority ${item.priority}`;
    list.append(row);
  });
}

function renderAudit(events) {
  const list = $("#audit-list");
  list.replaceChildren();
  if (!events.length) { list.innerHTML = '<p class="empty-copy">Actions will appear here.</p>'; return; }
  events.slice(0, 7).forEach((event) => {
    const row = document.createElement("article");
    row.className = "audit-row";
    const action = event.action.replace("stage.", "").replace("workflow.seeded", "workflow started");
    row.innerHTML = '<span class="audit-icon">↗</span><span class="audit-main"><strong></strong><small></small></span>';
    row.querySelector(".audit-main strong").textContent = `${event.actor} · ${action}`;
    row.querySelector(".audit-main small").textContent = `${event.entity_key} · ${event.details}`;
    list.append(row);
  });
}

async function refresh() {
  try {
    const [workflow, dashboard, items, events] = await Promise.all([
      request("/api/workflow"), request("/api/dashboard"), request("/api/work-items"), request("/api/audit")
    ]);
    currentWorkflow = workflow;
    $("#stat-items").textContent = dashboard.work_items;
    $("#stat-review").textContent = dashboard.awaiting_review;
    $("#stat-approved").textContent = dashboard.stages_approved;
    $("#stat-total").textContent = `of ${dashboard.stages_total} total phases`;
    renderStages(workflow);
    renderReview(workflow);
    renderBacklog(items);
    renderAudit(events);
  } catch (error) { showToast(error.message, true); }
}

$("#add-item").addEventListener("click", () => $("#item-dialog").showModal());
$("#item-form").addEventListener("submit", async (event) => {
  if (event.submitter?.value === "cancel") return;
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const button = $("#save-item");
  button.disabled = true;
  try {
    await request("/api/work-items", { method: "POST", body: JSON.stringify(Object.fromEntries(form)) });
    $("#item-dialog").close();
    event.currentTarget.reset();
    showToast("Enhancement added to the backlog.");
    await refresh();
  } catch (error) { showToast(error.message, true); }
  finally { button.disabled = false; }
});

refresh();
