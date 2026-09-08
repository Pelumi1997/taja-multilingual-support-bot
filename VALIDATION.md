# Validation record

Validated on **4 September 2026** in the build environment.

## Automated checks completed

- Python source compilation: passed
- Knowledge-base schema validation: 7 entries passed
- Pytest suite: 22 tests passed
- Measured test coverage: 86% across the application package
- Retrieval evaluation: 35 of 35 hand-curated development queries matched the intended FAQ
- Control-character scan: passed
- Repository secret-pattern scan: passed after excluding documented placeholders
- API smoke tests: health, browser demo, chat endpoint and dry-run Gupshup webhook passed
- Python wheel packaging: passed; package data included
- GitHub Actions workflow: present; its hosted CI run will begin after the first push

## Scope and limits

The retrieval dataset is deliberately small and transparent. A perfect result on that set is not evidence of production accuracy. The service has not been connected to Taja's live customer channels, help desk, production Redis instance or customer data in this build environment. Fluent-speaker and compliance review remain required before production deployment. The Docker image and live OpenAI/Gupshup/Redis integrations were not exercised in this build environment.
