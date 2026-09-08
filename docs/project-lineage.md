# Architecture evolution

The Taja implementation builds on patterns from earlier Python/Flask multilingual chatbot work.

The earlier architecture used Flask webhooks, Redis session state, language-specific conversation flows and WhatsApp messaging.

For this project, those ideas were reworked into a more modular FastAPI application with:

- data-driven multilingual FAQ content
- hybrid information retrieval
- separated service components
- safer handling of sensitive messages
- optional AI-assisted responses
- automated testing and CI
- Docker-based deployment support

The result is a cleaner architecture designed specifically around Taja's customer-support use case.
