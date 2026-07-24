# Üçüncü Taraf Lisansları / Third-Party Licenses

Bu derleme aşağıdaki açık kaynak projelerden seçilmiş skill'ler içerir. Lisans
metinleri ilgili paket veya skill klasörlerinde korunur. Derleme tarihi:
2026-07-19. Genel bildirim ve marka notları `NOTICE.md` içindedir.

| Paket / içerik | Skill sayısı | Kaynak | Lisans ve yerel metin |
|---|---:|---|---|
| core-pack / Superpowers | 13 | https://github.com/obra/superpowers | MIT — `plugins/core-pack/LICENSE-superpowers-MIT.txt` |
| core-pack / Kural Hazinesi | 1 (9 referans) | https://github.com/PatrickJS/awesome-cursorrules | CC0-1.0 — upstream `LICENSE` |
| core-pack / Bağlam Muhafızı kaynak fikirleri | 1 | https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering | MIT — `plugins/core-pack/skills/baglam-muhafizi/LICENSE.txt` |
| ui-pack / frontend-design, webapp-testing | 2 | https://github.com/anthropics/skills | Apache-2.0 — her skill'in `LICENSE.txt` dosyası |
| ui-pack / ui-ux-pro-max | 1 | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill | MIT — `plugins/ui-pack/LICENSE-uiuxpromax-MIT.txt` |
| react-pack | 8 | https://github.com/vercel-labs/agent-skills | MIT — upstream README lisans beyanı (upstream ayrı LICENSE dosyası sunmuyor) |
| zanaat-pack | 7 | https://github.com/anthropics/skills | Apache-2.0 — her skill'in `LICENSE.txt` dosyası |

Özgün `sadrazam`, `defterdar`, `musavir`, `ordu-nizami`, `vezir-yetistirme`,
`arama-ustasi` ve `temkin` içerikleri depo kökündeki MIT lisansı kapsamındadır.

## Bu derlemedeki değişiklikler

- `claude-api/SKILL.md` açıklaması Agent Skills 1024 karakter sınırına uyacak
  biçimde kısaltıldı; lisanslı gövde ve referans içeriği korundu.
- `vercel-react-best-practices/AGENTS.md` içindeki üç kırık göreli bağlantı
  gerçek `rules/` konumuna yönlendirildi.
- Kaynak ve bilinçli fark kayıtları `UPSTREAM.md` içinde tutulur.

## Bilinçli olarak hariç tutulanlar

Anthropic deposundaki docx, pdf, pptx ve xlsx skill'leri proprietary veya
source-available koşullardadır; bu ürüne dahil edilmemiştir. Lisans dosyası
bulunmayan Karpathy-skills içeriği de yeniden dağıtılmamıştır.

## Marka notu

Bu ürün Anthropic, Claude, OpenAI, Vercel veya Superpowers tarafından
onaylanmış ya da bu kuruluşlarla bağlantılı değildir. Uyumluluk ifadeleri
yalnızca tanımlayıcıdır.

## GitHub Actions (çalıştırılan, vendoring yapılmayan)

Aşağıdaki eylemler kaynak olarak bu dağıtıma kopyalanmaz. GitHub Actions
işlerinde tam commit SHA ile çağrılır; kaynak, amaç ve izin kararı `UPSTREAM.md`
içinde izlenir.

| Eylem | Kaynak | Lisans | Yerel kullanım |
|---|---|---|---|
| ossf/scorecard-action | https://github.com/ossf/scorecard-action | Apache-2.0 | `.github/workflows/scorecard.yml` |
| actions/dependency-review-action | https://github.com/actions/dependency-review-action | MIT | `.github/workflows/dependency-review.yml` |
| actions/attest-build-provenance | https://github.com/actions/attest-build-provenance | MIT | `.github/workflows/release.yml` |

## Project OS araştırma adayları (dağıtılmayan)

Bu bölüm lisans ve köken incelemesinin kaydıdır; aşağıdaki depolardan bu
sürümde **kaynak kodu dağıtılmaz**, vendoring yapılmaz, binary eklenmez ve
otomatik kurulum yapılmaz. Bir adayın `ADOPT` veya `ADAPT` kararı, ileride ayrı
pin+atıf+lisans+eval+teftiş işi olmadan yeniden dağıtım izni değildir.

| Kaynak | İncelenen commit | Lisans kanıtı | Karar | Dağıtım durumu |
|---|---|---|---|---|
| agentskills/agentskills | `38a2ff82958afee88dadf4831509e6f7e9d8ef4e` | Apache-2.0 `LICENSE` | ADOPT | Dağıtılmıyor |
| github/spec-kit | `cf0abe28f7ee875448f9e4dbd8cd2b533797a1cb` | MIT `LICENSE` | ADAPT | Dağıtılmıyor |
| Fission-AI/OpenSpec | `a874d1d6715886db9210c527b1fc3799d9688a76` | MIT `LICENSE` | ADAPT | Dağıtılmıyor |
| MaxMiksa/Auto-Company | `ebfab9b4bd5f0ab5ad452a1ff85285b3c141acdd` | Ayrı lisans dosyası bulunmadı; README rozeti yeterli kanıt değildir | REFERENCE | Dağıtılmıyor |
| GoogleChrome/lighthouse-ci | `ebee453dad3f8acacd657a62ccc65e3296afb7d0` | Apache-2.0 `LICENSE` | ADOPT | Dağıtılmıyor |
| patrickhulce/lhci-client OCI image | `sha256:558210c5e422a7babaaa09c285b7469da3f00fac1a9880c37883c65d666a7fc9` (Linux/AMD64, gerçek runtime Lighthouse CI 0.14.0) | GoogleChrome/lighthouse-ci Apache-2.0 `LICENSE`; kaynak `gitHead` `36e629e9c03a2b328f5996c16f256431c5fef1fe` | ADOPT | Divan release'inde dağıtılmıyor; üretilen opt-in workflow digest ile çeker ve runtime sürümünü doğrular |
| lycheeverse/lychee | `af73b4e02731e0ff3a678b56769704d689138279` | Apache-2.0 OR MIT `lychee-bin/Cargo.toml` | ADOPT | Dağıtılmıyor |

Bu adayların ayrıntılı ürün/risk gerekçeleri ve kanıt URL'leri
`registry/candidates.json` ile `UPSTREAM.md` içinde tutulur. Lisansı belirsiz
Auto Company yalnız karşılaştırmalı referanstır; ondan hiçbir içerik alınmaz.
