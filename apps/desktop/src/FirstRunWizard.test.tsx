import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Capability, DoctorPayload } from "./DoctorPanel";
import FirstRunWizard, { WIZARD_STEPS, capabilityLine } from "./FirstRunWizard";

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
    checked_at: "2026-08-17T09:00:00+00:00",
    healthy: false,
    capabilities: [
      capability({ capability_id: "divan-core", display_name: "Divan Core", evidence: "18 modül" }),
      capability({
        capability_id: "git",
        display_name: "Git",
        state: "DEGRADED",
        code: "AUTH_NOT_VERIFIED",
        detail: "çalıştırılabilir bulundu; oturum doğrulanmadı",
        evidence: "C:/Program Files/Git/cmd/git.exe",
      }),
      capability(),
      capability({
        capability_id: "claude",
        display_name: "Claude Code",
        state: "DEGRADED",
        code: "AUTH_REQUIRED",
        detail: "oturum açılmamış",
        evidence: "2.1.0",
        version: "2.1.0",
      }),
      capability({
        capability_id: "browser-qa",
        display_name: "Tarayıcı testi",
        state: "OFFLINE",
        code: "BROWSER_NOT_INSTALLED",
        detail: "playwright bu ortamda kullanılamıyor",
        evidence: null,
        usable: false,
      }),
      capability({ capability_id: "memory-store", display_name: "Hafıza deposu" }),
      capability({ capability_id: "memory-recall", display_name: "Hafıza geri çağırma" }),
      capability({ capability_id: "quality-factory", display_name: "Kalite fabrikası" }),
      capability({
        capability_id: "evidence",
        display_name: "Kanıt defteri",
        state: "INCOMPATIBLE",
        code: "CAPABILITY_NOT_CALLABLE",
        detail: "evidence.build_evidence",
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
    unusable_ids: ["browser-qa", "evidence", "local-state-security"],
    human_summary: [],
    ...overrides,
  };
}

const RAW_CODES = [
  "AUTH_REQUIRED",
  "AUTH_NOT_VERIFIED",
  "BROWSER_NOT_INSTALLED",
  "LOCAL_STATE_DACL_POLICY",
  "CAPABILITY_NOT_CALLABLE",
];

describe("FirstRunWizard", () => {
  it("welcomes the owner and renders nine steps in order", () => {
    render(<FirstRunWizard doctor={payload()} onComplete={vi.fn()} />);

    expect(screen.getByRole("heading", { name: "DİVAN'A HOŞ GELDİNİZ" })).toBeTruthy();
    const list = screen.getByRole("list", { name: "Kurulum adımları" });
    const items = within(list).getAllByRole("listitem");
    expect(items).toHaveLength(9);
    expect(WIZARD_STEPS.map((step) => step.title)).toEqual([
      "Divan Core",
      "Git",
      "Codex",
      "Claude Code",
      "Tarayıcı testi",
      "Hafıza",
      "Kalite ve kanıt",
      "Yerel güvenlik",
      "Çalışma klasörü",
    ]);
    expect(items[0].getAttribute("aria-current")).toBe("step");
  });

  it("maps every Core state to its glyph and plain sentence", () => {
    render(<FirstRunWizard doctor={payload()} onComplete={vi.fn()} />);

    expect(screen.getByText("✓ Codex hazır.")).toBeTruthy();
    expect(screen.getByText("⚠ Git kurulu ancak oturum doğrulanmadı.")).toBeTruthy();
    expect(screen.getByText("✗ Tarayıcı testi bulunamadı.")).toBeTruthy();
    expect(screen.getByText("⚠ Kanıt defteri uyumsuz sürüm.")).toBeTruthy();
    expect(screen.getByText("✓ Hafıza deposu hazır.")).toBeTruthy();
    expect(screen.getByText("✓ Hafıza geri çağırma hazır.")).toBeTruthy();
  });

  it("says a signed-out Claude is installed but not signed in", () => {
    render(<FirstRunWizard doctor={payload()} onComplete={vi.fn()} />);

    expect(screen.getByText("⚠ Claude Code kurulu ancak oturum açılmamış.")).toBeTruthy();
  });

  it("names the Windows policy for a blocked local security check", () => {
    render(<FirstRunWizard doctor={payload()} onComplete={vi.fn()} />);

    expect(
      screen.getByText("⚠ Yerel güvenlik kontrolü Windows politikası nedeniyle engelli."),
    ).toBeTruthy();
  });

  it("keeps reason codes, paths and raw detail out of the default view", () => {
    render(<FirstRunWizard doctor={payload()} onComplete={vi.fn()} />);

    for (const code of RAW_CODES) {
      expect(screen.queryByText(new RegExp(code))).toBeNull();
    }
    expect(screen.queryByText(/Program Files/)).toBeNull();
    expect(screen.queryByText(/DACL grants mutation/)).toBeNull();
    expect(screen.queryByText(/codex\.exe/)).toBeNull();
  });

  it("reveals the code only behind the technical disclosure", () => {
    render(<FirstRunWizard doctor={payload()} onComplete={vi.fn()} />);

    // Step 4 is Claude Code.
    fireEvent.click(screen.getByRole("button", { name: "Devam" }));
    fireEvent.click(screen.getByRole("button", { name: "Devam" }));
    fireEvent.click(screen.getByRole("button", { name: "Devam" }));
    expect(screen.queryByText(/AUTH_REQUIRED/)).toBeNull();

    const disclosure = screen.getByRole("button", { name: "Teknik ayrıntı" });
    expect(disclosure.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(disclosure);
    expect(disclosure.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByText(/AUTH_REQUIRED/)).toBeTruthy();
  });

  it("advances one step per Devam and closes the disclosure again", () => {
    render(<FirstRunWizard doctor={payload()} onComplete={vi.fn()} />);
    const list = screen.getByRole("list", { name: "Kurulum adımları" });
    const items = within(list).getAllByRole("listitem");

    fireEvent.click(screen.getByRole("button", { name: "Teknik ayrıntı" }));
    fireEvent.click(screen.getByRole("button", { name: "Devam" }));

    expect(items[0].getAttribute("aria-current")).toBeNull();
    expect(items[1].getAttribute("aria-current")).toBe("step");
    expect(screen.getByText(/Adım 2 \/ 9/)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Teknik ayrıntı" }).getAttribute("aria-expanded")).toBe(
      "false",
    );
  });

  it("promises Divan will try when the Core sends no owner action", () => {
    render(<FirstRunWizard doctor={payload()} onComplete={vi.fn()} />);

    // Step 5 is the browser check, reported OFFLINE without an action hint.
    for (let index = 0; index < 4; index += 1) {
      fireEvent.click(screen.getByRole("button", { name: "Devam" }));
    }
    expect(screen.getByText("Divan bunu kendisi hazırlamayı deneyecek.")).toBeTruthy();
  });

  it("shows the Core's owner action word for word when it sends one", () => {
    const doctor = payload();
    doctor.capabilities = doctor.capabilities.map((item) =>
      item.capability_id === "claude" ? { ...item, action_hint: "Claude Code'da oturum açın" } : item,
    );
    render(<FirstRunWizard doctor={doctor} onComplete={vi.fn()} />);

    for (let index = 0; index < 3; index += 1) {
      fireEvent.click(screen.getByRole("button", { name: "Devam" }));
    }
    expect(screen.getByText("Claude Code'da oturum açın")).toBeTruthy();
    expect(screen.queryByText("Divan bunu kendisi hazırlamayı deneyecek.")).toBeNull();
  });

  it("offers no owner action for a certified step", () => {
    render(<FirstRunWizard doctor={payload()} onComplete={vi.fn()} />);

    // Step 1, Divan Core, is CERTIFIED.
    expect(screen.queryByText("Divan bunu kendisi hazırlamayı deneyecek.")).toBeNull();
  });

  it("completes with the chosen workspace path", async () => {
    const onComplete = vi.fn();
    const pickWorkspace = vi.fn().mockResolvedValue("C:/Projeler/vaka-sistemi");
    render(
      <FirstRunWizard doctor={payload()} onComplete={onComplete} pickWorkspace={pickWorkspace} />,
    );

    for (let index = 0; index < 8; index += 1) {
      fireEvent.click(screen.getByRole("button", { name: "Devam" }));
    }
    expect(screen.queryByRole("button", { name: "Devam" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Klasör seç" }));

    await waitFor(() => expect(onComplete).toHaveBeenCalledWith("C:/Projeler/vaka-sistemi"));
    expect(pickWorkspace).toHaveBeenCalledOnce();
  });

  it("does not complete when the owner cancels the folder dialog", async () => {
    const onComplete = vi.fn();
    const pickWorkspace = vi.fn().mockResolvedValue(null);
    render(
      <FirstRunWizard doctor={payload()} onComplete={onComplete} pickWorkspace={pickWorkspace} />,
    );

    for (let index = 0; index < 8; index += 1) {
      fireEvent.click(screen.getByRole("button", { name: "Devam" }));
    }
    fireEvent.click(screen.getByRole("button", { name: "Klasör seç" }));

    await waitFor(() => expect(pickWorkspace).toHaveBeenCalledOnce());
    expect(onComplete).not.toHaveBeenCalled();
  });

  it("says a step is unchecked instead of guessing when the doctor has not run", () => {
    render(<FirstRunWizard doctor={null} onComplete={vi.fn()} onCheck={vi.fn()} />);

    expect(screen.getByText("… Divan Core henüz kontrol edilmedi.")).toBeTruthy();
    expect(screen.queryByText(/hazır\./)).toBeNull();
  });
});

describe("capabilityLine", () => {
  it("never certifies a capability the Core did not certify", () => {
    for (const state of ["DEGRADED", "OFFLINE", "INCOMPATIBLE", "BLOCKED"] as const) {
      const line = capabilityLine(capability({ state, code: "X" }));
      expect(line.glyph).not.toBe("✓");
      expect(line.sentence).not.toMatch(/hazır\.$/);
    }
    expect(capabilityLine(capability()).glyph).toBe("✓");
  });
});
