import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const PROJECT_ROOT = "C:/Projeler/vaka-sistemi";

const doctorPayload = {
  schema_version: 1,
  checked_at: "2026-08-17T09:00:00+00:00",
  healthy: true,
  capabilities: [
    {
      capability_id: "memory-store",
      display_name: "Hafıza deposu",
      state: "CERTIFIED",
      affects: "Geçmiş karar ve derslerin hatırlanması.",
      code: null,
      detail: null,
      evidence: "3 kayıt okundu",
      version: null,
      usable: true,
    },
    {
      capability_id: "memory-recall",
      display_name: "Hafıza geri çağırma",
      state: "DEGRADED",
      affects: "Planlamadan önce bilinenlerin hatırlanması.",
      code: "MEMORY_STORE_UNREADABLE",
      detail: "OperationalError",
      evidence: null,
      version: null,
      usable: true,
    },
  ],
  blocked_codes: [],
  unusable_ids: [],
  human_summary: ["Hafıza deposu hazır.", "Divan hazır."],
};

const agencyStatus = {
  schema_version: 1,
  project: "vaka-sistemi",
  project_root: PROJECT_ROOT,
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
};

function envelope(result: unknown) {
  return JSON.stringify({ api_version: 1, ok: true, result });
}

const coreResponses: Record<string, unknown> = {
  capabilities: { product: "divan", api_version: 1, features: [], commands: [] },
  readiness: {
    ready: true,
    tools: [
      {
        id: "codex",
        display_name: "Codex",
        available: true,
        path: "C:/divan-tools/codex.cmd",
        required: true,
        version: "0.147.0",
        auth: "connected",
        auth_detail: "chatgpt",
        subscription_supported: true,
        api_key_configured: false,
        app_installed: false,
        app_version: null,
      },
    ],
    engines: ["native"],
    recommended_engine: "native",
    recommended_agent: "codex",
    api_keys_required: false,
  },
  "project.list": [
    {
      project_id: "p1",
      name: "vaka-sistemi",
      root: PROJECT_ROOT,
      created_at: "2026-08-17T08:00:00+00:00",
      last_opened_at: "2026-08-17T08:00:00+00:00",
    },
  ],
  "task.list": [],
  "evidence.list": [],
  doctor: doctorPayload,
  "project.agency.status": agencyStatus,
};

vi.mock("@tauri-apps/api/core", () => ({
  invoke: vi.fn(async (command: string, args?: { request?: string }) => {
    if (command === "divan_capabilities") {
      return { product: "divan", version: "1.3.8", apiVersion: 1, shell: "tauri", features: [] };
    }
    if (command === "core_request" && args?.request) {
      const request = JSON.parse(args.request) as { command: string };
      if (request.command in coreResponses) return envelope(coreResponses[request.command]);
      return JSON.stringify({
        api_version: 1,
        ok: false,
        error: { code: "UNKNOWN", message: request.command },
      });
    }
    throw new Error(`unexpected invoke ${command}`);
  }),
}));

vi.mock("@tauri-apps/plugin-dialog", () => ({ open: vi.fn() }));

import App from "./App";

beforeEach(() => {
  window.localStorage.clear();
});
afterEach(cleanup);

async function renderShell() {
  window.localStorage.setItem("divan.firstRunDone", "1");
  render(<App />);
  await waitFor(() => expect(screen.getByRole("navigation", { name: "Ana gezinti" })).toBeTruthy());
}

describe("App shell", () => {
  it("shows the first-run wizard until the shell records first run done", async () => {
    render(<App />);

    expect(await screen.findByRole("heading", { name: "DİVAN'A HOŞ GELDİNİZ" })).toBeTruthy();
    expect(screen.queryByRole("navigation", { name: "Ana gezinti" })).toBeNull();
  });

  it("offers exactly the seven Patron destinations, in order, opening on TAHT", async () => {
    await renderShell();

    const nav = screen.getByRole("navigation", { name: "Ana gezinti" });
    const labels = within(nav)
      .getAllByRole("button")
      .map((button) => button.textContent?.trim());
    expect(labels).toEqual([
      "👑 TAHT",
      "🏛 DİVAN",
      "⚔ EKİP",
      "🕵 TEFTİŞ",
      "🧠 ARŞİV",
      "🧰 CEPHANELİK",
      "🩺 SİSTEM",
    ]);
    expect(within(nav).getByRole("button", { name: "👑 TAHT" }).className).toContain("active");
    expect(await screen.findByRole("heading", { name: "Patron Masası" })).toBeTruthy();
  });

  it("keeps the shell depth control and hides paths at the Patron depth", async () => {
    await renderShell();

    const depth = screen.getByRole("group", { name: "Ayrıntı düzeyi" });
    expect(within(depth).getAllByRole("button").map((b) => b.textContent)).toEqual([
      "Patron",
      "Divan",
      "Teknik",
    ]);
    // Wait until the project list is in, then assert the path is not shown.
    await screen.findAllByText("vaka-sistemi");
    expect(screen.queryByText(PROJECT_ROOT)).toBeNull();

    fireEvent.click(within(depth).getByRole("button", { name: "Teknik" }));
    expect((await screen.findAllByText(PROJECT_ROOT)).length).toBeGreaterThan(0);
  });

  it("renders the Patron summary from the Core status only", async () => {
    await renderShell();

    const summary = await screen.findByRole("region", { name: "Proje özeti" });
    expect(within(summary).getByText("Geliştirme sürüyor")).toBeTruthy();
    expect(within(summary).getByText("8 işin 5 tanesi tamamlandı.")).toBeTruthy();
    expect(within(summary).getByText("Sizi bekleyen")).toBeTruthy();
    // Not in the payload, so not on the screen.
    expect(within(summary).queryByText("Çalışan ajan")).toBeNull();
    expect(within(summary).queryByText("Son olay")).toBeNull();
  });

  it("shows only the memory doctor lines on ARŞİV", async () => {
    await renderShell();

    fireEvent.click(screen.getByRole("button", { name: "🧠 ARŞİV" }));
    expect(await screen.findByText("✓ Hafıza deposu hazır.")).toBeTruthy();
    expect(screen.getByText("⚠ Hafıza geri çağırma kurulu ancak hafıza okunamadı.")).toBeTruthy();
    expect(screen.queryByText(/MEMORY_STORE_UNREADABLE/)).toBeNull();
  });

  it("puts the Doctor behind SİSTEM and keeps releases reachable from it", async () => {
    await renderShell();

    fireEvent.click(screen.getByRole("button", { name: "🩺 SİSTEM" }));
    expect(await screen.findByRole("heading", { name: "Sistem durumu" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Sürümler ve güncelleme" }));
    expect(await screen.findByText(/SÜRÜMLER \/ GÜNCELLEME/)).toBeTruthy();
  });

  it("keeps the plugin trust center reachable under CEPHANELİK", async () => {
    await renderShell();

    fireEvent.click(screen.getByRole("button", { name: "🧰 CEPHANELİK" }));
    expect(await screen.findByRole("button", { name: "Eklentiler" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Yönetilen araçlar" }));
    expect(await screen.findByText("Bilgisayarda bulunan araçlar")).toBeTruthy();
    expect(screen.queryByText("C:/divan-tools/codex.cmd")).toBeNull();
  });
});
