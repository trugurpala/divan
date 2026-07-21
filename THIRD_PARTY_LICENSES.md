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
