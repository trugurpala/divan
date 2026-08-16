import { useState } from "react";

import {
  type AgencyStatus,
  presentAgencyStatus,
  readinessLabel,
} from "./humanStatus";

export type Depth = "padisah" | "divan" | "teknik";

export type TechnicalDetail = {
  provider?: string | null;
  worker?: string | null;
  attempt?: number | null;
  worktree?: string | null;
  exitCode?: number | null;
  diffSha256?: string | null;
  receipt?: string | null;
};

/**
 * One project, told at the depth the reader asked for.
 *
 * Padişah is the default and deliberately carries no technical vocabulary.
 * Nothing here derives state: every claim comes from `project.agency.status`
 * through the pure presenter, so the renderer stays a view.
 */
export default function ProjectStatusCard({
  status,
  technical,
}: {
  status: AgencyStatus;
  technical?: TechnicalDetail;
}) {
  const [depth, setDepth] = useState<Depth>("padisah");
  const human = presentAgencyStatus(status);
  const packages = status.work_packages;

  return (
    <article className="agency-card" aria-labelledby={`project-${status.project}`}>
      <header>
        <h3 id={`project-${status.project}`}>{status.project}</h3>
        <span
          className={`agency-readiness agency-readiness-${human.readiness}`}
          data-readiness={human.readiness}
        >
          {readinessLabel(human.readiness)}
        </span>
      </header>

      <div className="agency-depths" role="tablist" aria-label="Ayrıntı düzeyi">
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
            id={`depth-${value}-${status.project}`}
            aria-selected={depth === value}
            aria-controls={`panel-${value}-${status.project}`}
            onClick={() => setDepth(value)}
          >
            {label}
          </button>
        ))}
      </div>

      {depth === "padisah" && (
        <section
          role="tabpanel"
          id={`panel-padisah-${status.project}`}
          aria-labelledby={`depth-padisah-${status.project}`}
        >
          <p>{human.doing}</p>
          <p>{human.progress}</p>
          {human.problem && <p className="agency-problem">{human.problem}</p>}
          <p>{human.divanAction}</p>
          <p className={human.needsOwner ? "agency-owner-decision" : undefined}>
            {human.ownerAction}
          </p>
          <p>{human.nextStep}</p>
        </section>
      )}

      {depth === "divan" && (
        <section
          role="tabpanel"
          id={`panel-divan-${status.project}`}
          aria-labelledby={`depth-divan-${status.project}`}
        >
          <dl>
            <dt>Aşama</dt>
            <dd>{String(status.phase)}</dd>
            <dt>İş paketi</dt>
            <dd>
              {packages.completed}/{packages.total} tamamlandı, {packages.active} çalışıyor,{" "}
              {packages.verifying} kontrolde, {packages.blocked} durdu
            </dd>
            <dt>Sizi bekleyen</dt>
            <dd>{packages.awaiting_owner}</dd>
            <dt>Aktif ferman</dt>
            <dd>{status.active_goal_id ?? "yok"}</dd>
            <dt>Durum sağlığı</dt>
            <dd>{status.state_health}</dd>
          </dl>
        </section>
      )}

      {depth === "teknik" && (
        <section
          role="tabpanel"
          id={`panel-teknik-${status.project}`}
          aria-labelledby={`depth-teknik-${status.project}`}
        >
          <dl>
            <dt>Sağlayıcı</dt>
            <dd>{technical?.provider ?? "—"}</dd>
            <dt>Çalışan</dt>
            <dd>{technical?.worker ?? "—"}</dd>
            <dt>Deneme</dt>
            <dd>{technical?.attempt ?? "—"}</dd>
            <dt>Worktree</dt>
            <dd>{technical?.worktree ?? "—"}</dd>
            <dt>Çıkış kodu</dt>
            <dd>{technical?.exitCode ?? "—"}</dd>
            <dt>Diff</dt>
            <dd>{technical?.diffSha256 ?? "—"}</dd>
            <dt>Makbuz</dt>
            <dd>{technical?.receipt ?? "—"}</dd>
            <dt>Proje yolu</dt>
            <dd>{status.project_root}</dd>
          </dl>
        </section>
      )}
    </article>
  );
}
