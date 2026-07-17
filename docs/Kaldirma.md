# Divan'ı Komple Kaldırma

Misafirlik bitti mi? Divan iz bırakmadan gider. Sıra önemli:

## 1. Claude Code'dan paketleri kaldır
```
/plugin uninstall sadrazam@divan
/plugin uninstall core-pack@divan
/plugin uninstall ui-pack@divan
/plugin uninstall react-pack@divan
```

## 2. Marketplace kaydını sil
```
/plugin marketplace remove divan
```
Bu ikisi komutları, skill'leri, subagent'ları (kâşif, müfettiş) ve
SessionStart hook'unu tamamen devre dışı bırakır.

## 3. (İsteğe bağlı) Proje hafızası dosyaları
Defterdar'ın SENİN projende ürettiği dosyalar sana aittir ve kaldırma
sonrası zararsız düz Markdown'dır — AGENTS.md'yi başka ajanlar da okur,
silmek zorunda değilsin. Yine de komple temizlik istersen proje kökünde:
```
rm -rf .divan/ && rm -f AGENTS.md BLUEPRINT.md
```
(Önce içlerinde saklamak istediğin karar/ilerleme notu var mı bak.)

## 4. Cursor/Codex'e elle kopyaladıysan
Kopyaladığın skill klasörlerini ilgili skill dizininden sil.

## 5. Önbellek kalıntısı (nadiren gerekir)
Claude Code marketplace klonlarını `~/.claude/` altında tutar; adım 2
bunu yönetir. Şüphen varsa `~/.claude/plugins/` içinde "divan" ara, sil.

Hepsi bu — kayıt cihazı yok, telemetri yok, eve arama yok. Divan yalnızca
Markdown'dır; sildiğinde gitmiştir.
