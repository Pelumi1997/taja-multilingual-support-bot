# Security policy

## Reporting

Do not open a public issue containing credentials, customer data or details of an exploitable vulnerability. Report security issues privately to the repository owner or Taja's authorised security contact.

## Supported version

Only the latest release on the default branch is supported during the reference-implementation stage.

## Secrets

- Never commit `.env`, API keys, Redis credentials, customer exports or `dump.rdb`.
- Rotate a secret immediately if it appears in a commit.
- Use a different value for `WEBHOOK_SECRET` and `PSEUDONYMISATION_SALT`.
- Do not log raw payment credentials or authentication secrets.

## Production review

Before production use, complete threat modelling, dependency scanning, penetration testing, provider-signature validation, rate limiting, access control, incident response and data-protection review.
