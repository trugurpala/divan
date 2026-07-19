# Divan davranış eval'leri

Bu koşucu aynı vakayı iki kez çalıştırır: baseline koşulunda skill yolu verilmez,
skill koşulunda ilgili `SKILL.md` dizini adaptöre sunulur. Çıktılar A/B olarak
körleştirilir. OpenAI Agents SDK, Codex, Claude Code veya başka bir ajan bu küçük
JSON stdin/stdout sözleşmesine adaptör olabilir.

## API anahtarsız sözleşme kontrolü

```bash
python evals/run.py --check
python evals/run.py --check --skill kaynak-kuratori
```

Bu komut model çalıştırmaz. Sıfır skill veya sıfır vaka başarı sayılmaz.

## Gerçek A/B koşusu

```bash
python evals/run.py --run \
  --skill kaynak-kuratori \
  --adapter "python /guvenilir/yol/agent_adapter.py"
```

Ajan adaptörü stdin'den şu alanları alır: `condition`, `skill_name`, `case_id`,
`prompt`, `files`, `skill_path`. Baseline için `skill_path` null'dır. Tek JSON
nesnesi döndürmelidir:

```json
{
  "output": "Ajanın son yanıtı",
  "events": ["search", "license-check"],
  "changed_files": []
}
```

Hakem verilmezse sonuç `review_required` olur ve performans iddiası üretmez.
Körleme anahtarı `latest.key.json` dosyasına ayrı yazılır.

## Birinci taraf Claude + Codex yolu

Divan'ın gerçek sağlayıcı preset'i Claude Code'u ajan, Codex'i kör hakem olarak
çalıştırır:

```bash
python evals/run.py --run \
  --provider-preset claude-codex \
  --skill baglam-muhafizi \
  --provenance provenance.json \
  --output evals/results/claude-codex.json
```

Bu preset yalnız araç gerektirmeyen, denetlenmiş `baglam-muhafizi` sözleşmesini
kabul eder. Böylece geçici boş çalışma dizini ve kapalı araçlarla repo araması
yapılmış gibi davranan sahte bir operasyonel kanıt üretilemez. Claude baseline
koşusu geçici boş dizinde, araçlar/MCP/ayar kaynakları kapalı çalışır. Skill
koşusu aynı sınırlarla yalnız seçilen skill'in ait olduğu paket dizinini
`--plugin-dir` üzerinden görür. Codex hakemi kullanıcı config ve proje
kurallarını yüklemez; ephemeral ve `read-only` sandbox içinde katı JSON şeması
ile yalnız kör A/B adaylarını değerlendirir. Hiçbir adaptör tehlikeli bypass
bayrağı kullanmaz.

İsteğe bağlı `DIVAN_CLAUDE_MODEL`, `DIVAN_CODEX_MODEL` ve
`DIVAN_EVAL_TIMEOUT` ortam değişkenleri model ve çağrı süresini sabitler. Bu yol
yerel Claude/Codex oturum haklarını kullanır ve sağlayıcı kullanım kotası
tüketebilir. Fixture testleri yalnız sözleşmeyi kanıtlar; kalite artışı iddiası
için yukarıdaki gerçek koşu ve kayıtlı provenance gerekir.

## Gerçek koşu provenance kaydı

Yayımlanabilir bir gerçek koşuda ajan, hakem ve ortam kimliğini sonuçla birlikte
saklamak için redakte edilmiş bir JSON dosyası verin. API anahtarı, kişisel veri,
müşteri verisi veya `sk-` ile başlayan herhangi bir değer eklemeyin:

```json
{
  "agent": "Declared runner",
  "agent_version": "1.2.3",
  "judge": "Independent judge",
  "judge_version": "4.5.6",
  "source_commit": "0123456789abcdef0123456789abcdef01234567",
  "environment": "Windows 11; redacted local environment"
}
```

```bash
python evals/run.py --run --skill kaynak-kuratori \
  --adapter "python adapter.py" \
  --judge "python judge.py" \
  --provenance provenance.json
```

Koşucu `source_commit` değerini temiz Git çalışma ağacının tam `HEAD` değeriyle
eşleştirir. Birinci taraf preset'inde Claude ve Codex sürümlerini doğrudan
CLI'lardan, Divan sürümünü `VERSION` dosyasından, işletim sistemi bilgisini de
çalışan ortamdan türetir; beyan edilen değerleri kanıt saymaz. Kamu sonucuna
yazmadan önce secret, e-posta ve kullanıcı-home yolu örüntülerini redakte eder.
Kör A/B adaylarının baseline/skill eşlemesi ile `winner_condition` yalnız ayrı
anahtar dosyasında kalır; kamu dosyasında adaylar A/B etiketiyle, kör rubrik
skorları ve toplu sayımlarla bulunur. Provenance tek başına
kalite kanıtı değildir. v0.12.0 için yayımlanan ilk gerçek koşu
`evals/results/claude-codex-baglam-muhafizi-v012.json` dosyasındadır: Claude Code
2.1.209 / `claude-sonnet-5` ajanı ile Codex CLI 0.144.4 /
`gpt-5.6-terra` kör hakemi üç vakayı değerlendirdi; skill koşulu sıfır, baseline
bir vaka kazandı ve iki beraberlik çıktı. Eşik önceden belirlenmediği ve skill
galibiyeti bulunmadığı için sonuç kalite artışı veya release-geçiş iddiası
değildir; yalnız gerçek
ajan/hakem kapısının denetlenebilir çalıştırma kanıtıdır. Ham körleme seed'i,
eşleme, vaka gerekçeleri, kazanan etiketi ve `winner_condition` özel anahtar
dosyasında kalmış, repoya alınmamıştır. Yayımlanabilir preset dışarıdan `--seed`
kabul etmez; OS CSPRNG ile `secrets.token_bytes(32)` üretir. Kamu provenance'ında
seed'in yalnız SHA-256 taahhüdü, 256 bit uzunluğu ve üretim yöntemi bulunur.

## Otomatik hakem ve kapı

```bash
python evals/run.py --run \
  --skill kaynak-kuratori \
  --adapter "python /guvenilir/yol/agent_adapter.py" \
  --judge "python /guvenilir/yol/judge_adapter.py" \
  --min-skill-win-rate 0.60
```

Hakem; prompt, beklenen çıktı, rubrik ve kör A/B adaylarını alır. Şunu döndürür:

```json
{
  "winner": "A",
  "reasons": ["Lisans kapısını uyguladı"],
  "expectation_scores": {"Lisans kapısını uygular": true}
}
```

Eşik sağlanmazsa komut `2` ile çıkar. Tek bir model/hakem sonucu evrensel kalite
kanıtı değildir; adaptör, model, prompt ve koşu ortamı sonuç kaydıyla birlikte
saklanmalıdır.

## OpenAI ile kullanım

OpenAI Agents SDK uygulaması adaptör protokolünü uygulayabilir. Resmî yaklaşımda
önce trace'lerle davranış hataları bulunur; iyi davranış tanımlanınca dataset ve
tekrarlanabilir eval koşularına geçilir. Divan koşucusu bu ikinci aşamanın yerel,
sağlayıcı-bağımsız kayıt katmanıdır. API anahtarını bu repoya veya sonuçlara
yazmayın.

- Agents: https://developers.openai.com/api/docs/guides/agents
- Agent evals: https://developers.openai.com/api/docs/guides/agent-evals
