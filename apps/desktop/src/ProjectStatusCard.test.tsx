import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import ProjectStatusCard from "./ProjectStatusCard";
import type { AgencyStatus } from "./humanStatus";

afterEach(cleanup);

function status(overrides: Partial<AgencyStatus> = {}): AgencyStatus {
  return {
    schema_version: 1,
    project: "vaka-sistemi",
    project_root: "C:/tmp/vaka-sistemi",
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
      blocked: 1,
      awaiting_owner: 0,
      ready_task_ids: [],
      state_counts: {},
    },
    state_health: "healthy",
    ...overrides,
  };
}

describe("ProjectStatusCard", () => {
  it("opens on the Padişah depth and shows no technical vocabulary", () => {
    render(<ProjectStatusCard status={status()} />);

    expect(screen.getByRole("tab", { name: "Padişah" })).toHaveProperty(
      "ariaSelected",
      "true",
    );
    expect(screen.getByText("Geliştirme sürüyor")).toBeTruthy();
    expect(screen.getByText("8 işin 5 tanesi tamamlandı.")).toBeTruthy();
    expect(screen.getByText("Bir iş durdu.")).toBeTruthy();
    expect(
      screen.getByText(/güvenli tekrar denemeyi başlattı/),
    ).toBeTruthy();
    expect(screen.getByText("Sizden işlem beklenmiyor.")).toBeTruthy();

    // The default view must not leak worktree or exit codes at the owner.
    expect(screen.queryByText("Worktree")).toBeNull();
    expect(screen.queryByText(/C:\/tmp/)).toBeNull();
  });

  it("never shows Hazır while the work is only implemented", () => {
    render(
      <ProjectStatusCard
        status={status({
          work_packages: {
            ...status().work_packages,
            completed: 8,
            active: 0,
            blocked: 0,
          },
        })}
      />,
    );

    const badge = screen.getByText("Yapılıyor");
    expect(badge.getAttribute("data-readiness")).toBe("working");
    expect(screen.queryByText("Hazır")).toBeNull();
  });

  it("shows Hazır only when Core reports delivery ready", () => {
    render(<ProjectStatusCard status={status({ phase: "DELIVERY_READY" })} />);

    expect(screen.getByText("Hazır").getAttribute("data-readiness")).toBe("ready");
  });

  it("does not present a BLOCKED project as ready", () => {
    render(
      <ProjectStatusCard
        status={status({
          phase: "BLOCKED",
          attention: "blocked",
          state_health: "invalid",
          state_problem: "Aktif ferman makbuzu doğrulanamadı.",
        })}
      />,
    );

    expect(screen.queryByText("Hazır")).toBeNull();
    expect(screen.getByText("Beklemede").getAttribute("data-readiness")).toBe(
      "blocked",
    );
    expect(screen.getByText("Aktif ferman makbuzu doğrulanamadı.")).toBeTruthy();
  });

  it("makes an owner decision visible rather than burying it", () => {
    render(
      <ProjectStatusCard
        status={status({ phase: "OWNER_DECISION", attention: "decision" })}
      />,
    );

    const owner = screen.getByText("Bir karar sizi bekliyor.");
    expect(owner.className).toContain("agency-owner-decision");
  });

  it("drills down to Divan and Teknik detail on request", () => {
    render(
      <ProjectStatusCard
        status={status()}
        technical={{
          provider: "codex",
          worker: "worker-7",
          attempt: 2,
          worktree: "C:/tmp/wt/DIV-1",
          exitCode: 1,
          diffSha256: "abc123",
          receipt: "receipt-9",
        }}
      />,
    );

    fireEvent.click(screen.getByRole("tab", { name: "Divan" }));
    const divan = screen.getByRole("tabpanel");
    expect(within(divan).getByText("IMPLEMENTATION")).toBeTruthy();
    expect(within(divan).getByText(/5\/8 tamamlandı/)).toBeTruthy();

    fireEvent.click(screen.getByRole("tab", { name: "Teknik" }));
    const technical = screen.getByRole("tabpanel");
    expect(within(technical).getByText("codex")).toBeTruthy();
    expect(within(technical).getByText("worker-7")).toBeTruthy();
    expect(within(technical).getByText("C:/tmp/wt/DIV-1")).toBeTruthy();
    expect(within(technical).getByText("abc123")).toBeTruthy();
  });

  it("keeps the depth switcher keyboard reachable and labelled", () => {
    render(<ProjectStatusCard status={status()} />);

    const tablist = screen.getByRole("tablist", { name: "Ayrıntı düzeyi" });
    const tabs = within(tablist).getAllByRole("tab");
    expect(tabs).toHaveLength(3);
    for (const tab of tabs) {
      // Native buttons are focusable and operable by keyboard by default.
      expect(tab.tagName).toBe("BUTTON");
      tab.focus();
      expect(document.activeElement).toBe(tab);
    }
    const panel = screen.getByRole("tabpanel");
    expect(panel.getAttribute("aria-labelledby")).toBeTruthy();
  });
});
