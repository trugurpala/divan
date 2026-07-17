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
