# Divan'ı Komple Kaldırma

Misafirlik bitti mi? Divan iz bırakmadan gider. Sıra önemli:

## 1. Claude Code'dan paketleri kaldır
```
/plugin uninstall sadrazam@divan
/plugin uninstall core-pack@divan
/plugin uninstall ui-pack@divan
/plugin uninstall react-pack@divan
/plugin uninstall zanaat-pack@divan
```

## 2. Marketplace kaydını sil
```
/plugin marketplace remove divan
```
Bu ikisi komutları, skill'leri, subagent'ları (kâşif, müfettiş) ve
SessionStart hook'unu tamamen devre dışı bırakır.

## 3. (İsteğe bağlı) Proje hafızası dosyaları
Defterdar'ın SENİN projende ürettiği dosyalar sana aittir. `.divan/`,
`AGENTS.md` ve `BLUEPRINT.md` başka araçlar veya ekip üyeleri tarafından da
kullanılıyor olabilir; otomatik bir silme komutu çalıştırma. Önce yedek al,
`git status` ile sahipliği ve değişiklikleri denetle, sonra yalnızca Divan'a ait
olduğundan emin olduğun dosyaları tek tek kaldır.

## 4. Cursor/Codex'e elle kopyaladıysan
Kopyaladığın skill klasörlerini ilgili skill dizininden tek tek kaldır. Codex
kurucusunun oluşturduğu `~/.codex/divan-install-*.tsv` kaydı hedefleri ve varsa
önceki sürüm yedeklerini gösterir; yedekleri geri yüklemeden önce içeriklerini
incele.

## 5. Önbellek kalıntısı (nadiren gerekir)
Claude Code marketplace klonlarını `~/.claude/` altında tutar; adım 2
bunu yönetir. Şüphen varsa `~/.claude/plugins/` içinde "divan" ara, sil.

Hepsi bu — otomatik telemetri veya eve arama yoktur. Depoda Markdown skill
metinlerinin yanında açık kaynak betikler ve bazı üçüncü taraf varlıkları da
bulunur; kaldırma kapsamını kurulum kaydından doğrula.
