import "./plugin-trust-center.css";

export type PluginIssue = {
  code: string;
  path: string;
  message: string;
};

export type PluginManifestSummary = {
  id: string;
  display_name: string;
  version: string;
  kind: string;
  transport: string;
  executable: string;
  capabilities: string[];
  source_url: string;
  license_expression: string;
  license_evidence: string;
  requires_mandate: boolean;
  mutating: boolean;
};

export type PluginInspection = {
  api_version: number;
  stage: "invalid" | "executable-missing" | "approval-required";
  validation: {
    ok: boolean;
    errors: PluginIssue[];
  };
  manifest: PluginManifestSummary | null;
  artifact: {
    manifest_name: string;
    manifest_sha256: string | null;
    executable_available: boolean;
    executable_name: string | null;
    executable_sha256: string | null;
  };
  activation: {
    supported: boolean;
    reason: string;
  };
};

type TrustCenterProps = {
  inspection: PluginInspection | null;
  busy: boolean;
  onInspect: () => void;
};

const capabilityCopy: Record<string, string> = {
  "project.read": "Proje dosyalarını okuyabilir",
  "project.mutate": "Proje dosyalarını değiştirebilir",
  "git.read": "Git durumunu okuyabilir",
  "git.mutate": "Git üzerinde değişiklik yapabilir",
  "process.spawn": "Yerel süreç başlatabilir",
  "network.outbound": "Dış ağa bağlanabilir",
  "evidence.read": "Kanıtları okuyabilir",
  "evidence.emit": "Yeni kanıt üretebilir",
  "review.read": "Review verisini okuyabilir",
  "provider.read": "Provider verisini okuyabilir",
};

function stageCopy(stage: PluginInspection["stage"]) {
  if (stage === "invalid") {
    return {
      title: "Manifest geçersiz",
      detail: "Divan sözleşmesi geçmedi. Bu eklenti approval aşamasına ilerleyemez.",
      tone: "danger",
    } as const;
  }
  if (stage === "executable-missing") {
    return {
      title: "Manifest geçerli, executable bulunamadı",
      detail: "Kimlik tamamlanmadan binary hash üretilemez ve approval verilemez.",
      tone: "warning",
    } as const;
  }
  return {
    title: "Doğrulandı, approval gerekli",
    detail: "Manifest ve executable kimliği biliniyor. Bu sürüm yine de eklentiyi çalıştırmaz.",
    tone: "ready",
  } as const;
}

function shortHash(value: string | null) {
  if (!value) return "Yok";
  return `${value.slice(0, 12)}…${value.slice(-12)}`;
}

function capabilityClass(capability: string) {
  return capability.endsWith(".mutate") || capability === "process.spawn"
    ? "plugin-capability elevated"
    : "plugin-capability";
}

export function PluginTrustCenter({ inspection, busy, onInspect }: TrustCenterProps) {
  const status = inspection ? stageCopy(inspection.stage) : null;
  const manifest = inspection?.manifest ?? null;

  return (
    <section className="plugin-trust-center" aria-labelledby="plugin-trust-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">PLUGIN SDK / TRUST CENTER</span>
          <h1 id="plugin-trust-title">Eklenti Güven Merkezi</h1>
        </div>
        <button className="primary" onClick={onInspect} disabled={busy}>
          {busy ? "Doğrulanıyor…" : inspection ? "Başka manifest incele" : "Manifest incele"}
        </button>
      </div>

      <section className="plugin-safety-banner" aria-label="Güvenlik sınırı">
        <div className="plugin-safety-mark" aria-hidden="true">01</div>
        <div>
          <strong>İnceleme sırasında hiçbir üçüncü taraf kodu çalışmaz.</strong>
          <p>
            Divan yalnız seçtiğin JSON manifesti okur, sözleşmeyi doğrular, bare executable
            adını sınırlı yerel resolver ile arar ve SHA-256 kimliğini hesaplar.
          </p>
        </div>
      </section>

      {!inspection ? (
        <section className="plugin-empty-state">
          <div className="plugin-flow" aria-label="Plugin doğrulama akışı">
            <article>
              <span>1</span>
              <strong>Manifest seç</strong>
              <p>Yalnız senin açıkça seçtiğin bir JSON dosyası okunur.</p>
            </article>
            <article>
              <span>2</span>
              <strong>Divan doğrulasın</strong>
              <p>Kaynak, lisans, yetkiler, mandate kuralı ve executable kimliği kontrol edilir.</p>
            </article>
            <article>
              <span>3</span>
              <strong>Kararı gör</strong>
              <p>Valid olmak approval veya enable olmak değildir; her state ayrı gösterilir.</p>
            </article>
          </div>
          <p className="plugin-empty-note">
            Bu SDK diliminde Install / Enable / Run yok. Önce trust contract doğrulanıyor.
          </p>
        </section>
      ) : (
        <div className="plugin-report" aria-live="polite">
          <section className={`plugin-status ${status?.tone ?? "warning"}`}>
            <div>
              <span className="eyebrow">CURRENT TRUST STATE</span>
              <strong>{status?.title}</strong>
              <p>{status?.detail}</p>
            </div>
            <span className="plugin-stage-code">{inspection.stage}</span>
          </section>

          <div className="plugin-metrics">
            <article>
              <span className="eyebrow">MANIFEST</span>
              <strong>{inspection.validation.ok ? "Sözleşme geçti" : "Bloklandı"}</strong>
              <small>{inspection.artifact.manifest_name}</small>
            </article>
            <article>
              <span className="eyebrow">EXECUTABLE</span>
              <strong>{inspection.artifact.executable_available ? "Kimliği biliniyor" : "Bulunamadı"}</strong>
              <small>{inspection.artifact.executable_name ?? manifest?.executable ?? "—"}</small>
            </article>
            <article>
              <span className="eyebrow">MUTATION</span>
              <strong>{manifest?.mutating ? "Değişiklik yapabilir" : "Read-only"}</strong>
              <small>{manifest?.requires_mandate ? "Divan mandate zorunlu" : "Mutation yetkisi yok"}</small>
            </article>
          </div>

          {manifest && (
            <div className="plugin-detail-grid">
              <section className="plugin-detail-section">
                <div className="plugin-section-title">
                  <span className="eyebrow">IDENTITY</span>
                  <strong>{manifest.display_name}</strong>
                </div>
                <dl className="plugin-kv">
                  <div><dt>ID</dt><dd><code>{manifest.id}</code></dd></div>
                  <div><dt>Sürüm</dt><dd>{manifest.version}</dd></div>
                  <div><dt>Tür</dt><dd>{manifest.kind}</dd></div>
                  <div><dt>Transport</dt><dd>{manifest.transport}</dd></div>
                  <div><dt>Executable</dt><dd><code>{manifest.executable}</code></dd></div>
                </dl>
              </section>

              <section className="plugin-detail-section">
                <div className="plugin-section-title">
                  <span className="eyebrow">SOURCE / LICENSE</span>
                  <strong>Provenance</strong>
                </div>
                <dl className="plugin-kv">
                  <div><dt>Lisans</dt><dd>{manifest.license_expression}</dd></div>
                  <div className="plugin-kv-stack"><dt>Kaynak</dt><dd><code>{manifest.source_url}</code></dd></div>
                  <div className="plugin-kv-stack"><dt>Lisans kanıtı</dt><dd><code>{manifest.license_evidence}</code></dd></div>
                </dl>
              </section>
            </div>
          )}

          {manifest && (
            <section className="plugin-detail-section plugin-capability-section">
              <div className="plugin-section-title">
                <span className="eyebrow">REQUESTED CAPABILITIES</span>
                <strong>{manifest.capabilities.length} yetki beyanı</strong>
              </div>
              <div className="plugin-capabilities">
                {manifest.capabilities.map((capability) => (
                  <div className={capabilityClass(capability)} key={capability}>
                    <code>{capability}</code>
                    <span>{capabilityCopy[capability] ?? "Divan tarafından tanınan capability"}</span>
                  </div>
                ))}
              </div>
            </section>
          )}

          <section className="plugin-detail-section">
            <div className="plugin-section-title">
              <span className="eyebrow">BYTE IDENTITY</span>
              <strong>SHA-256</strong>
            </div>
            <dl className="plugin-hashes">
              <div>
                <dt>Manifest</dt>
                <dd title={inspection.artifact.manifest_sha256 ?? undefined}>
                  <code>{shortHash(inspection.artifact.manifest_sha256)}</code>
                </dd>
              </div>
              <div>
                <dt>Executable</dt>
                <dd title={inspection.artifact.executable_sha256 ?? undefined}>
                  <code>{shortHash(inspection.artifact.executable_sha256)}</code>
                </dd>
              </div>
            </dl>
          </section>

          {!inspection.validation.ok && (
            <section className="plugin-detail-section plugin-issues" aria-labelledby="plugin-issues-title">
              <div className="plugin-section-title">
                <span className="eyebrow">VALIDATION ERRORS</span>
                <strong id="plugin-issues-title">{inspection.validation.errors.length} blocker</strong>
              </div>
              <ul>
                {inspection.validation.errors.map((issue) => (
                  <li key={`${issue.code}-${issue.path}`}>
                    <code>{issue.code}</code>
                    <span>{issue.message}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section className="plugin-activation-boundary">
            <span className="eyebrow">ACTIVATION BOUNDARY</span>
            <strong>Bu ekran eklentiyi çalıştırmaz.</strong>
            <p>
              Persistent owner approval ve sidecar execution contract ayrı güvenlik dilimlerinde
              tamamlanmadan Enable/Run yetkisi açılmayacak.
            </p>
          </section>
        </div>
      )}
    </section>
  );
}

export function PluginInspectorRail({
  inspection,
  busy,
  onInspect,
}: TrustCenterProps) {
  if (!inspection) {
    return (
      <aside className="inspector plugin-rail" aria-label="Plugin Trust Center özeti">
        <span className="eyebrow">PLUGIN TRUST</span>
        <h2>Henüz manifest seçilmedi</h2>
        <p>Divan yalnız açıkça seçtiğin JSON manifesti inceleyecek; disk taraması yapmayacak.</p>
        <button className="secondary" onClick={onInspect} disabled={busy}>
          Manifest incele
        </button>
        <small>Validasyon, approval değildir. Bu SDK diliminde üçüncü taraf binary çalıştırılmaz.</small>
      </aside>
    );
  }

  const status = stageCopy(inspection.stage);
  const manifest = inspection.manifest;
  return (
    <aside className="inspector plugin-rail" aria-label="Plugin Trust Center özeti">
      <span className="eyebrow">PLUGIN TRUST</span>
      <h2>{manifest?.display_name ?? inspection.artifact.manifest_name}</h2>
      <p>{status.title}</p>
      <dl>
        <div><dt>State</dt><dd>{inspection.stage}</dd></div>
        <div><dt>Manifest</dt><dd>{inspection.validation.ok ? "Valid" : "Invalid"}</dd></div>
        <div><dt>Binary</dt><dd>{inspection.artifact.executable_available ? "Bound" : "Missing"}</dd></div>
        <div><dt>Mutation</dt><dd>{manifest?.mutating ? "Var" : "Yok"}</dd></div>
        <div><dt>Activation</dt><dd>Kapalı</dd></div>
      </dl>
      <button className="secondary" onClick={onInspect} disabled={busy}>
        Başka manifest incele
      </button>
      <small>Manifest veya executable değişirse gelecekteki approval hash bağı nedeniyle geçersiz olur.</small>
    </aside>
  );
}
