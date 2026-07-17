# Eval Protokolü

## Sözleşme

`evals/evals.json` en az iki gerçek kullanım örneği taşır:

```json
{
  "skill_name": "ornek-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "Kullanıcının söyleyeceği gerçek görev",
      "expected_output": "Başarılı çıktının kısa tarifi",
      "expectations": ["Nesnel ölçüt"],
      "files": []
    }
  ]
}
```

`files` yolları skill klasörüne göre göreli olmalı ve klasörün dışına çıkmamalı.

## Karşılaştırma düzeni

1. Aynı prompt, girdi dosyaları, model sınıfı ve araç yetkilerini kullan.
2. Yeni skill'de `with_skill`; yeni skill için skillsiz `baseline`, iyileştirmede
   eski skill snapshot'ı çalıştır.
3. Koşuları temiz ve birbirinden bağımsız bağlamlarda başlat. Beklenen cevabı
   veya diğer koşunun sonucunu prompt'a koyma.
4. Sonuçları `.divan/evals/<skill>/<tarih>/` altında veya geçici çalışma
   alanında tut; skill klasörünün yanına keşfedilebilir workspace bırakma.
5. Her beklentiyi çıktı kanıtıyla `pass`, `fail` veya `not_observable` olarak
   değerlendir. Sıfır tamamlanmış koşuda rapor üretme.
6. Süre ve token runtime bildirirse ham değeri kaydet; bildirmiyorsa boş bırak.
7. En az iki örnek skill lehine açık davranış farkı göstermeden “iyileşti” deme.

## Öznel işler

Tasarım ve yazımda tek modelin kendi çıktısına sayısal puan vermesi zayıf
kanıttır. Çıktıları kimlikleri gizlenmiş A/B biçiminde kullanıcıya göster veya
önceden yazılmış rubriği kullan. Tercihi kalite gerekçesiyle birlikte kaydet.

## Tetikleme kontrolü

Pozitif prompt'ların yanında skill'in açılmaması gereken yakın negatif örnekler
de düşün. Description çok genişse gereksiz bağlam yükler; çok darsa gerçek
isteklerde tetiklenmez. Tetikleme testi ile çıktı kalitesi testini ayrı raporla.
