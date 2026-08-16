import { describe, expect, it } from "vitest";

import {
  type AgencyStatus,
  presentAgencyStatus,
  readinessLabel,
} from "./humanStatus";

function status(overrides: Partial<AgencyStatus> = {}): AgencyStatus {
  return {
    schema_version: 1,
    project: "demo",
    project_root: "C:/tmp/demo",
    active_goal_id: "goal-1",
    goal_state: "PREVIEWED",
    goal_count: 1,
    phase: "IMPLEMENTATION",
    attention: "none",
    execution_authority: "not-granted",
    work_packages: {
      total: 8,
      completed: 5,
      active: 2,
      verifying: 0,
      blocked: 0,
      awaiting_owner: 0,
      ready_task_ids: [],
      state_counts: {},
    },
    state_health: "healthy",
    ...overrides,
  };
}

describe("presentAgencyStatus", () => {
  it("answers the six owner questions in plain language", () => {
    const human = presentAgencyStatus(status());

    expect(human.doing).toBe("Geliştirme sürüyor");
    expect(human.progress).toBe("8 işin 5 tanesi tamamlandı.");
    expect(human.problem).toBeNull();
    expect(human.ownerAction).toBe("Sizden işlem beklenmiyor.");
    expect(human.needsOwner).toBe(false);
    expect(human.nextStep).not.toHaveLength(0);
  });

  it("reports a stopped work package as a problem and says what Divan did", () => {
    const human = presentAgencyStatus(
      status({
        work_packages: { ...status().work_packages, blocked: 1 },
      }),
    );

    expect(human.problem).toBe("Bir iş durdu.");
    expect(human.divanAction).toContain("güvenli tekrar denemeyi başlattı");
    // A recoverable failure is Divan's job, not an owner interruption.
    expect(human.needsOwner).toBe(false);
  });

  it("never reports Hazır while work is only implemented", () => {
    // "Code written" and "Ready" must not collapse into one state.
    const allDone = status({
      phase: "IMPLEMENTATION",
      work_packages: {
        ...status().work_packages,
        total: 8,
        completed: 8,
        active: 0,
      },
    });

    expect(presentAgencyStatus(allDone).readiness).toBe("working");
    expect(readinessLabel(presentAgencyStatus(allDone).readiness)).not.toBe("Hazır");
  });

  it("only reports Hazır once Core says delivery is ready", () => {
    for (const phase of ["DELIVERY_READY", "RELEASED"]) {
      const human = presentAgencyStatus(status({ phase }));
      expect(human.readiness).toBe("ready");
      expect(readinessLabel(human.readiness)).toBe("Hazır");
    }
  });

  it("treats a BLOCKED phase as blocked and never as ready", () => {
    const human = presentAgencyStatus(
      status({
        phase: "BLOCKED",
        attention: "blocked",
        state_health: "invalid",
        state_problem: "Active goal receipt could not be verified.",
      }),
    );

    expect(human.readiness).toBe("blocked");
    expect(human.problem).toBe("Active goal receipt could not be verified.");
    expect(readinessLabel(human.readiness)).not.toBe("Hazır");
  });

  it("surfaces an owner decision instead of hiding it", () => {
    const human = presentAgencyStatus(
      status({ phase: "OWNER_DECISION", attention: "decision" }),
    );

    expect(human.needsOwner).toBe(true);
    expect(human.ownerAction).toBe("Bir karar sizi bekliyor.");
    expect(human.nextStep).toContain("Kararınızdan sonra");
  });

  it("does not invent progress when no work packages exist yet", () => {
    const human = presentAgencyStatus(
      status({
        phase: "INTAKE",
        work_packages: { ...status().work_packages, total: 0, completed: 0, active: 0 },
      }),
    );

    expect(human.progress).toBe("Henüz iş paketi çıkarılmadı.");
    expect(human.readiness).toBe("planning");
  });
});
