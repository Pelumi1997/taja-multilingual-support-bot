# API reference

Interactive OpenAPI documentation is available at `/docs` while the service is running.

## `GET /health`

Returns service status and the number of knowledge-base entries loaded.

## `GET /api/v1/languages`

Returns the five supported languages and their menu numbers.

## `GET /api/v1/faqs?language=yo`

Returns the public FAQ list in the requested language, including source links.

## `POST /api/v1/chat`

Request:

```json
{
  "session_id": "customer-001",
  "message": "Can I convert crypto to cash?",
  "language": "en",
  "channel": "website",
  "metadata": {}
}
```

Response fields:

| Field | Meaning |
|---|---|
| `reply` | Customer-facing response |
| `intent` | Routine, complaint, fraud/security, account access, restricted advice, unsupported or menu |
| `matched_faq_id` | Knowledge-base entry used for a routine answer |
| `confidence` | Retrieval score from 0 to 1; it is not a calibrated probability |
| `requires_human` | Whether the application requires a human route |
| `escalation_priority` | None, normal, high or critical |
| `case_reference` | Stable customer-facing reference for a human-review request |
| `sources` | Public pages supporting the answer |
| `answer_mode` | Deterministic, OpenAI RAG or deterministic fallback |
| `generation_fallback` | Whether a configured generator failed and the approved answer was returned |
| `redacted_input` | Present only when sensitive material was removed |

## `POST /webhooks/gupshup`

Send the configured value of `WEBHOOK_SECRET` in the `X-Webhook-Secret` header.

The endpoint recognises message and opted-in events based on the structure used by the legacy Gupshup integration. It returns dry-run output unless all three Gupshup credentials are configured.

Do not place this endpoint directly on the public internet without rate limiting, provider verification, request-size controls and monitoring.
