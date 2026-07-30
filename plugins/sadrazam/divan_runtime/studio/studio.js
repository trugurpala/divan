"use strict";

const CAPABILITY_KEY = "divan-seyir-capability";
const STALE_AFTER_MS = 10000;
const fragmentToken = window.location.hash.slice(1);
let token = fragmentToken;
try {
  if (fragmentToken) sessionStorage.setItem(CAPABILITY_KEY, fragmentToken);
  else token = sessionStorage.getItem(CAPABILITY_KEY) ?? "";
} catch {
  token = fragmentToken;
}
if (fragmentToken) {
  history.replaceState(null, "", `${window.location.pathname}${window.location.search}`);
}

const phaseOrder = ["FERMAN", "PLAN", "ICRA", "TEFTIS", "YAYIN"];
let copy = {};
let currentEtag = null;
let lastSuccessfulAt = 0;

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) node.textContent = value ?? "—";
}

function format(template, values) {
  return template.replace(/\{(\w+)\}/g, (_, key) => String(values[key] ?? ""));
}

function translated(key, fallback = "—") {
  return copy[key] ?? fallback;
}

function stateKey(state) {
  const normalized = String(state ?? "unknown").toLowerCase();
  const aliases = {
    discovered: "running",
    specified: "running",
    planned: "running",
    implementing: "running",
    verified: "complete",
    previewed: "complete",
    released: "complete",
    observed: "complete",
    no_active_goal: "pending",
    pass: "passed",
    fail: "failed",
  };
  return `state.${aliases[normalized] ?? normalized}`;
}

function clearList(id) {
  const list = document.getElementById(id);
  while (list.firstChild) list.removeChild(list.firstChild);
  return list;
}

function appendListItem(list, text, status) {
  const item = document.createElement("li");
  const label = status ? `${status} · ${text}` : text;
  item.textContent = label;
  list.appendChild(item);
}

function renderLabels() {
  const labels = {
    "app-title": "app.title",
    "app-subtitle": "app.subtitle",
    "request-label": "progress.request",
    "current-task-label": "progress.current_task",
    "completed-label": "progress.completed",
    "checks-label": "progress.checks",
    "blocker-label": "progress.blocker",
    "next-action-label": "progress.next_action",
    "technical-title": "technical.title",
    "branch-label": "technical.branch",
    "commit-label": "technical.commit",
    "changed-label": "technical.changed",
    "evidence-label": "technical.evidence",
    "task-list-label": "technical.tasks",
    "skip-link": "navigation.skip",
  };
  for (const [id, key] of Object.entries(labels)) setText(id, translated(key));
  document.getElementById("phase-rail").setAttribute(
    "aria-label",
    translated("navigation.progress"),
  );
  document.getElementById("progress-summary").setAttribute(
    "aria-label",
    translated("progress.summary"),
  );
  document.title = translated("app.title", "Divan Seyir");
  for (const phase of phaseOrder) {
    const item = document.querySelector(`[data-phase="${phase}"]`);
    item.querySelector(".phase-label").textContent =
      translated(`phase.${phase.toLowerCase()}`, phase);
  }
}

function renderPhases(snapshot) {
  const currentIndex = phaseOrder.indexOf(snapshot.current.phase);
  for (const [index, phase] of phaseOrder.entries()) {
    const item = document.querySelector(`[data-phase="${phase}"]`);
    const state = index < currentIndex ? "complete" :
      index === currentIndex ? "current" : "pending";
    item.dataset.state = state;
    if (state === "current") item.setAttribute("aria-current", "step");
    else item.removeAttribute("aria-current");
    const messageKey = state === "current" ? stateKey(snapshot.goal.status) :
      `state.${state === "complete" ? "complete" : "pending"}`;
    item.querySelector(".phase-state").textContent = translated(messageKey);
  }
}

function render(snapshot) {
  copy = snapshot.copy ?? {};
  document.documentElement.lang = snapshot.locale;
  renderLabels();

  const noGoal = snapshot.goal.status === "NO_ACTIVE_GOAL";
  setText(
    "goal-title",
    noGoal ? translated("progress.no_active_goal") : snapshot.goal.title,
  );
  setText("goal-status", translated(stateKey(snapshot.goal.status)));
  document.getElementById("goal-status").dataset.state = snapshot.goal.status;
  setText(
    "current-task",
    noGoal ? translated("progress.no_active_goal_hint") :
      snapshot.current.task ?? translated("progress.no_current_task"),
  );

  const complete = snapshot.tasks.filter((task) => task.status === "DONE").length;
  setText(
    "completed-summary",
    format(translated("progress.task_count"), {
      complete,
      total: snapshot.tasks.length,
    }),
  );

  const checks = clearList("checks-list");
  if (snapshot.checks.length === 0) {
    appendListItem(checks, translated("state.unknown"));
  } else {
    for (const check of snapshot.checks) {
      appendListItem(checks, check.id, translated(stateKey(check.status)));
    }
  }

  const blocker = snapshot.blocker;
  setText(
    "blocker",
    blocker?.reason || (blocker ? translated(stateKey(blocker.state)) :
      translated("progress.no_blocker")),
  );
  document.getElementById("blocker-card").dataset.state =
    blocker ? blocker.state : "CLEAR";
  setText(
    "next-action",
    snapshot.next_action ?? translated("progress.no_next_action"),
  );
  setText(
    "progress-announcer",
    format(translated("progress.live_summary"), {
      complete,
      total: snapshot.tasks.length,
      current: snapshot.current.task ?? translated("progress.no_current_task"),
      next: snapshot.next_action ?? translated("progress.no_next_action"),
    }),
  );

  setText("branch", snapshot.project.branch);
  setText("commit", snapshot.project.head);
  setText(
    "changed",
    snapshot.project.dirty === null ? translated("state.unknown") :
      snapshot.project.dirty ? translated("state.running") :
        translated("state.complete"),
  );

  const evidence = clearList("evidence-list");
  if (snapshot.evidence.length === 0) {
    appendListItem(evidence, translated("state.unknown"));
  } else {
    for (const row of snapshot.evidence) appendListItem(evidence, row.label);
  }

  const tasks = clearList("task-list");
  if (snapshot.tasks.length === 0) {
    appendListItem(tasks, translated("progress.no_current_task"));
  } else {
    for (const task of snapshot.tasks) {
      appendListItem(tasks, task.title, translated(stateKey(task.status)));
    }
  }

  renderPhases(snapshot);
  markConnected();
}

function markConnected() {
  lastSuccessfulAt = Date.now();
  const connection = document.getElementById("connection-state");
  connection.dataset.state = "connected";
  setText("connection-label", translated("connection.connected"));
}

function markFailure(error) {
  const connection = document.getElementById("connection-state");
  const unauthorized = error.message === "unauthorized";
  if (unauthorized) {
    try {
      sessionStorage.removeItem(CAPABILITY_KEY);
    } catch {
      // The page remains safely unauthorized when storage is unavailable.
    }
  }
  const stale = !unauthorized && lastSuccessfulAt > 0 &&
    Date.now() - lastSuccessfulAt >= STALE_AFTER_MS;
  connection.dataset.state = stale ? "stale" : "disconnected";
  const key = unauthorized ? "connection.unauthorized" :
    stale ? "progress.stale" : "connection.disconnected";
  setText(
    "connection-label",
    translated(key, "The local connection was interrupted."),
  );
}

async function refresh() {
  if (!token) {
    document.getElementById("connection-state").dataset.state = "disconnected";
    setText(
      "connection-label",
      translated(
        "connection.missing_capability",
        "This local session link is incomplete.",
      ),
    );
    return;
  }
  const headers = {"X-Divan-Session": token};
  if (currentEtag) headers["If-None-Match"] = currentEtag;
  try {
    const response = await fetch("/api/status", {cache: "no-store", headers});
    if (response.status === 304) {
      markConnected();
      return;
    }
    if (response.status === 401) throw new Error("unauthorized");
    if (!response.ok) throw new Error(`status ${response.status}`);
    currentEtag = response.headers.get("ETag");
    render(await response.json());
  } catch (error) {
    markFailure(error);
  }
}

refresh();
window.setInterval(refresh, 2000);
