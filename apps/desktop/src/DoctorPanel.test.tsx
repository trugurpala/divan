import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import DoctorPanel, { type Capability, type DoctorPayload } from "./DoctorPanel";

afterEach(cleanup);

function capability(overrides: Partial<Capability> = {}): Capability {
  return {
    capability_id: "codex",
    display_name: "Codex",
    state: "CERTIFIED",
    affects: "Kod yazan çalışanlardan biri.",
    code: null,
    detail: null,
    evidence: "codex.exe",
    version: null,
    usable: true,
    ...overrides,
  };
}

function payload(overrides: Partial<DoctorPayload> = {}): DoctorPayload {
  return {
    schema_version: 1,
    checked_at: "2026-08-16T12:00:00+00:00",
    healthy: false,
    capabilities: [
      capability(),
      capability({
        capability_id: "claude",
        display_name: "Claude Code",
        state: "OFFLINE",
        code: "TOOL_NOT_INSTALLED",
        detail: "claude bulunamadı",
        evidence: null,
        usable: false,
      }),
      capability({
        capability_id: "local-state-security",
        display_name: "Yerel güvenlik kontrolü",
        state: "BLOCKED",
        code: "LOCAL_STATE_DACL_POLICY",
        detail: "trusted init state directory DACL grants mutation rights",
        affects: "Yerel kanıtın son doğrulaması eksik kalır; geliştirme durmaz.",
        evidence: null,
        usable: false,
      }),
    ],
    blocked_codes: ["LOCAL_STATE_DACL_POLICY"],
    unusable_ids: ["claude", "local-state-security"],
    human_summary: [
      "Codex hazır.",
      "Claude Code kurulu değil.",
      "Yerel güvenlik kontrolü engelli.",
      "Eksik yetenekler yalnız ilgili işlevi durdurur; geliştirme çalışmaya devam eder.",
    ],
    ...overrides,
  };
}

describe("DoctorPanel", () => {
  it("offers one button and says nothing before it is used", () => {
    const onCheck = vi.fn();
    render(<DoctorPanel payload={null} onCheck={onCheck} />);

    expect(screen.getByText("Henüz kontrol edilmedi.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Sistemi kontrol et" }));
    expect(onCheck).toHaveBeenCalledOnce();
  });

  it("opens on Padişah and speaks plain language only", () => {
    render(<DoctorPanel payload={payload()} onCheck={vi.fn()} />);

    expect(screen.getByRole("tab", { name: "Padişah" })).toHaveProperty(
      "ariaSelected",
      "true",
    );
    expect(screen.getByText("Codex hazır.")).toBeTruthy();
    expect(screen.getByText("Yerel güvenlik kontrolü engelli.")).toBeTruthy();

    // No reason codes or DACL vocabulary at the owner.
    expect(screen.queryByText("LOCAL_STATE_DACL_POLICY")).toBeNull();
    expect(screen.queryByText(/DACL grants mutation/)).toBeNull();
  });

  it("tells the owner a missing capability is not a dead product", () => {
    render(<DoctorPanel payload={payload()} onCheck={vi.fn()} />);

    expect(
      screen.getByText(/geliştirme çalışmaya devam eder/),
    ).toBeTruthy();
  });

  it("never presents a blocked capability as ready", () => {
    render(<DoctorPanel payload={payload()} onCheck={vi.fn()} />);
    fireEvent.click(screen.getByRole("tab", { name: "Divan" }));

    const panel = screen.getByRole("tabpanel");
    const blocked = within(panel)
      .getByText("Yerel güvenlik kontrolü")
      .closest("li");

    expect(blocked?.getAttribute("data-state")).toBe("BLOCKED");
    expect(within(blocked as HTMLElement).getByText("engelli")).toBeTruthy();
    // It must say what it costs the owner, not merely that it failed.
    expect(
      within(blocked as HTMLElement).getByText(/geliştirme durmaz/),
    ).toBeTruthy();
  });

  it("exposes reason codes and evidence only in the technical depth", () => {
    render(<DoctorPanel payload={payload()} onCheck={vi.fn()} />);
    fireEvent.click(screen.getByRole("tab", { name: "Teknik" }));

    const panel = screen.getByRole("tabpanel");
    expect(within(panel).getByText("LOCAL_STATE_DACL_POLICY")).toBeTruthy();
    expect(within(panel).getByText("TOOL_NOT_INSTALLED")).toBeTruthy();
    expect(within(panel).getByText(/DACL grants mutation/)).toBeTruthy();
  });

  it("keeps the depth switcher keyboard reachable and labelled", () => {
    render(<DoctorPanel payload={payload()} onCheck={vi.fn()} />);

    const tablist = screen.getByRole("tablist", { name: "Ayrıntı düzeyi" });
    const tabs = within(tablist).getAllByRole("tab");
    expect(tabs).toHaveLength(3);
    for (const tab of tabs) {
      expect(tab.tagName).toBe("BUTTON");
      tab.focus();
      expect(document.activeElement).toBe(tab);
    }
    expect(screen.getByRole("tabpanel").getAttribute("aria-labelledby")).toBeTruthy();
  });
});
