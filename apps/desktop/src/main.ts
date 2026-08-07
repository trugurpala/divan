import { invoke } from "@tauri-apps/api/core";
import "./styles.css";

type ToolProbe = {
  id: string;
  label: string;
  available: boolean;
  detail: string;
};

type HealthSnapshot = {
  schema_version: number;
  status: string;
  tools: ToolProbe[];
};

type JsonRecord = Record<string, unknown>;

const app = document.querySelector<HTMLDivElement>("#app");
if (!app) throw new Error("#app root is missing");

app.innerHTML = `
  <div class="app-shell">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark">D</div>
        <div class="brand-copy"><strong>DİVAN</strong><span>AI Yazılım Kumanda Merkezi</span></div>
      </div>
      <div class="top-context">
        <span>Proje <strong id="top-project">seçilmedi</strong></span>
        <span>Hedef <strong id="top-goal">—</strong></span>
      </div>
      <div class="engine-pill"><span id="engine-dot" class="dot pending"></span><span id="engine-label">Orca kontrol edilmedi</span></div>
    </header>

    <div class="workspace">
      <aside class="sidebar">
        <div class="nav-label">Çalışma Alanı</div>
        <button class="nav-item active"><span class="nav-icon">◫</span>Projeler</button>
        <button class="nav-item"><span class="nav-icon">✓</span>Görevler</button>
        <button class="nav-item"><span class="nav-icon">◎</span>Ajanlar</button>
        <button class="nav-item"><span class="nav-icon">◇</span>Kanıtlar</button>
        <button class="nav-item"><span class="nav-icon">↗</span>Sürümler</button>
        <div class="nav-label" style="margin-top:18px">Sistem</div>
        <button class="nav-item"><span class="nav-icon">⚙</span>Ayarlar</button>
        <div class="sidebar-footer">Divan Core kaynak otoritedir.<br/>Execution engine değiştirilebilir.</div>
      </aside>

      <main class="main">
        <div class="section-heading">
          <div><h1>Kontrol Merkezi</h1><p>Projeyi seç, hedefi planla ve makinedeki ajan altyapısını doğrula.</p></div>
          <div class="toolbar"><button id="scan-tools" class="button">Makineyi Tara</button></div>
        </div>

        <div class="pipeline">
          <div class="pipeline-step pass"><span class="state">01</span><strong>PLAN</strong></div>
          <div class="pipeline-step current"><span class="state">02</span><strong>WORKING</strong></div>
          <div class="pipeline-step"><span class="state">03</span><strong>REVIEW</strong></div>
          <div class="pipeline-step"><span class="state">04</span><strong>PASS / RETRY</strong></div>
          <div class="pipeline-step"><span class="state">05</span><strong>RELEASE</strong></div>
        </div>

        <div class="grid two">
          <section class="card">
            <div class="card-header"><div><div class="card-title">Proje</div><div class="card-subtitle">Divan Project Contract durumunu oku</div></div></div>
            <div class="card-body">
              <div class="field"><label for="project-path">Proje klasörü</label><input id="project-path" class="input" placeholder="C:\\Projeler\\uygulamam" autocomplete="off" /></div>
              <div class="toolbar"><button id="read-project" class="button primary">Projeyi Oku</button></div>
              <div id="project-status-line" class="status-line"></div>
            </div>
          </section>

          <section class="card">
            <div class="card-header"><div><div class="card-title">Yeni Hedef</div><div class="card-subtitle">Önce plan üretir; dosya yazmaz</div></div></div>
            <div class="card-body">
              <div class="field"><label for="goal-intent">Ne yapılacak?</label><textarea id="goal-intent" class="textarea" placeholder="Login hatasını bul, testini yaz ve release'e hazırla."></textarea></div>
              <div class="field"><label for="goal-target">Hedef kapısı</label><select id="goal-target" class="select"><option value="verified">Verified</option><option value="previewed">Previewed</option><option value="released">Released</option><option value="observed">Observed</option></select></div>
              <button id="plan-goal" class="button primary">Planla</button>
              <div id="goal-status-line" class="status-line"></div>
            </div>
          </section>
        </div>

        <div class="grid two" style="margin-top:14px">
          <section class="card">
            <div class="card-header"><div><div class="card-title">Makine Hazırlığı</div><div class="card-subtitle">Gerçek CLI process probe</div></div></div>
            <div class="card-body"><div id="tool-list" class="tool-list"><div class="empty-state">Henüz taranmadı.</div></div></div>
          </section>

          <section class="card">
            <div class="card-header"><div><div class="card-title">Divan JSON</div><div class="card-subtitle">Desktop için stabil çekirdek sözleşmesi</div></div></div>
            <div class="card-body"><pre id="json-view" class="json-view">Henüz proje veya hedef okunmadı.</pre></div>
          </section>
        </div>
      </main>

      <aside class="inspector">
        <h2>Onay Kapısı</h2>
        <p>Mutasyonlar owner mandate olmadan çalıştırılmaz. Bu alpha ekranı yalnız okuma ve planlama yapar.</p>
        <div class="approval">
          <div class="approval-row"><span>Repository</span><strong id="approval-project">—</strong></div>
          <div class="approval-row"><span>Goal</span><strong id="approval-goal">—</strong></div>
          <div class="approval-row"><span>Engine</span><strong>Orca Sidecar</strong></div>
          <div class="approval-row"><span>Yetki</span><strong>Bekliyor</strong></div>
          <div class="approval-row"><span>Risk</span><strong>Henüz hesaplanmadı</strong></div>
          <div class="approval-actions"><button class="button danger" disabled>Reddet</button><button class="button primary" disabled>Bir kez onayla</button></div>
        </div>
        <p style="margin-top:14px">Alpha'da mutasyon butonları bilinçli olarak kapalıdır. Bir sonraki kapı governed execution coordinator'a bağlanır.</p>
      </aside>
    </div>
  </div>
`;

const byId = <T extends HTMLElement>(id: string): T => {
  const element = document.getElementById(id);
  if (!element) throw new Error(`#${id} is missing`);
  return element as T;
};

const projectPath = byId<HTMLInputElement>("project-path");
const intentInput = byId<HTMLTextAreaElement>("goal-intent");
const targetInput = byId<HTMLSelectElement>("goal-target");
const jsonView = byId<HTMLPreElement>("json-view");
const toolList = byId<HTMLDivElement>("tool-list");
const engineDot = byId<HTMLSpanElement>("engine-dot");
const engineLabel = byId<HTMLSpanElement>("engine-label");

function setLine(id: string, message: string, kind: "" | "error" | "success" = ""): void {
  const element = byId<HTMLDivElement>(id);
  element.textContent = message;
  element.className = `status-line ${kind}`.trim();
}

function renderJson(value: unknown): void {
  jsonView.textContent = JSON.stringify(value, null, 2);
}

function shortProject(value: string): string {
  const normalized = value.replace(/[\\/]+$/, "");
  const parts = normalized.split(/[\\/]/);
  return parts.at(-1) || value || "seçilmedi";
}

function updateProjectContext(project: string, goal = "—"): void {
  byId<HTMLElement>("top-project").textContent = shortProject(project);
  byId<HTMLElement>("approval-project").textContent = shortProject(project);
  byId<HTMLElement>("top-goal").textContent = goal;
  byId<HTMLElement>("approval-goal").textContent = goal;
}

function renderTools(snapshot: HealthSnapshot): void {
  toolList.replaceChildren();
  for (const tool of snapshot.tools) {
    const row = document.createElement("div");
    row.className = "tool-row";
    const info = document.createElement("div");
    const name = document.createElement("div");
    name.className = "tool-name";
    const dot = document.createElement("span");
    dot.className = `dot ${tool.available ? "ready" : "missing"}`;
    name.append(dot, document.createTextNode(tool.label));
    const detail = document.createElement("div");
    detail.className = "tool-detail";
    detail.textContent = tool.detail || (tool.available ? "hazır" : "bulunamadı");
    info.append(name, detail);
    const badge = document.createElement("span");
    badge.className = `badge ${tool.available ? "ready" : "missing"}`;
    badge.textContent = tool.available ? "Hazır" : "Yok";
    row.append(info, badge);
    toolList.append(row);
  }
  const orca = snapshot.tools.find((tool) => tool.id === "orca");
  engineDot.className = `dot ${orca?.available ? "ready" : "missing"}`;
  engineLabel.textContent = orca?.available ? "Orca Engine hazır" : "Orca Engine yok";
}

async function scanTools(): Promise<void> {
  const button = byId<HTMLButtonElement>("scan-tools");
  button.disabled = true;
  button.textContent = "Taranıyor…";
  try {
    const snapshot = await invoke<HealthSnapshot>("health_check");
    renderTools(snapshot);
  } catch (error) {
    toolList.textContent = `Tarama hatası: ${String(error)}`;
  } finally {
    button.disabled = false;
    button.textContent = "Makineyi Tara";
  }
}

async function readProject(): Promise<void> {
  const project = projectPath.value.trim();
  if (!project) {
    setLine("project-status-line", "Önce proje klasörünü yaz.", "error");
    return;
  }
  setLine("project-status-line", "Okunuyor…");
  try {
    const result = await invoke<JsonRecord>("project_status", { project });
    renderJson(result);
    updateProjectContext(project, typeof result.goal_id === "string" ? result.goal_id : "—");
    setLine("project-status-line", "Proje Divan runtime üzerinden okundu.", "success");
  } catch (error) {
    setLine("project-status-line", String(error), "error");
  }
}

async function planGoal(): Promise<void> {
  const project = projectPath.value.trim();
  const intent = intentInput.value.trim();
  if (!project || !intent) {
    setLine("goal-status-line", "Proje klasörü ve hedef metni gerekli.", "error");
    return;
  }
  setLine("goal-status-line", "Plan hesaplanıyor…");
  try {
    const result = await invoke<JsonRecord>("goal_start_preview", {
      project,
      intent,
      target: targetInput.value,
    });
    renderJson(result);
    const goal = typeof result.goal_id === "string" ? result.goal_id : "plan";
    updateProjectContext(project, goal);
    setLine("goal-status-line", "Plan hazır. Henüz mutasyon yapılmadı.", "success");
  } catch (error) {
    setLine("goal-status-line", String(error), "error");
  }
}

byId<HTMLButtonElement>("scan-tools").addEventListener("click", () => void scanTools());
byId<HTMLButtonElement>("read-project").addEventListener("click", () => void readProject());
byId<HTMLButtonElement>("plan-goal").addEventListener("click", () => void planGoal());

void scanTools();
