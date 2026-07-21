# Kurulum

## Claude Code/Desktop Code + Codex (önerilen yerel yol)

Kurucu varsayılan olarak yalnız planı gösterir; host durumunu değiştirmez:

```powershell
python scripts/kur-hostlar.py --host both --ref <release-tag>
```

Çıktıyı inceledikten sonra aynı sabit referansı uygula:

```powershell
python scripts/kur-hostlar.py --host both --ref <release-tag> --execute
```

Kurulumdan önce veya sonra iki hostun durumunu hiçbir şeyi değiştirmeden kontrol
edin:

```powershell
python scripts/kur-hostlar.py --doctor --host both --ref <release-tag>
```

Doctor, CLI erişilebilirliğini, Divan pazarı kaynak/ref bilgisini, beş paketin
sürümünü ve etkinliğini, pazarsız kalmış paketleri ve tamamlanmamış işlemleri
raporlar. Otomasyon için yalnız JSON çıktı alın:

```powershell
python scripts/kur-hostlar.py --doctor --json --host both --ref <release-tag>
```

Her doctor sonucu bir sonraki kesin komutu yazar; tamamlanmamış işlemde bu,
ilgili `--rollback-transaction` komutudur. Doctor host CLI'larını veya işlem
günlüklerini değiştirmez.

Uzak Claude pazarı değişmez bir release etiketi ister. Bir commit SHA'sını CI
veya geliştirme doğrulamasında kullanacaksanız, aynı temiz checkout'u yerel
kaynak olarak verin: `--source <repo-yolu> --ref <40-karakter-SHA>`.

Repo üzerinden geliştirme yapıyorsanız önce
`python scripts/hijyen.py --check` çalıştırın. Cache temizliği gerektiğinde
`--clean` yalnız yeniden üretilebilir allowlist'i siler; kurulum manifestleri,
kanıtlar ve geri alma yedekleri korunur.

Kurucu, aynı isimde mevcut bir `divan` pazarı veya pazarsız kalmış `@divan`
eklentisi görürse onun kaynak ve ref bilgisini güvenilir biçimde kanıtlayamadığı
için durur; mevcut pazarı veya eklentileri değiştirmez. Önce host'un kendi
listeleme komutlarıyla kayıtları inceleyin ve yalnız size ait olduklarından
eminseniz elle kaldırıp işlemi yeniden çalıştırın.

Her dış CLI değişikliğinden önce işlem günlüğü atomik yazılır. Kesinti sonrası
`in-progress`, `recovering` veya `rollback-incomplete` kaydını yalnız o işlemin oluşturduğu
girdilerle geri almak için:

```bash
python scripts/kur-hostlar.py --rollback-transaction <islem.json>
```

Eski gevşek-skill göçü de tüm hedeflerin kurulum özetini önce doğrular; değişmiş
dosyaya dokunmaz, hedefleri silmek yerine `.codex/divan-quarantine/` altında
saklar ve ara hata olursa bütün taşıma işlemlerini tersine çevirir.
Göç ve fallback kopyalama adımları da ayrı, atomik bir legacy günlüğü tutar;
ana işlem günlüğü kesinti sonrası önce bu alt işlemi, sonra host kayıtlarını
idempotent biçimde geri kazanır.

`--host claude` veya `--host codex` tek host seçer. Kurucu iki ürünün resmî
plugin CLI'larını kullanır, mevcut durumun tam listesini işlem kaydına yazar,
yalnız kendi eklediği `divan` kayıtlarını geri alır ve alakasız eklentilere
dokunmaz. Kayıtlar `~/.divan/transactions/` altındadır. Claude Desktop'ın Code
yüzeyi kullanıcı kapsamındaki Claude Code eklentilerini ortak kullanır.

Önceden `kur-codex` ile kopyalanmış Divan skill'leri varsa onları ancak beş
paketin yerel kurulumu doğrulandıktan sonra taşı:

```powershell
python scripts/kur-hostlar.py --host both --ref <release-tag> --execute --migrate-legacy
```

## Elle yerel eklenti kurulumu

Claude Code:

```text
/plugin marketplace add trugurpala/divan
/plugin install sadrazam@divan
/plugin install core-pack@divan
/plugin install ui-pack@divan
/plugin install react-pack@divan
/plugin install zanaat-pack@divan
```

Codex:

```powershell
codex plugin marketplace add trugurpala/divan --ref <tag-veya-commit>
codex plugin add sadrazam@divan
codex plugin add core-pack@divan
codex plugin add ui-pack@divan
codex plugin add react-pack@divan
codex plugin add zanaat-pack@divan
```

Doğrudan skill kopyalayan `kur-codex.ps1`/`.sh` yolu yalnız eski hostlar için
uyumluluk fallback'idir; yerel plugin pazarı destekleniyorsa bu yolu kullanma.

v0.12.2 eski-host fallback kaydı; betik release arşivini indirmeden önce eşlik
eden SHA-256 kaydını alır ve uyuşmayan arşivi açmadan durur:

```bash
curl -fsSL https://raw.githubusercontent.com/trugurpala/divan/v0.12.2/scripts/kur-codex.sh | DIVAN_REF=v0.12.2 bash
```

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
| Skills (41 vezir) | ✓ yerel plugin ile | ✓ Codex yerel plugin; diğer hostlarda Agent Skills klasörü |
| Memory (defterdar dosyaları: AGENTS.md, BLUEPRINT, .divan/) | ✓ | ✓ düz dosya + AGENTS.md'yi Codex/Cursor doğal okur |
| Komutlar (/ferman /sefer /defter /teftis) | ✓ | ✗ Claude Code'a özgü (skill tetikleyicileri yine çalışır) |
| Subagents (kâşif, müfettiş) | ✓ | ✗ Claude Code'a özgü |
| Hooks (oturum başında defteri otomatik oku) | ✓ | ✗ Claude Code'a özgü |
| Marketplace tek komut kurulum | ✓ | ✓ |

Özet: skill'ler ve hafıza dosyaları her yerde taşınır; komut/subagent/hook
katmanları Claude Code'da tam güçtedir.

`uyumluluk` CI matrisi Claude Code ve Codex pazar/paket şemalarını; fallback
yolunu ise Linux, macOS ve Windows'ta geçici, boş skill dizinlerinde 41 skill
keşfi ve kayıtlı kaldırma tatbikatıyla sınar.
