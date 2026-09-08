# Taja Multilingual Support Bot

A Python-based multilingual customer-support chatbot for **Taja (Itaja Innovations Ltd)**.

The bot is designed to answer common customer FAQs in:

- English
- Hausa
- Igbo
- Nigerian Pidgin
- Yoruba

It uses Taja's published FAQ and product information as its knowledge source and routes sensitive cases such as complaints, suspected fraud and account-related issues to human support.

## Features

- Multilingual FAQ support
- TF-IDF, fuzzy matching and keyword-based retrieval
- Optional AI-assisted responses
- Human escalation for sensitive cases
- FastAPI REST API
- Redis session support
- WhatsApp/Gupshup integration
- Browser demo
- Automated tests with GitHub Actions

## Run locally

```bash
git clone https://github.com/Pelumi1997/taja-multilingual-support-bot.git
cd taja-multilingual-support-bot

python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"

cp .env.example .env
uvicorn taja_bot.api:app --reload
