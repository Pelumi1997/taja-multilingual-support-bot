# ADR 0003: Make Redis optional but required for distributed sessions

- **Status:** Accepted
- **Date:** 2026-09-04

## Context

Local contributors need a one-command development path, while production deployments may use multiple workers or instances.

## Decision

Use an in-memory session store by default and provide a Redis implementation through the same interface. Docker Compose enables Redis automatically.

## Consequences

Local development has no infrastructure dependency. Production operators must configure Redis to keep language state consistent across processes.
