import { useEffect, useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";

type ToolStatus = { id: string; available: boolean; path: string | null; required: boolean };
type RuntimeProbe = { ready: boolean; tools: ToolStatus[] };
type Capabilities = { product: string; apiVersion: number; shell: string; features: string[] };
type CoreEnvelope<T> = {
  api_version: number;
  ok: boolean;
  result?: T;
  error?: { code: string; message: string };
};
type CoreTask = {
  task_id: string;
  title: string;
  state: string;
  project_root: string | null;
  engine_id: string | null;
  mandate_id: string | null;
  metadata: Record<string, unknown>;
};

type UiState = "PLAN" | "WORKING" | "REVIEW" | "PASS" | "APPROVAL";

const stateMap: Record<string, UiState> = {
  draft: "PLAN",
  planned: "PLAN",
  running: "WORKING",
  review: "REVIEW",
  passed: "PASS",
  retry: "WORKING",
  blocked: "REVIEW",
  approval: "APPROVAL",
  merged: "PASS",
  released: "PASS",
  cancelled: "REVIEW",
};

async function coreRequest<T>(request: Record<string, unknown>): Promise<T> {
  const raw = await invoke<string>("core_request", { request: JSON.stringify(request) });
  const envelope = JSON.parse(raw) as CoreEnvelope<T>;
  if (!envelope.ok || envelope.result === undefined) {
    throw new Error(envelope.error ? `${envelope.error.code}: ${envelope.error.message}` : "Divan Core isteği başarısız");
  }
  return envelope.result;
}

function App() {
  const [probe, setProbe] = useState<RuntimeProbe | null>(null);
  const [caps, setCaps] = useState<Capabilities | null>(null);
  const [tasks, setTasks] = useState<CoreTask[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const refreshTasks = async () => {
    const result = await coreRequest<CoreTask[]>({ command: "task.list" });
    setTasks(result);
    setSelectedId((current) => current ?? result[0]?.task_id ?? null);
  };

  useEffect(() => {
    Promise.all([
      invoke<RuntimeProbe>("runtime_probe"),
      invoke<Capabilities>("divan_capabilities"),
      refreshTasks(),
    ])
      .then(([runtime, capabilities]) => {
        setProbe(runtime);
        setCaps(capabilities);
      })
      .catch((value: unknown) => setError(String(value)));
  }, []);

  const selected = useMemo(
    () => tasks.find((task) => task.task_id === selectedId) ?? tasks[0] ?? null,
    [tasks, selectedId],
  );
  const readyCount = useMemo(
    () => probe?.tools.filter((tool) => tool.available).length ?? 0,
    [probe],
  );

  const createTask = async () => {
    const title = window.prompt("Yeni görevin adı");
    if (!title?.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const created = await coreRequest<CoreTask>({ command: "task.create", title: title.trim() });
      await refreshTasks();
      setSelectedId(created.task_id);
    } catch (value) {
      setError(String(value));
    } finally {
      setCreating(false);
    }
  };

  const selectedState = selected ? stateMap[selected.state] ?? "PLAN" : "PLAN";
  const worker = selected?.engine_id ?? "Henüz atanmadı";

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand"><span className="seal">D</span><strong>DİVAN</strong></div>
        <div className="project-pill">{selected?.project_root ?? "Proje seçilmedi"}</div>
        <div className="engine-pill"><span className="dot" /> Core {probe?.ready ? "hazır" : "kontrol ediliyor"}</div>
      </header>

      <aside className="sidebar">
        <nav>
          {['Projeler', 'Görevler', 'Ajanlar', 'Kanıtlar', 'Sürümler', 'Ayarlar'].map((item, index) => (
            <button className={index === 1 ? 'nav-item active' : 'nav-item'} key={item}>{item}</button>
          ))}
        </nav>
        <section className="runtime-card">
          <span className="eyebrow">ÇALIŞMA ORTAMI</span>
          <strong>{readyCount}/{probe?.tools.length ?? 5} araç bulundu</strong>
          {probe?.tools.map((tool) => (
            <div className="tool-row" key={tool.id}>
              <span>{tool.id}</span><span className={tool.available ? 'ok' : 'muted'}>{tool.available ? '●' : '○'}</span>
            </div>
          ))}
        </section>
      </aside>

      <section className="workspace">
        <div className="section-heading">
          <div><span className="eyebrow">AKTİF GÖREVLER</span><h1>Yazılım ekibi</h1></div>
          <button className="primary" disabled={creating} onClick={createTask}>{creating ? "Oluşturuluyor…" : "+ Yeni görev"}</button>
        </div>
        {tasks.length > 0 ? (
          <div className="task-grid">
            {tasks.map((task) => {
              const uiState = stateMap[task.state] ?? "PLAN";
              return (
                <button key={task.task_id} className={selected?.task_id === task.task_id ? 'task-card selected' : 'task-card'} onClick={() => setSelectedId(task.task_id)}>
                  <span className="task-id">{task.task_id}</span>
                  <strong>{task.title}</strong>
                  <div className="task-meta"><span>{task.engine_id ?? 'Motor bekliyor'}</span><span className={`state ${uiState.toLowerCase()}`}>{uiState}</span></div>
                </button>
              );
            })}
          </div>
        ) : (
          <section className="terminal-panel empty-state">
            <span className="eyebrow">BAŞLAMAYA HAZIR</span>
            <h2>Henüz görev yok</h2>
            <p>“Yeni görev” ile Divan Core içinde kalıcı ilk görevi oluştur.</p>
          </section>
        )}

        {selected && (
          <>
            <section className="pipeline">
              {['PLAN', 'WORKING', 'REVIEW', 'PASS', 'APPROVAL'].map((step) => (
                <div key={step} className={step === selectedState ? 'pipeline-step current' : 'pipeline-step'}>{step}</div>
              ))}
            </section>
            <section className="terminal-panel">
              <div className="tabs"><button className="active-tab">Özet</button><button>Diff</button><button>Terminal</button><button>Testler</button></div>
              <div className="summary-grid">
                <div><span className="eyebrow">EXECUTION ENGINE</span><strong>{worker}</strong></div>
                <div><span className="eyebrow">REVIEWER</span><strong>Atanmayı bekliyor</strong></div>
                <div><span className="eyebrow">CORE STATE</span><strong>{selected.state}</strong></div>
                <div><span className="eyebrow">DIVAN CORE</span><strong>{caps?.apiVersion ? `API v${caps.apiVersion}` : 'bağlanıyor'}</strong></div>
              </div>
            </section>
          </>
        )}
        {error && <p className="error">Runtime hatası: {error}</p>}
      </section>

      <aside className="inspector">
        <span className="eyebrow">ONAY KAPISI</span>
        <h2>{selected?.task_id ?? "Görev seçilmedi"}</h2>
        <p>{selected?.title ?? "Bir görev oluşturduğunda burada gerçek Core durumu ve kanıtları görünecek."}</p>
        <dl>
          <div><dt>Durum</dt><dd>{selected?.state ?? "—"}</dd></div>
          <div><dt>Test</dt><dd>{selectedState === "PASS" || selectedState === "APPROVAL" ? <span className="ok-text">PASS</span> : "Bekliyor"}</dd></div>
          <div><dt>Engine</dt><dd>{selected?.engine_id ?? "Bekliyor"}</dd></div>
          <div><dt>Risk</dt><dd>Hesaplanacak</dd></div>
          <div><dt>Mandate</dt><dd>{selected?.mandate_id ? "Var" : "Gerekli"}</dd></div>
        </dl>
        <button className="secondary" disabled={!selected}>Değişiklikleri incele</button>
        <button className="approve" disabled={selectedState !== 'APPROVAL'}>Bir kez onayla</button>
        <small>Merge/release yalnız PASS + açık kullanıcı onayı + mandate ile açılır.</small>
      </aside>
    </main>
  );
}

export default App;
