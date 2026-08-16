# PASS 1 teftişi — Ferman planlama hattı

- Tarih: 2026-08-16
- Kapsam: PR #156 → #157 → #158 yığını, güncel `main` üzerinde
- Taban commit: `68e91fd`
- Dal: `work/pass1-ferman-pipeline`
- Ortam: Windows 11, Python 3.12.10, Node 22.23.2, pnpm 10.34.5, Git 2.54.0

## Sonuç

Yığın güncel `main` üzerinde zaten yeniden yazılmıştı; yeniden uygulanmadı.
Bağımsız teftiş üç adet P1 kusur buldu. Üçü de kendi reprodüksiyonumuzla
doğrulandı, düzeltildi ve regresyon testine bağlandı. Kanonik doğrulama bu
makinede tamamlanamıyor; nedeni koda değil makine ACL durumuna bağlıdır ve
aşağıda ayrıca kayıtlıdır.

## Yığın kimliği

| PR | Commit | İçerik |
|---|---|---|
| #156 | `82331fe` | Nizâm-ı Sefer hedef planlamasını Desktop API'ye açar |
| #157 | `dcb5427` | Planı bağımlılık farkındalıklı iş paketlerine materialize eder |
| #158 | `ff13737` | Patron Masası'nı önizleme/kaydetme akışına bağlar |

## Bağımsız teftiş bulguları ve kapanışı

Teftiş değişikliği yazmayan ayrı bir ajan tarafından yapıldı ve **BLOCK**
kararı verdi. Üç P1 bulgusu:

1. **Önizlenen plan, kaydedilen plan değildi.** `goal.preview` ve
   `goal.create` ham fermandan planlarken `start_goal` redakte edilmiş
   fermandan planlıyor ve kaydediyordu. Kimlik bilgisi içeren bir fermanda
   önizleme 6 iş paketi gösterirken 12 tanesi yazıldı; tek bir
   `goal.create` yanıtının içinde `summary` ile `work_packages` çelişti.
2. **`goal.create` rastgele klasöre yazıyordu.** `project.register` gerçek
   bir Git deposu şart koşarken hedef planlama bu kapıyı atlıyor ve
   kayıtsız, Git bile olmayan bir klasöre `.divan` açıyordu.
3. **Bağımlılık grafiği zorlanmıyordu.** `_execution_task` yalnız
   `approve_execution` ve task durumuna bakıyordu; bağımlı olduğu paket
   hâlâ `planned` iken bir iş paketi başlatılabiliyordu.

Üçü de düzeltildi. Ek olarak ulaşılamaz durumdaki `TaskStore.goal_tasks`
`goal.tasks` komutu olarak bağlandı.

## Doğrulama

| Kapı | Sonuç |
|---|---|
| Hedefli testler (goal + desktop + host probe) | PASS — 79 test |
| Yeni regresyon testleri | PASS — 4 test |
| Desktop frontend `tsc -b` + `vite build` | PASS |
| Hijyen, validate, prose, handoff, catalog, v1, release, evals | PASS |
| Kanonik `scripts/verify.py` tam süit | ENGELLİ — aşağıya bakınız |

Yeni testlerin totolojik olmadığı, kaynak düzeltmeleri geçici olarak geri
alınıp 4/4 testin kırmızıya döndüğü gözlenerek kanıtlandı.

## Regresyon farkı

Aynı makinede, aynı komutla iki koşum:

| Ölçüm | `main` (`68e91fd`) | PASS 1 dalı |
|---|---|---|
| Çalışan test | 1020 | 1037 |
| Başarısız test (tekil) | 87 | 84 |
| Yeni regresyon | — | **0** |
| Düzelen önceki hata | — | 3 |

Düzelen üç test `test_host_install` içindeki host probe testleridir.
Bunlar `shutil.which` yamalıyordu; `run()` Windows'ta `resolve_executable`
kullandığı için bu testler yalnız makinede gerçekten `codex` kuruluysa
geçiyordu. Kardeş testin desenine hizalandılar.

## Engel: kanonik doğrulama bu makinede tamamlanamıyor

Kalan 84 başarısız test `main` ile birebir aynıdır ve tamamı tek bir kök
nedene bağlıdır:

```text
trusted init state directory DACL grants mutation rights to another principal
```

`C:\Users\User\AppData` üzerinde çözümlenemeyen bir capability SID
(`S-1-15-3-3557...`) bütün AppData ağacına `FullControl` veriyor.
`project_os._windows_private_dacl`, `LOCALAPPDATA`'yı güvenilir state kökü
olarak denetlediği için bunu yabancı principal sayıp fail-closed duruyor.
`DIVAN_STATE_HOME` ile kaçış yok; override da `LOCALAPPDATA` içinde olmak
zorunda ve düşen dizin `LOCALAPPDATA`'nın kendisi.

Bu bir Divan kod regresyonu değildir; `main` üzerinde de aynen üretilir ve
GitHub Windows runner'larında bu ACE bulunmadığı için orada görünmez. Bu
kapı `PASS` sayılmamıştır; `ENGELLİ` olarak kaydedilmiştir ve sahibe karar
olarak taşınmıştır.

## Sınır

Bu kayıt yerel doğrulama ve bağımsız teftiş kanıtıdır. Yayımlanmış release,
canlı doğrulama, bağımsız kullanıcı kabulü, performans veya kalite artışı
iddiası değildir. Gerçek Codex/Claude worker ile uçtan uca execution bu
dilimin kapsamında değildir; planlama hiçbir kaynak kodu değiştirmez.
