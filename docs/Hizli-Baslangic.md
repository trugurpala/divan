# Hızlı Başlangıç

Divan'ı kullanmak için skill veya ajan adı ezberlemen gerekmez. Önce hedefini
söyle, sonra Divan'ın kanıt zincirini izle.

## 1. Çekirdeği kur

Claude Code:

```text
/plugin marketplace add trugurpala/divan
/plugin install sadrazam@divan
/plugin install core-pack@divan
```

Codex, Cursor ve diğer hostlar için [[Kurulum]] sayfasına git.

## 2. Niyetini ferman olarak yaz

Kopyalayıp doldur:

```text
Ferman: [istediğim sonucu yaz].
Önce mevcut projeyi tanı, en küçük planı çıkar, uygula, test et;
README/plan/canlı yüzey etkileniyorsa aynı turda güncelle.
Kanıtsız “bitti” deme ve sıradaki kesin adımı kaydet.
```

Örnekler:

- “Kullanıcı girişini baştan sona ekle.”
- “Bu hatanın kök nedenini bul, regresyon testiyle düzelt.”
- “Landing'i özgün bir görsel yönle yeniden tasarla ve tarayıcıda doğrula.”
- “Bu repoyu tanı; mimari, risk ve sıradaki işi kalıcı deftere yaz.”

## 3. Teslimde beş kanıtı ara

1. Ne istendiği ve hangi varsayımların yapıldığı.
2. Uygulanan kısa plan.
3. Değişen gerçek dosyalar.
4. Test/CI/tarayıcı çıktısı.
5. `main`, release ve canlı durumunun birbirinden doğru ayrılması.

Canlı ferman seçici: https://trugurpala.github.io/divan/#basla
