---
name: arama-ustasi
description: Evidence-first codebase search using ripgrep for bounded text discovery and optional ast-grep for syntax-aware structural search. Use when exploring an unfamiliar repository, locating definitions or call sites, estimating refactor impact, finding repeated code shapes, auditing risky patterns, or when the user says kodda ara, nerede kullanılıyor, bütün çağrıları bul, repo keşfet, search the codebase, find usages, structural search, or ast-grep. Starts narrow, caps output, and never pretends a regex result is AST-precise.
license: MIT
compatibility: Requires ripgrep; ast-grep is optional and must already be installed
---

# Arama Ustası

Amaç çok sonuç üretmek değil, soruyu kanıtlayan en küçük sonuç kümesini
bulmaktır. Metin için `rg`; sözdizimi önemliyse ve mevcutsa `ast-grep` kullan.

## Arama nizamı

1. Arama sorusunu tek cümleye indir: tanım mı, çağrı mı, dosya mı, kod şekli mi?
2. Önce kapsamı gör: `rg --files <hedef> | head -80`. Tüm depoyu körlemesine okuma.
3. Metin aramasını dosya türü ve dizinle daralt. Önce dosya sayısını veya ilk
   20–50 eşleşmeyi gör; sonra gerekirse genişlet.
4. Regex semantiği ayıramıyorsa AST aramasına geç. Araç yoksa kurma; regex
   sonucunun yaklaşık olduğunu açıkça söyle.
5. Sonucu `dosya:satır → neden ilgili` biçiminde özetle. Ham binlerce satırı
   bağlama taşıma.
6. Değişiklik öncesi etki haritası çıkar: tanım, çağrılar, testler, yapılandırma.

## Araç seçimi

```bash
command -v rg
command -v ast-grep || true
```

Bazı sistemlerde `sg` başka bir programa aittir. Yalnızca `sg --version`
çıktısı gerçekten ast-grep diyorsa onu kullan. Kullanıcı istemeden paket kurma.

### Metin araması

```bash
rg -n -F "exactSymbol" src/ --type ts --type tsx
rg -l "old_method\(" src/ --type py | head -50
rg -n "TODO|FIXME" . --glob '!{node_modules,dist,build,.git}/**' | head -50
```

- Kesin sembolde `-F`, kelimede `-w`, çevre gerekiyorsa küçük `-C` kullan.
- `.gitignore` davranışını varsayılan olarak koru; gizli/ignore edilmiş alanları
  yalnızca görev gerektiriyorsa bilinçli aç.
- `rg` varken `grep -R` veya `find` ile geniş tarama yapma.

### Yapısal arama

Ast-grep deseninin hedef dilde geçerli, parse edilebilir kod olması gerekir.
Metadeğişkenleri `$NAME`, `$ARG` ve `$$$BODY` biçiminde kullan.

```bash
ast-grep run --lang ts --pattern 'fetch($URL, $$$REST)' src/
ast-grep run --lang py --pattern 'def $NAME($$$ARGS): $$$BODY' app/
```

Önce tek dosya veya dar dizinde deseni doğrula. Dönüşüm yapmadan önce yalnızca
arama çalıştır; otomatik rewrite ayrı kullanıcı kararıdır.

## Emniyet ve takdim

- Sır veya kimlik bilgisi araması gerekiyorsa değeri çıktıda gösterme; yalnızca
  konumu ve bulgu türünü bildir.
- Aktif hata ayıklamada son hata mesajını ve ilgili satırları kesme.
- Teslimde kullanılan komutu, kapsamı, eşleşme sayısını ve önemli dosyaları ver.
- “Hiç eşleşme yok” sonucunda kapsam, ignore kuralları ve dil filtresini kontrol et.
