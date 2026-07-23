# Aday Meclisi

> Tek doğru kaynak: `registry/candidates.json`. Bu sayfa otomatik üretilir;
> bir adayın burada görünmesi kurulduğu veya onaylandığı anlamına gelmez.
> Otonomi sınırı: `never-auto-install`.

## Durum

Toplam **7** aday · ADAPT: 2 · ADOPT: 3 · PENDING: 0 · REFERENCE: 2 · REJECT: 0

| Aday | Tür | Lisans | Karar | Sonraki inceleme | Gerekçe |
|---|---|---|---|---|---|
| [Agent Skills Specification](https://github.com/agentskills/agentskills) | `standard-research` | Apache-2.0 | **ADOPT** | 2026-10-23 | ADOPT, yalnız açık Agent Skills sözleşmesinin uygun yüzeyini inceleme/adaptasyon adayı yapar; taşınacak içerik için ayrı pin, atıf, eval ve teftiş gerekir. |
| [Auto Company](https://github.com/MaxMiksa/Auto-Company) | `app-template` | UNKNOWN | **REFERENCE** | 2026-10-23 | REFERENCE: rol metaforu karşılaştırma girdisidir; lisans belirsizliği ve daemon modeli nedeniyle kod, prompt veya yapılandırma alınmayacaktır. |
| [Awesome MCP Servers](https://github.com/punkpeye/awesome-mcp-servers) | `registry-index` | MIT | **REFERENCE** | 2026-10-18 | İçeriği topluca almak yerine yapılandırılmış katkı ve otomatik aday teftişi fikri özgün Meclis akışına uyarlandı. |
| [GitHub Spec Kit](https://github.com/github/spec-kit) | `standard-research` | MIT | **ADAPT** | 2026-10-23 | ADAPT: specification-first kanıt zinciri Divan'ın dil, host ve fail-closed sözleşmesine özgün olarak uyarlanacaktır. |
| [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci) | `framework-library` | Apache-2.0 | **ADOPT** | 2026-10-23 | ADOPT: pinli, opt-in SEO/erişilebilirlik kanıtı için adaydır; gerçek çalıştırma ve CI entegrasyonu ayrı bir karardır. |
| [Lychee](https://github.com/lycheeverse/lychee) | `framework-library` | Apache-2.0 OR MIT | **ADOPT** | 2026-10-23 | ADOPT: isteğe bağlı, pinli link denetimi için adaydır; bu kayıt kurulum veya kaynak dağıtımı değildir. |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | `standard-research` | MIT | **ADAPT** | 2026-10-23 | ADAPT: değişiklik-spec yaklaşımı, Divan'ın kendi durum makinesi ve receipt sözleşmesine uyarlanacaktır. |

## Yaşam döngüsü

1. **Keşif:** GitHub araması veya topluluk formu yalnız aday üretir.
2. **Triage:** Kimlik, tür, mükerrerlik ve kullanıcı boşluğu belirlenir.
3. **Audit:** Lisans, köken, script/hook/araç yetkileri ve bakım kanıtı incelenir.
4. **Karar:** `ADOPT`, `ADAPT`, `REFERENCE` veya `REJECT` gerekçesiyle kaydedilir.
5. **İcra:** Yalnız `ADOPT/ADAPT`; pin, atıf, eval ve tüm teftiş kapılarından sonra ayrı PR ile yapılır.

Haftalık keşif workflow'u aday kodu indirmez veya çalıştırmaz. Yıldız ve güncellik yalnız keşif sinyalidir; lisans, güvenlik veya kalite kanıtı değildir.
