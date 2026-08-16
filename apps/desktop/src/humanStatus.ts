/**
 * Turn one Core agency status into the six answers a Padişah actually needs.
 *
 * This layer is deliberately pure and derives nothing the Core did not already
 * decide. The renderer must never become a second source of truth, so every
 * field here is a presentation of `project.agency.status`, not a computation
 * over raw task rows.
 */

export type AgencyPhase =
  | "INTAKE"
  | "INTELLIGENCE"
  | "PRODUCT_DEFINITION"
  | "UX_DESIGN"
  | "ARCHITECTURE"
  | "PLAN_REVIEW"
  | "READY_FOR_EXECUTION"
  | "IMPLEMENTATION"
  | "VERIFICATION"
  | "OWNER_DECISION"
  | "DELIVERY_READY"
  | "RELEASED"
  | "MAINTENANCE"
  | "LEARNING"
  | "STAGING_ACCEPTANCE"
  | "BLOCKED";

export type Attention = "none" | "info" | "decision" | "blocked";

export type WorkPackages = {
  total: number;
  completed: number;
  active: number;
  verifying: number;
  blocked: number;
  awaiting_owner: number;
  ready_task_ids: string[];
  state_counts: Record<string, number>;
};

export type AgencyStatus = {
  schema_version: number;
  project: string;
  project_root: string;
  active_goal_id: string | null;
  goal_state: string | null;
  goal_count: number;
  phase: AgencyPhase | string;
  attention: Attention | string;
  execution_authority: string;
  work_packages: WorkPackages;
  state_health: string;
  state_problem?: string | null;
  /**
   * Fields the Patron screen wants but `project.agency.status` does not send
   * yet. They are optional so the renderer shows them only when the Core
   * provides them; nothing here is ever computed on the client.
   */
  agents_working?: number | null;
  critical_problems?: number | null;
  divan_resolving?: number | null;
  last_event?: string | null;
};

/**
 * "Written" and "Ready" are different states and must never render alike.
 * Ready is only ever reached through DELIVERY_READY or RELEASED, which the
 * Core sets after the required gates pass.
 */
export type Readiness = "planning" | "working" | "checking" | "ready" | "blocked";

export type HumanStatus = {
  /** Ne yapılıyor? */
  doing: string;
  /** Ne durumda? */
  progress: string;
  /** Sorun var mı? */
  problem: string | null;
  /** Divan ne yapıyor? */
  divanAction: string;
  /** Benden bir şey gerekiyor mu? */
  ownerAction: string;
  /** Sonraki adım nedir? */
  nextStep: string;
  readiness: Readiness;
  needsOwner: boolean;
};

const PHASE_DOING: Record<string, string> = {
  INTAKE: "Ferman bekleniyor",
  INTELLIGENCE: "Divan konuyu araştırıyor",
  PRODUCT_DEFINITION: "Ne yapılacağı netleştiriliyor",
  UX_DESIGN: "Kullanıcı akışı tasarlanıyor",
  ARCHITECTURE: "Teknik yaklaşım kararlaştırılıyor",
  PLAN_REVIEW: "Plan ikinci gözle denetleniyor",
  READY_FOR_EXECUTION: "Çalışma başlamaya hazır",
  IMPLEMENTATION: "Geliştirme sürüyor",
  VERIFICATION: "Yapılan iş kontrol ediliyor",
  OWNER_DECISION: "Sizin kararınız bekleniyor",
  DELIVERY_READY: "Teslime hazır",
  RELEASED: "Teslim edildi",
  MAINTENANCE: "Bakımda",
  LEARNING: "Divan bu işten ders çıkarıyor",
  STAGING_ACCEPTANCE: "Kabul kontrolünde",
  BLOCKED: "Çalışma durdu",
};

const READY_PHASES = new Set(["DELIVERY_READY", "RELEASED"]);
const CHECKING_PHASES = new Set(["VERIFICATION", "PLAN_REVIEW", "STAGING_ACCEPTANCE"]);
const WORKING_PHASES = new Set(["IMPLEMENTATION", "READY_FOR_EXECUTION", "MAINTENANCE"]);

function readinessOf(status: AgencyStatus): Readiness {
  if (status.attention === "blocked" || status.phase === "BLOCKED") return "blocked";
  if (status.attention === "decision" || status.phase === "OWNER_DECISION") return "blocked";
  // Ready is a Core verdict, never inferred from "all tasks look done".
  if (READY_PHASES.has(String(status.phase))) return "ready";
  if (CHECKING_PHASES.has(String(status.phase))) return "checking";
  if (WORKING_PHASES.has(String(status.phase))) return "working";
  return "planning";
}

function progressOf(packages: WorkPackages): string {
  if (packages.total === 0) return "Henüz iş paketi çıkarılmadı.";
  return `${packages.total} işin ${packages.completed} tanesi tamamlandı.`;
}

function problemOf(status: AgencyStatus): string | null {
  if (status.state_problem) return status.state_problem;
  if (status.state_health !== "healthy") {
    return "Proje durumu doğrulanamadı.";
  }
  if (status.work_packages.blocked > 0) {
    const count = status.work_packages.blocked;
    return count === 1 ? "Bir iş durdu." : `${count} iş durdu.`;
  }
  return null;
}

function divanActionOf(status: AgencyStatus, problem: string | null): string {
  if (status.attention === "blocked" || status.state_health !== "healthy") {
    return "Divan durumu güvenli biçimde durdurdu ve nedeni kaydetti.";
  }
  if (status.attention === "decision") {
    return "Divan gerekli hazırlığı tamamladı ve kararınızı bekliyor.";
  }
  if (problem) {
    return "Divan sorunu tespit etti ve güvenli tekrar denemeyi başlattı.";
  }
  if (status.work_packages.verifying > 0) {
    return "Divan yapılan işi bağımsız olarak kontrol ediyor.";
  }
  if (status.work_packages.active > 0) {
    return "Divan işi çalışanlara dağıttı ve ilerlemeyi izliyor.";
  }
  return "Divan sıradaki adımı hazırlıyor.";
}

function nextStepOf(status: AgencyStatus): string {
  switch (readinessOf(status)) {
    case "blocked":
      return status.attention === "decision"
        ? "Kararınızdan sonra çalışma kaldığı yerden sürer."
        : "Engel kaldırılana kadar çalışma beklemede.";
    case "ready":
      return "Teslim alınabilir.";
    case "checking":
      return "Kontroller bitince sonuç size bildirilecek.";
    case "working":
      return status.work_packages.ready_task_ids.length > 0
        ? "Sıradaki iş paketleri başlatılacak."
        : "Süren işler tamamlanacak.";
    default:
      return "Plan hazırlandıktan sonra çalışma başlayacak.";
  }
}

export function presentAgencyStatus(status: AgencyStatus): HumanStatus {
  const problem = problemOf(status);
  const needsOwner =
    status.attention === "decision" || status.work_packages.awaiting_owner > 0;
  return {
    doing: PHASE_DOING[String(status.phase)] ?? "Çalışma sürüyor",
    progress: progressOf(status.work_packages),
    problem,
    divanAction: divanActionOf(status, problem),
    ownerAction: needsOwner
      ? "Bir karar sizi bekliyor."
      : "Sizden işlem beklenmiyor.",
    nextStep: nextStepOf(status),
    readiness: readinessOf(status),
    needsOwner,
  };
}

const READINESS_LABEL: Record<Readiness, string> = {
  planning: "Planlanıyor",
  working: "Yapılıyor",
  checking: "Kontrol ediliyor",
  ready: "Hazır",
  blocked: "Beklemede",
};

export function readinessLabel(readiness: Readiness): string {
  return READINESS_LABEL[readiness];
}

/** The plain-language name of a Core phase; unknown phases stay generic. */
export function phaseLabel(phase: AgencyPhase | string): string {
  return PHASE_DOING[String(phase)] ?? "Çalışma sürüyor";
}

export type PatronField = {
  id: string;
  label: string;
  value: string;
};

function countValue(value: number | null | undefined): string | null {
  return typeof value === "number" && Number.isFinite(value) ? String(value) : null;
}

/**
 * The Patron screen as an ordered list of label/value pairs.
 *
 * Only fields the Core payload actually carries are returned. Optional fields
 * (`agents_working`, `critical_problems`, `divan_resolving`, `last_event`) are
 * omitted when absent instead of being estimated from other numbers, so the
 * screen never shows a figure the Core did not compute.
 */
export function patronSummary(status: AgencyStatus): PatronField[] {
  const human = presentAgencyStatus(status);
  const packages = status.work_packages;
  const fields: Array<PatronField | null> = [
    { id: "project", label: "Proje", value: status.project },
    { id: "phase", label: "Aşama", value: phaseLabel(status.phase) },
    { id: "progress", label: "İlerleme", value: human.progress },
    { id: "activity", label: "Şu an", value: human.divanAction },
    { id: "active", label: "Çalışan iş paketi", value: String(packages.active) },
    optional("agents_working", "Çalışan ajan", countValue(status.agents_working)),
    { id: "blocked", label: "Durmuş iş", value: String(packages.blocked) },
    optional("critical_problems", "Kritik sorun", countValue(status.critical_problems)),
    optional("divan_resolving", "Divan çözüyor", countValue(status.divan_resolving)),
    { id: "awaiting_owner", label: "Sizi bekleyen", value: String(packages.awaiting_owner) },
    optional("last_event", "Son olay", status.last_event?.trim() || null),
    { id: "next_step", label: "Sıradaki adım", value: human.nextStep },
  ];
  return fields.filter((field): field is PatronField => field !== null);
}

function optional(id: string, label: string, value: string | null): PatronField | null {
  return value === null ? null : { id, label, value };
}
