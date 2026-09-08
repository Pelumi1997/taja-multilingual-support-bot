# Optional RAG answer mode

## Purpose

The retrieval layer selects one approved multilingual FAQ record using TF-IDF, fuzzy similarity and keyword signals. In deterministic mode, the stored answer is returned unchanged. In OpenAI mode, that retrieved answer becomes the only factual context for a constrained generation step.

This design keeps the system usable without a model and makes failures safe: a timeout, provider error or empty model response returns the reviewed answer.

## Enable it

```env
ANSWER_MODE=openai
OPENAI_API_KEY=replace-with-server-side-key
OPENAI_MODEL=gpt-5.6-luna
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_TIMEOUT_SECONDS=20
```

The implementation calls the OpenAI Responses API over server-side HTTPS. Never expose the API key in the browser, Git repository or customer-channel payload.

## Data sent to the model

For routine, supported questions only:

- the redacted customer question;
- requested language;
- retrieved FAQ identifier;
- the reviewed answer in that language;
- public source URLs for provenance.

Fraud, complaints, account-access problems, restricted-advice requests and unsupported questions bypass generation.

## Guardrails

The system prompt prohibits new facts, fees, rates, timings, destinations, account decisions and promises. It also prohibits credential collection and investment, legal or tax advice. These instructions reduce risk but do not replace evaluation, monitoring or human review.

## Audit fields

`ChatResponse.answer_mode` is one of:

- `deterministic`
- `openai-rag`
- `deterministic-fallback`

`generation_fallback=true` records that a configured provider failed and the stored answer was returned.
