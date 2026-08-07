import { useEffect, useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";

type ToolStatus = { id: string; available: boolean; path: string | null; required: boolean };
type RuntimeProbe = { ready: boolean; tools: ToolStatus[] };
type Capabilities = { product: string; apiVersion: number; shell: string; features: string[] };

type Task = {
  id: string;
  title: string;
  state: "PLAN" | "WORKING" | "REVIEW" | "PASS" | "APPROVAL";
  worker: string;
  reviewer: string;
  files: number;
};

const tasks: Task[] = [
  { id: "DIV-104", title: "Login akışını düzelt ve test et", state: "WORKING", worker: "Codex", reviewer: "Claude", files: 7 },
  { id: "DIV-103", title: "Release kanıtlarını doğrula", state: "REVIEW", worker: "Claude", reviewer: "Codex", files: 3 },
  { id: "DIV-102", title: "Engine registry migration", state: "PASS", worker: "Codex", reviewer: "Claude", files: 5 },
];

function App() {
  const [probe, setProbe] = useState<RuntimeProbe | null>(null);
  const [caps, setCaps] = useState<Capabilities | null>(null);
  const [selected, setSelected] = useState(tasks[0]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      invoke<RuntimeProbe>("runtime_probe"),
      invoke<Capabilities>("divan_capabilities"),
    ])
      .then(([runtime, capabilities]) => {
        setProbe(runtime);
        setCaps(capabilities);
      })
      .catch((value: unknown) => setError(String(value)));
  }, []);

  const readyCount = useMemo(
    () => probe?.tools.filter((tool) => tool.available).length ?? 0,
    [probe],
  );

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand"><span className="seal">D</span><strong>DİVAN</strong></div>
        <div className="project-pill">Divan / main</div>
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
          <button className="primary">+ Yeni görev</button>
        </div>
        <div className="task-grid">
          {tasks.map((task) => (
            <button key={task.id} className={selected.id === task.id ? 'task-card selected' : 'task-card'} onClick={() => setSelected(task)}>
              <span className="task-id">{task.id}</span>
              <strong>{task.title}</strong>
              <div className="task-meta"><span>{task.worker}</span><span>{task.files} dosya</span><span className={`state ${task.state.toLowerCase()}`}>{task.state}</span></div>
            </button>
          ))}
        </div>
        <section className="pipeline">
          {['PLAN', 'WORKING', 'REVIEW', 'PASS', 'APPROVAL'].map((step) => (
            <div key={step} className={step === selected.state ? 'pipeline-step current' : 'pipeline-step'}>{step}</div>
          ))}
        </section>
        <section className="terminal-panel">
          <div className="tabs"><button className="active-tab">Özet</button><button>Diff</button><button>Terminal</button><button>Testler</button></div>
          <div className="summary-grid">
            <div><span className="eyebrow">İŞÇİ</span><strong>{selected.worker}</strong></div>
            <div><span className="eyebrow">REVIEWER</span><strong>{selected.reviewer}</strong></div>
            <div><span className="eyebrow">DEĞİŞİKLİK</span><strong>{selected.files} dosya</strong></div>
            <div><span className="eyebrow">DIVAN CORE</span><strong>{caps?.apiVersion ? `API v${caps.apiVersion}` : 'bağlanıyor'}</strong></div>
          </div>
          {error && <p className="error">Runtime hatası: {error}</p>}
        </section>
      </section>

      <aside className="inspector">
        <span className="eyebrow">ONAY KAPISI</span>
        <h2>{selected.id}</h2>
        <p>{selected.title}</p>
        <dl>
          <div><dt>Durum</dt><dd>{selected.state}</dd></div>
          <div><dt>Test</dt><dd className="ok-text">PASS</dd></div>
          <div><dt>Reviewer</dt><dd>Bekleniyor</dd></div>
          <div><dt>Risk</dt><dd>Orta</dd></div>
          <div><dt>Mandate</dt><dd>Gerekli</dd></div>
        </dl>
        <button className="secondary">Değişiklikleri incele</button>
        <button className="approve" disabled={selected.state !== 'APPROVAL'}>Bir kez onayla</button>
        <small>Merge/release yalnız PASS + açık kullanıcı onayı + mandate ile açılır.</small>
      </aside>
    </main>
  );
}

export default App;
