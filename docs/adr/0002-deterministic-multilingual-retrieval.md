# ADR 0002: Use deterministic multilingual retrieval for published FAQs

- **Status:** Accepted
- **Date:** 2026-09-04

## Context

The support domain is small, fintech information is sensitive and the public FAQ set is bounded. Free-form generation would add hallucination and translation risk.

## Decision

Store reviewed answers and question variants in five languages. Retrieve them with character n-gram TF-IDF, fuzzy matching and keyword signals. Return the stored answer and source links unchanged.

## Consequences

Responses are auditable and inexpensive. Editors must maintain translations, and questions outside the approved domain must be routed to humans rather than improvised.
