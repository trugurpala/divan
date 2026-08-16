import { useState } from "react";

export type CapabilityState =
  | "CERTIFIED"
  | "DEGRADED"
  | "OFFLINE"
  | "INCOMPATIBLE"
  | "BLOCKED";

export type Capability = {
  capability_id: string;
  display_name: string;
  state: CapabilityState;
  affects: string;
  code: string | null;
  detail: string | null;
  evidence: string | null;
  version: string | null;
  usable: boolean;
  /**
   * One plain-language owner action the Core may attach to a capability that
   * is not certified (for example "Codex'te oturum açın"). The Core does not
   * send it yet; the renderer shows it only when present and never writes one.
   */
  action_hint?: string | null;
};

export type DoctorPayload = {
  schema_version: number;
  checked_at: string;
  healthy: boolean;
  capabilities: Capability[];
  blocked_codes: string[];
  unusable_ids: string[];
  human_summary: string[];
};

export type Depth = "padisah" | "divan" | "teknik";

const STATE_LABEL: Record<CapabilityState, string> = {
  CERTIFIED: "hazır",
  DEGRADED: "sınırlı",
  OFFLINE: "kurulu değil",
  INCOMPATIBLE: "uyumsuz",
  BLOCKED: "engelli",
};

/**
 * The health of the machine, told at the depth the reader asked for.
 *
 * Every claim comes from the Core doctor payload. The renderer derives no
 * health of its own, so the CLI and this panel can never disagree.
 *
 * The depth is owned locally unless the shell passes `depth`, in which case
 * the shell-level "Ayrıntı düzeyi" control drives this panel too.
 */
export default function DoctorPanel({
  payload,
  onCheck,
  depth: controlledDepth,
  onDepthChange,
}: {
  payload: DoctorPayload | null;
  onCheck: () => void;
  depth?: Depth;
  onDepthChange?: (depth: Depth) => void;
}) {
  const [localDepth, setLocalDepth] = useState<Depth>("padisah");
  const depth = controlledDepth ?? localDepth;
  const setDepth = (value: Depth) => {
    setLocalDepth(value);
    onDepthChange?.(value);
  };

  return (
    <section className="doctor-panel" aria-labelledby="doctor-title">
      <header>
        <h2 id="doctor-title">Sistem durumu</h2>
        <button type="button" onClick={onCheck}>
          Sistemi kontrol et
        </button>
      </header>

      {payload === null ? (
        <p>Henüz kontrol edilmedi.</p>
      ) : (
        <>
          <div className="doctor-depths" role="tablist" aria-label="Ayrıntı düzeyi">
            {(
              [
                ["padisah", "Padişah"],
                ["divan", "Divan"],
                ["teknik", "Teknik"],
              ] as const
            ).map(([value, label]) => (
              <button
                key={value}
                type="button"
                role="tab"
                id={`doctor-depth-${value}`}
                aria-selected={depth === value}
                aria-controls={`doctor-panel-${value}`}
                onClick={() => setDepth(value)}
              >
                {label}
              </button>
            ))}
          </div>

          {depth === "padisah" && (
            <div
              role="tabpanel"
              id="doctor-panel-padisah"
              aria-labelledby="doctor-depth-padisah"
            >
              <ul>
                {payload.human_summary.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </div>
          )}

          {depth === "divan" && (
            <div
              role="tabpanel"
              id="doctor-panel-divan"
              aria-labelledby="doctor-depth-divan"
            >
              <ul>
                {payload.capabilities.map((item) => (
                  <li key={item.capability_id} data-state={item.state}>
                    <strong>{item.display_name}</strong>
                    <span>{STATE_LABEL[item.state]}</span>
                    {/* What the owner loses, not what the machine lacks. */}
                    {!item.usable && <small>{item.affects}</small>}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {depth === "teknik" && (
            <div
              role="tabpanel"
              id="doctor-panel-teknik"
              aria-labelledby="doctor-depth-teknik"
            >
              <table>
                <thead>
                  <tr>
                    <th scope="col">Yetenek</th>
                    <th scope="col">Durum</th>
                    <th scope="col">Kod</th>
                    <th scope="col">Ayrıntı</th>
                    <th scope="col">Kanıt</th>
                  </tr>
                </thead>
                <tbody>
                  {payload.capabilities.map((item) => (
                    <tr key={item.capability_id}>
                      <td>{item.capability_id}</td>
                      <td>{item.state}</td>
                      <td>{item.code ?? "—"}</td>
                      <td>{item.detail ?? "—"}</td>
                      <td>{item.evidence ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </section>
  );
}
