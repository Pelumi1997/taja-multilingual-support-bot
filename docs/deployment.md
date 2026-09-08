# Deployment guide

## Docker Compose

```bash
cp .env.example .env
# Edit .env and set unique secrets.
docker compose up --build
```

The Compose setup uses Redis so language preferences are shared across the two Uvicorn workers.

## Required production settings

- `ENVIRONMENT=production`
- `SESSION_BACKEND=redis`
- `REDIS_URL`
- `WEBHOOK_SECRET`
- `PSEUDONYMISATION_SALT`
- `ALLOWED_ORIGINS`

The webhook secret and pseudonymisation salt must be different random values.

## Reverse proxy

Terminate TLS at a trusted reverse proxy or cloud load balancer. Forward only the required paths, preserve the client IP in trusted headers and apply rate limits.

## Data protection

The reference implementation stores only language preference. It does not persist messages or escalation cases. Before adding persistence:

1. agree a lawful purpose and retention period;
2. minimise personal data;
3. encrypt data in transit and at rest;
4. restrict staff access;
5. create deletion and data-subject workflows;
6. prohibit secrets and complete payment-card data;
7. document incident response.

## Support-system integration

`ChatResponse.requires_human` is a routing instruction, not proof that a ticket was created. Connect it to an authorised help desk or CRM and record the returned ticket ID before telling a customer that a case has been opened.

## Scaling

- Use Redis sessions for more than one worker or instance.
- Keep the knowledge base in the application image for deterministic releases.
- Use blue/green or rolling deployments after knowledge changes.
- Monitor response latency, unmatched questions, escalation rate and provider failures.
