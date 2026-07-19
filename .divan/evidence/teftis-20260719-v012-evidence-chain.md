# v0.12 Evidence Chain Teftişi · 2026-07-19

## Kapsam

- Windows Codex kurulumunun kur–çakışmayı yedekle–kaldır–geri yükle yaşam döngüsü.
- Gerçek eval sonucuna gizli anahtar içermeyen provenance ekleme sözleşmesi.
- Vitrin ve kalıcı proje kayıtlarının güncellenmesi.

## Kanıt

| Kontrol | Sonuç |
| --- | --- |
| `python scripts/validate.py` | Geçti: 5 paket, 41 skill, isim çakışması yok |
| `python scripts/devral.py --check` | Geçti |
| `python scripts/katalog.py --check` | Geçti: 41 skill / 5 paket |
| `python scripts/v1.py --check` | Geçti: hedef v1.0.0; dış kapılar değişmedi |
| `python scripts/yayin.py --check` | Geçti: v0.11.1, 13 yüzey |
| `python evals/run.py --check` | Geçti: 4 skill, 13 vaka |
| `python -m unittest discover -s tests -v` | 33 geçti; 1 POSIX shell testi Windows'ta bilinçli atlandı |
| `git diff --check` | Geçti |

## Sonuç

Windows'ta PowerShell kurucusu artık gerçek yaşam döngüsü testiyle doğrulanır.
Eval provenance alanı ajan/hakem/sürüm/commit/ortam kimliğini kamu sonucuna
ekler, kör eşlemeyi anahtar dosyasından ayırır ve `sk-` biçimli gizli değerleri
reddeder.

Bu mekanik kanıt, gerçek ajan+hâkim A/B sonucunun veya bağımsız kullanıcı
benimsemesinin yerine geçmez. `real-agent-comparison` ve
`independent-adoption` v1 kapıları `pending` kalır.
