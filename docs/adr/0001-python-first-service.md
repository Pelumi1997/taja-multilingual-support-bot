# ADR 0001: Use a Python-first service

- **Status:** Accepted
- **Date:** 2026-09-04

## Context

The project has an earlier Python/Flask design lineage and needs a testable API that can connect to web and WhatsApp channels without coupling business logic to a workflow platform.

## Decision

Use Python 3.11+ and FastAPI with a service-oriented package structure. Transport adapters remain optional and call the same `ChatService`.

## Consequences

The implementation is portable, testable and independent of a particular messaging provider. Deployment teams must still operate an API runtime and Redis when scaling horizontally.
