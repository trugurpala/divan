---
name: baglam-muhafizi
description: Context-budget guardian for long-running agent work. Use when a session becomes long or repetitive, tool outputs dominate the conversation, retrieved documents overwhelm the task, compaction or handoff is approaching, multiple agents need clean partitions, API context cost or cache stability matters, or the user says bağlamı koru, context doldu, token azalt, konuşma ağırlaştı, compact this, optimize context, mask tool output, or preserve state. Protects goals and active errors while reducing low-value context, and never invents token or cache metrics the runtime does not expose.
license: MIT
compatibility: Claude Code, Codex and API agents; telemetry-dependent actions require runtime support
---

# Bağlam Muhafızı

Bağlam kalitesi miktardan önemlidir. Önce sinyali koru, sonra gürültüyü azalt;
ölçemediğin token, maliyet veya cache oranını uydurma.

## Korunacak çekirdek

Her azaltmadan önce şu çekirdeği çıkar:

- güncel hedef ve “bitti” ölçütü,
- kullanıcının değişmez kısıtları ve son düzeltmeleri,
- alınmış kararlar ve gerekçeleri,
- aktif hata, son hata çıktısı ve denenmiş başarısız yollar,
- değişen dosyalar, doğrulama komutları ve açık riskler.

Aktif debugging sürerken hata mesajını, stack trace'in ilgili bölümünü veya son
üç turun tanı kanıtını maskeleme.

## Azaltma sırası

1. **Daralt:** İlgisiz araçları ve belgeleri yükleme; aramayı dosya/dizin/türle sınırla.
2. **Tekilleştir:** Yinelenen çıktıları kaldır, tek kanonik bulgu bırak.
3. **Dışarı al:** Büyük log ve raporları dosyada tut; bağlamda yol + kısa özet bırak.
   Projede `defterdar` etkin değilse kalıcı `.divan/` dosyası oluşturma.
4. **Maskele:** Amacını tamamlamış eski araç çıktısını geri çağrılabilir referans ve
   ana bulguyla değiştir. Son turu veya aktif kanıtı maskeleme.
5. **Sıkıştır:** Hedefi, kararları, hataları ve kullanıcı tercihlerini koruyan bir
   devir özeti üret; sıkıştırma sonrası özeti güncel fermanla tekrar karşılaştır.
6. **Böl:** Tek bağlam hâlâ yetmiyorsa yalnızca bağımsız işleri `ordu-nizami`
   ile temiz bağlamlara ayır. Koordinasyon maliyetini hesaba kat.

## Ölçüm politikası

Runtime gerçek kullanım verisi veriyorsa:

- %70 civarında uyar ve azaltma planını hazırla,
- %80 civarında maskeleme/sıkıştırmayı uygula,
- toplam pencerenin en az %10'unu cevap ve doğrulama için ayır.

Runtime veri vermiyorsa yüzdelik raporlama. Bunun yerine belirtileri izle:
tekrar, unutulan kısıtlar, aynı dosyanın yeniden okunması, çok büyük araç
çıktıları ve ilgisiz retrieval sonuçları.

API/harness tasarımında cache istatistiği gerçekten ölçülüyorsa kararlı sistem
ve araç tanımlarını prefix'te, dinamik veriyi sonda tut. Sağlayıcı metriği yoksa
“cache hit yükseldi” deme; yalnızca cache-dostu yapı uygulandığını söyle.

## Devir özeti

Sıkıştırma veya oturum devrinde şu biçimi kullan:

```markdown
## Hedef
## Değişmez kısıtlar
## Kararlar
## Kanıt ve değişen dosyalar
## Aktif hata / açık risk
## Sonraki kesin adım
```

Ham log yerine dosya yolunu ve gerekli 3–8 satırlık özü yaz. Devir özetini
otorite saymadan önce son kullanıcı mesajıyla çelişki açısından denetle.

## Takdim

Bağlam müdahalesi yaptıysan neyin korunduğunu, neyin dışarı alındığını,
hangi çıktının maskelendiğini ve ölçülebilen gerçek kazanımı bildir. Ölçüm yoksa
yalnızca uygulanan politikayı söyle; kalite veya maliyet yüzdesi uydurma.
