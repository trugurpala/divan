# GitHub Kullanımı — Bu Repo Nimetleri Nasıl Kullanıyor?

Divan, GitHub'ı yalnız depo değil, ürünün işletim sistemi olarak kullanır.
Vibe coder olarak senin de asgari GitHub aklın bu tablo kadar olsun:

| Nimet | Divan'da ne işe yarıyor | Sen nasıl kullanırsın |
|---|---|---|
| **Repo** | Tek gerçek kaynak; `/plugin marketplace add trugurpala/divan` buradan kurar | Kod + BLUEPRINT hep repoda; sohbette değil |
| **Actions (CI)** | Yerel + Agent Skills + Claude Code teftişi; temiz-host matrisi, site/Wiki testi, yayın, upstream nöbeti ve Meclis keşfi | Yeşil tik görmeden birleştirme |
| **Pages** | https://trugurpala.github.io/divan/ — ücretsiz, login'siz vitrin | docs/ klasörü = anında site |
| **Releases** | `main` sonrası Pages ve Wiki v0.11.1 olunca CHANGELOG'dan otomatik tag/not üretir | Güncel tag'i Releases sayfasından doğrula; üretimde etikete sabitle |
| **Issues + etiketler** | yeni-vezir / hata / conduct akışları | Fikrini şablonla aç, etiket yönlendirir |
| **Discussions** | Serbest sohbet, soru-cevap | Issue'ya değmeyen her şey |
| **Topics** | claude-code, agent-skills, vibe-coding... keşif | Arayanlar seni bulur |
| **Wiki** | `docs/*.md` kaynaklarından derlenir; `main` sonrası Actions ayrı Wiki Git deposuna yazar ve canlı sürümü okur | Elle Wiki'yi değil kaynak belgeyi değiştir |

Altın kural: **repoya girmeyen bilgi yok hükmündedir.** Ajanla verdiğin her
kalıcı karar BLUEPRINT.md'ye işlenmeli — akıl orada yaşar.

## Bakım ve güvenlik kapıları

- `.github/CODEOWNERS`, politika, otomasyon, yayın ve hafıza dosyalarının
  sorumlusunu belirler. Zorunlu inceleme için GitHub Ruleset içinde code-owner
  review ayrıca açılmalıdır.
- `.github/dependabot.yml`, GitHub Actions için haftalık güncelleme PR'ları
  açar. Dependabot alerts, secret scanning, push protection ve CodeQL depo
  ayarlarıdır; dosya eklemek bunların açık olduğunu kanıtlamaz.
- Workflow'lar `GITHUB_TOKEN` yetkisini iş düzeyinde daraltır. Release ve Wiki
  yazma işleri dışında varsayılan erişim salt okunurdur.
- `CLAUDE.md` ile `scripts/devral.py --check`, Claude Code'un sohbet geçmişi
  olmadan kuralları, yönü, mevcut durumu ve yayın kapılarını bulmasını sağlar.

## Yayın tek komut, ama tek durum değil

`python scripts/yayin.py --prepare <semver>` deterministik sürüm alanlarını
hazırlar. CHANGELOG ve BLUEPRINT yapılan gerçek işi anlatır. CI
`python scripts/yayin.py --check` ile farkı kırar. `main` sonrası `release`
workflow'u Pages ve Wiki'yi canlıdan okur; ikisi de aynı sürüme gelince etiketi
ve GitHub Release sayfasını üretir. Var olan etiket başka commit'e taşınmaz.
