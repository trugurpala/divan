import { useState } from "react";
import { open } from "@tauri-apps/plugin-dialog";

import type { Capability, CapabilityState, DoctorPayload } from "./DoctorPanel";

/**
 * The first thing a new owner sees: nine short lines and one folder choice.
 *
 * Every line is a translation of a Core doctor capability. The wizard reads
 * `state` and `code`, picks a glyph and a plain sentence, and stops there. It
 * installs nothing, repairs nothing and never decides a capability is ready
 * when the Core did not say so. When the Core has not attached an owner
 * action, the wizard says Divan will try, and leaves the trying to the Core.
 */

export type WizardStep = {
  id: string;
  title: string;
  /** Doctor capability ids this step reports. Empty for the workspace step. */
  capabilities: readonly string[];
};

export const WIZARD_STEPS: readonly WizardStep[] = [
  { id: "core", title: "Divan Core", capabilities: ["divan-core"] },
  { id: "git", title: "Git", capabilities: ["git"] },
  { id: "codex", title: "Codex", capabilities: ["codex"] },
  { id: "claude", title: "Claude Code", capabilities: ["claude"] },
  { id: "browser", title: "Tarayıcı testi", capabilities: ["browser-qa"] },
  { id: "memory", title: "Hafıza", capabilities: ["memory-store", "memory-recall"] },
  { id: "quality", title: "Kalite ve kanıt", capabilities: ["quality-factory", "evidence"] },
  { id: "security", title: "Yerel güvenlik", capabilities: ["local-state-security"] },
  { id: "workspace", title: "Çalışma klasörü", capabilities: [] },
];

export type LineTone = "ok" | "warn" | "off" | "pending";

export type CapabilityLine = {
  glyph: string;
  sentence: string;
  tone: LineTone;
  /** True when the owner may need to act and the step is not certified. */
  needsAttention: boolean;
};

const DEGRADED_REASON: Record<string, string> = {
  AUTH_REQUIRED: "oturum açılmamış",
  AUTH_NOT_VERIFIED: "oturum doğrulanmadı",
  MEMORY_STORE_UNREADABLE: "hafıza okunamadı",
  BROWSER_BINARY_MISSING: "tarayıcı indirilmemiş",
  BROWSER_PROBE_FAILED: "yoklama tamamlanamadı",
  BROWSER_PROBE_UNREADABLE: "yoklama tamamlanamadı",
};

const WINDOWS_POLICY_CODE = "LOCAL_STATE_DACL_POLICY";

function degradedReason(capability: Capability): string {
  return (capability.code && DEGRADED_REASON[capability.code]) || "sınırlı çalışıyor";
}

/**
 * One Patron sentence for one Core capability. Pure, so the ARŞİV screen and
 * the wizard read the same words for the same payload.
 */
export function capabilityLine(capability: Capability): CapabilityLine {
  const name = capability.display_name;
  const state: CapabilityState = capability.state;
  switch (state) {
    case "CERTIFIED":
      return { glyph: "✓", sentence: `${name} hazır.`, tone: "ok", needsAttention: false };
    case "DEGRADED":
      return {
        glyph: "⚠",
        sentence: `${name} kurulu ancak ${degradedReason(capability)}.`,
        tone: "warn",
        needsAttention: true,
      };
    case "OFFLINE":
      return { glyph: "✗", sentence: `${name} bulunamadı.`, tone: "off", needsAttention: true };
    case "INCOMPATIBLE":
      return { glyph: "⚠", sentence: `${name} uyumsuz sürüm.`, tone: "warn", needsAttention: false };
    case "BLOCKED":
      return {
        glyph: "⚠",
        sentence:
          capability.capability_id === "local-state-security" ||
          capability.code === WINDOWS_POLICY_CODE
            ? `${name} Windows politikası nedeniyle engelli.`
            : `${name} engelli.`,
        tone: "warn",
        needsAttention: false,
      };
  }
}

export function pendingLine(title: string): CapabilityLine {
  return {
    glyph: "…",
    sentence: `${title} henüz kontrol edilmedi.`,
    tone: "pending",
    needsAttention: false,
  };
}

/** The owner action for a step that is not certified, in the Core's words or Divan's promise. */
export function ownerActionFor(capability: Capability): string | null {
  if (capability.state !== "DEGRADED" && capability.state !== "OFFLINE") return null;
  const hint = capability.action_hint?.trim();
  return hint ? hint : "Divan bunu kendisi hazırlamayı deneyecek.";
}

function findCapability(doctor: DoctorPayload | null, id: string): Capability | null {
  return doctor?.capabilities.find((item) => item.capability_id === id) ?? null;
}

async function pickWorkspaceWithDialog(): Promise<string | null> {
  const folder = await open({
    directory: true,
    multiple: false,
    title: "Divan'ın çalışacağı proje klasörünü seç",
  });
  return typeof folder === "string" && folder.trim() ? folder.trim() : null;
}

export default function FirstRunWizard({
  doctor,
  onComplete,
  onCheck,
  pickWorkspace = pickWorkspaceWithDialog,
  notice = null,
}: {
  doctor: DoctorPayload | null;
  /** Called once with the chosen folder; the parent persists "first run done". */
  onComplete: (workspacePath: string) => void;
  /** Re-run the Core doctor. Optional so the wizard can render from a snapshot. */
  onCheck?: () => void;
  /** Injectable folder picker; defaults to the Tauri dialog. */
  pickWorkspace?: () => Promise<string | null>;
  /** A plain message from the parent, for example when the folder was refused. */
  notice?: string | null;
}) {
  const [current, setCurrent] = useState(0);
  const [showTechnical, setShowTechnical] = useState(false);
  const [picking, setPicking] = useState(false);
  const [pickError, setPickError] = useState<string | null>(null);

  const lastIndex = WIZARD_STEPS.length - 1;
  const step = WIZARD_STEPS[current];
  const stepCapabilities = step.capabilities.map((id) => ({
    id,
    capability: findCapability(doctor, id),
  }));

  const goTo = (index: number) => {
    setCurrent(Math.min(Math.max(index, 0), lastIndex));
    setShowTechnical(false);
  };

  const chooseWorkspace = async () => {
    setPicking(true);
    setPickError(null);
    try {
      const folder = await pickWorkspace();
      if (folder) onComplete(folder);
    } catch (value) {
      setPickError(String(value));
    } finally {
      setPicking(false);
    }
  };

  return (
    <section className="first-run" aria-labelledby="first-run-title">
      <header className="first-run-header">
        <span className="eyebrow">İLK KURULUM</span>
        <h1 id="first-run-title">DİVAN'A HOŞ GELDİNİZ</h1>
        <p>
          Divan bilgisayarınızda ne bulduğunu dokuz kısa satırda söyler; sonra yalnız sizin
          seçtiğiniz klasörde çalışır.
        </p>
      </header>

      <ol className="first-run-steps" aria-label="Kurulum adımları">
        {WIZARD_STEPS.map((item, index) => {
          const isCurrent = index === current;
          const lines = item.capabilities.map((id) => {
            const capability = findCapability(doctor, id);
            return {
              key: id,
              line: capability ? capabilityLine(capability) : pendingLine(item.title),
            };
          });
          return (
            <li
              key={item.id}
              className={isCurrent ? "first-run-step current" : "first-run-step"}
              aria-current={isCurrent ? "step" : undefined}
              data-step={item.id}
            >
              <span className="first-run-index">{index + 1}</span>
              <div className="first-run-copy">
                <strong>{item.title}</strong>
                {item.id === "workspace" ? (
                  <span className="wizard-line" data-tone="pending">
                    Divan yalnız seçtiğiniz klasörde çalışır.
                  </span>
                ) : (
                  lines.map(({ key, line }) => (
                    <span key={key} className="wizard-line" data-tone={line.tone}>
                      {`${line.glyph} ${line.sentence}`}
                    </span>
                  ))
                )}
              </div>
            </li>
          );
        })}
      </ol>

      <section className="first-run-detail" aria-live="polite">
        <span className="eyebrow">
          Adım {current + 1} / {WIZARD_STEPS.length} · {step.title}
        </span>

        {step.id === "workspace" ? (
          <>
            <p>
              Çalışma klasörünüzü seçin. Divan tüm diski taramaz; yalnız bu klasörü kaydeder ve
              yalnız onun içinde çalışır.
            </p>
            {pickError && <p className="error">Klasör seçilemedi. Yeniden deneyin.</p>}
            {notice && <p className="error">{notice}</p>}
            <div className="action-row">
              <button type="button" className="secondary" onClick={() => goTo(current - 1)}>
                Geri
              </button>
              <button
                type="button"
                className="primary"
                onClick={() => void chooseWorkspace()}
                disabled={picking}
              >
                {picking ? "Klasör bekleniyor…" : "Klasör seç"}
              </button>
            </div>
          </>
        ) : (
          <>
            {stepCapabilities.map(({ id, capability }) => {
              const action = capability ? ownerActionFor(capability) : null;
              return action ? (
                <p key={id} className="wizard-action">
                  {action}
                </p>
              ) : null;
            })}
            {stepCapabilities.every(({ capability }) => capability === null) && (
              <p className="muted-copy">
                Bu adım henüz kontrol edilmedi.
                {onCheck ? " Aşağıdan yeniden kontrol edebilirsiniz." : ""}
              </p>
            )}

            <button
              type="button"
              className="text-button"
              aria-expanded={showTechnical}
              onClick={() => setShowTechnical((value) => !value)}
            >
              Teknik ayrıntı
            </button>
            {showTechnical && (
              <dl className="wizard-technical">
                {stepCapabilities.map(({ id, capability }) => (
                  <div key={id}>
                    <dt>{id}</dt>
                    <dd>
                      {capability
                        ? [capability.state, capability.code, capability.detail]
                            .filter((part): part is string => Boolean(part))
                            .join(" · ")
                        : "kontrol edilmedi"}
                    </dd>
                  </div>
                ))}
              </dl>
            )}

            <div className="action-row">
              {current > 0 && (
                <button type="button" className="secondary" onClick={() => goTo(current - 1)}>
                  Geri
                </button>
              )}
              {onCheck && (
                <button type="button" className="secondary" onClick={onCheck}>
                  Yeniden kontrol et
                </button>
              )}
              <button type="button" className="primary" onClick={() => goTo(current + 1)}>
                Devam
              </button>
            </div>
          </>
        )}
      </section>
    </section>
  );
}
