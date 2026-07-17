# GitHub Kullanımı — Bu Repo Nimetleri Nasıl Kullanıyor?

Divan, GitHub'ı yalnız depo değil, ürünün işletim sistemi olarak kullanır.
Vibe coder olarak senin de asgari GitHub aklın bu tablo kadar olsun:

| Nimet | Divan'da ne işe yarıyor | Sen nasıl kullanırsın |
|---|---|---|
| **Repo** | Tek gerçek kaynak; `/plugin marketplace add trugurpala/divan` buradan kurar | Kod + BLUEPRINT hep repoda; sohbette değil |
| **Actions (CI)** | Yerel + Agent Skills + Claude Code teftişi; site/Wiki testi, aylık upstream nöbeti ve haftalık Meclis keşfi | Yeşil tik görmeden birleştirme |
| **Pages** | https://trugurpala.github.io/divan/ — ücretsiz, login'siz vitrin | docs/ klasörü = anında site |
| **Releases** | Marketplace `main` sürümü v0.10.3; son etiketli release v0.7.0 | Etiket yokken “release yayımlandı” deme; üretimde bilinen commit'e sabitle |
| **Issues + etiketler** | yeni-vezir / hata / conduct akışları | Fikrini şablonla aç, etiket yönlendirir |
| **Discussions** | Serbest sohbet, soru-cevap | Issue'ya değmeyen her şey |
| **Topics** | claude-code, agent-skills, vibe-coding... keşif | Arayanlar seni bulur |
| **Wiki** | `docs/*.md` kaynaklarından derlenir; `main` sonrası Actions ayrı Wiki Git deposuna yazar ve canlı sürümü okur | Elle Wiki'yi değil kaynak belgeyi değiştir |

Altın kural: **repoya girmeyen bilgi yok hükmündedir.** Ajanla verdiğin her
kalıcı karar BLUEPRINT.md'ye işlenmeli — akıl orada yaşar.
