# Kurulum

## Tek komutla her şey — Divan Kurucusu (önerilen)

Kurucu; Claude Code'u (masaüstü uygulaması + CLI — ikisi aynı `~/.claude`
kurulumunu paylaşır) ve Codex'i kendisi bulur, Divan'ı bilgisayara **global**
kurar. Önce ne yapacağını söyler, soru sormaz; aynı adlı mevcut skill'leri
silmez, tarihli yedeğe taşır ve kurulum kaydı tutar.

Windows (PowerShell):
```powershell
irm https://raw.githubusercontent.com/trugurpala/divan/main/scripts/kur.ps1 | iex
```
macOS/Linux:
```bash
curl -fsSL https://raw.githubusercontent.com/trugurpala/divan/main/scripts/kur.sh | bash
```

En güvenli kullanımda betiği önce indirip inceleyin. Araçlardan biri kurulu
değilse kurucu resmî kurulum komutunu gösterir; aracı kurduktan sonra **yeni**
bir terminal açıp kurucuyu tekrar çalıştırın. `claude` komutu olmayan
yalnız-masaüstü kullanıcısına, uygulamaya yapıştırılacak `/plugin` satırlarını
yazdırır. Geri alma da tek komuttur: [[Kaldirma]].

### Sürüm sabitleme (isteğe bağlı)

Kurucu varsayılan olarak `main` içeriğini kurar. Codex'e kopyalanan skill
içeriğini belirli bir sürüme sabitlemek için:

```bash
curl -fsSL https://raw.githubusercontent.com/trugurpala/divan/main/scripts/kur.sh | DIVAN_REF=v0.12.0 bash
```

Claude Code paketleri marketplace üzerinden depo varsayılan dalını izler;
`DIVAN_REF` yalnız Codex tarafını sabitler.

## Claude Code — elle kurulum
```
/plugin marketplace add trugurpala/divan
/plugin install sadrazam@divan
/plugin install core-pack@divan
/plugin install ui-pack@divan
/plugin install react-pack@divan
/plugin install zanaat-pack@divan
```
Güncelleme: `/plugin marketplace update divan` · Kaldırma: `/plugin uninstall <paket>@divan`

## Yalnız Codex kurulumu

Divan Kurucusu Codex'i zaten kapsar; yalnız Codex'e kurmak istersen:

Windows (PowerShell):
```powershell
$env:DIVAN_REF = "v0.12.0"
irm https://raw.githubusercontent.com/trugurpala/divan/main/scripts/kur-codex.ps1 | iex
```
macOS/Linux:
```bash
curl -fsSL https://raw.githubusercontent.com/trugurpala/divan/main/scripts/kur-codex.sh | DIVAN_REF=v0.12.0 bash
```
`DIVAN_REF` bir sürüm etiketi veya commit ile kaynak içeriğini sabitler;
geliştirme dalını izlemek isteyenler bilinçli olarak `main` kullanabilir.
Kurucu, aynı adlı mevcut skill klasörlerini birleştirmez: tarihli yedeğe taşır
ve kurulum kaydı üretir. Sonra Codex'i yeniden başlat. Skill'ler tetikleyici
cümlelerle çalışır ("baştan sona yap", "defter kur"); /komutlar, hook ve
subagent'lar Claude Code'a özgüdür — Codex'te hafıza AGENTS.md üzerinden yürür.

## Cursor / diğer Agent Skills uyumlu ajanlar
Skill'ler açık standarttır; repo'daki `plugins/*/skills/*` klasörlerini
ajanının skill dizinine kopyalaman yeterlidir (ör. Cursor'da proje köküne
`.cursor/skills/` ya da ajanın belgelerinde belirtilen dizin).

## Doğrulama
Kurulumdan sonra ajana "hangi skill'lerin var?" diye sor; `sadrazam` ve
`vezir-yetistirme` listede görünmelidir.

## Uyumluluk matrisi (dürüst)

| Katman | Claude Code | Codex / Cursor / diğer |
|---|---|---|
| Skills (41 vezir) | ✓ /plugin ile | ✓ Agent Skills standardı — klasör kopyala |
| Memory (defterdar dosyaları: AGENTS.md, BLUEPRINT, .divan/) | ✓ | ✓ düz dosya + AGENTS.md'yi Codex/Cursor doğal okur |
| Komutlar (/ferman /sefer /defter /teftis) | ✓ | ✗ Claude Code'a özgü (skill tetikleyicileri yine çalışır) |
| Subagents (kâşif, müfettiş) | ✓ | ✗ Claude Code'a özgü |
| Hooks (oturum başında defteri otomatik oku) | ✓ | ✗ Claude Code'a özgü |
| Tek komut kurulum (Divan Kurucusu) | ✓ | ✓ Codex — kurucu betiğiyle; Cursor vb. elle kopyalama |

Özet: skill'ler ve hafıza dosyaları her yerde taşınır; komut/subagent/hook
katmanları Claude Code'da tam güçtedir.

`uyumluluk` CI matrisi Claude Code marketplace/paket şemasını temiz CLI ile;
Codex kurulumunu Linux, macOS ve Windows'ta geçici, boş skill dizinlerinde 41
skill keşfi ve kayıtlı kaldırma tatbikatıyla; birleşik Divan Kurucusu'nu ise
aynı üç işletim sisteminde sahte `claude` CLI kayıtlarıyla (pazar ekleme, beş
paket, tekrarlı koşu ve kaldırma) sınar.
