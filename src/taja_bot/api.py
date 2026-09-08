from __future__ import annotations

import hashlib
import hmac
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from taja_bot import __version__
from taja_bot.adapters.gupshup import GupshupAdapter
from taja_bot.config import Settings, get_settings
from taja_bot.models import (
    ChatRequest,
    ChatResponse,
    GupshupDelivery,
    GupshupWebhookResponse,
    HealthResponse,
    LanguageCode,
    LanguageOption,
    PublicFaq,
)
from taja_bot.services.chat import ChatService
from taja_bot.services.faq import FaqService
from taja_bot.services.generation import build_answer_generator
from taja_bot.services.language import LanguageService
from taja_bot.services.safety import SafetyService
from taja_bot.services.session import build_session_store

logger = logging.getLogger("taja_bot")
PACKAGE_DIR = Path(__file__).resolve().parent


def build_services(settings: Settings) -> dict[str, Any]:
    faq_service = FaqService(settings.faq_data_path)
    language_service = LanguageService()
    safety_service = SafetyService()
    answer_generator = build_answer_generator(settings)
    session_store = build_session_store(
        backend=settings.session_backend,
        redis_url=settings.redis_url,
        ttl_seconds=settings.session_ttl_seconds,
    )
    chat_service = ChatService(
        settings=settings,
        faq_service=faq_service,
        language_service=language_service,
        safety_service=safety_service,
        session_store=session_store,
        answer_generator=answer_generator,
    )
    return {
        "faq": faq_service,
        "language": language_service,
        "chat": chat_service,
        "gupshup": GupshupAdapter(settings),
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    app.state.settings = settings
    app.state.services = build_services(settings)
    yield


app = FastAPI(
    title="Taja Multilingual Support Bot",
    version=__version__,
    description="Python-first multilingual FAQ assistant for Taja customer support.",
    lifespan=lifespan,
)
settings_for_middleware = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_for_middleware.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Webhook-Secret"],
)
app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")


def services(request: Request) -> dict[str, Any]:
    return request.app.state.services


def settings(request: Request) -> Settings:
    return request.app.state.settings


def pseudonymise_identifier(value: str, salt: str) -> str:
    return hmac.new(salt.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()[:24]


def verify_webhook_secret(
    app_settings: Settings,
    supplied: str | None,
) -> None:
    configured = app_settings.webhook_secret
    if not configured:
        if app_settings.environment == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Webhook authentication is not configured",
            )
        return
    if not supplied or not hmac.compare_digest(configured, supplied):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="index.html", context={"version": __version__})


@app.get("/health", response_model=HealthResponse, tags=["operations"])
async def health(request: Request) -> HealthResponse:
    service_map = services(request)
    app_settings = settings(request)
    return HealthResponse(
        status="ok",
        app=app_settings.app_name,
        version=__version__,
        knowledge_base_entries=len(service_map["faq"]),
    )


@app.get("/api/v1/languages", response_model=list[LanguageOption], tags=["chat"])
async def get_languages(request: Request) -> list[LanguageOption]:
    return services(request)["language"].options()


@app.get("/api/v1/faqs", response_model=list[PublicFaq], tags=["knowledge"])
async def get_faqs(
    request: Request,
    language: LanguageCode = Query(default=LanguageCode.ENGLISH),
) -> list[PublicFaq]:
    return services(request)["faq"].public_faqs(language)


@app.post("/api/v1/chat", response_model=ChatResponse, tags=["chat"])
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    response: ChatResponse = await services(request)["chat"].process(payload)
    logger.info(
        "chat_result session=%s intent=%s requires_human=%s confidence=%.3f",
        pseudonymise_identifier(payload.session_id, settings(request).pseudonymisation_salt)[:12],
        response.intent,
        response.requires_human,
        response.confidence,
    )
    return response


@app.post("/webhooks/gupshup", response_model=GupshupWebhookResponse, tags=["webhooks"])
async def gupshup_webhook(
    payload: dict[str, Any],
    request: Request,
    x_webhook_secret: str | None = Header(default=None),
) -> GupshupWebhookResponse:
    app_settings = settings(request)
    verify_webhook_secret(app_settings, x_webhook_secret)
    service_map = services(request)
    adapter: GupshupAdapter = service_map["gupshup"]
    parsed = adapter.parse(payload)

    if app_settings.gupshup_app_name and parsed.app_name != app_settings.gupshup_app_name:
        raise HTTPException(status_code=400, detail="Unexpected Gupshup app name")
    if parsed.event_type not in {"message", "user-event"} or not parsed.sender or not parsed.message:
        return GupshupWebhookResponse(accepted=False, detail="Event does not contain a supported text message")

    chatbot_response: ChatResponse = await service_map["chat"].process(
        ChatRequest(
            session_id=f"gupshup:{pseudonymise_identifier(parsed.sender, app_settings.pseudonymisation_salt)}",
            message=parsed.message,
            channel="gupshup-whatsapp",
        )
    )

    if not adapter.configured:
        return GupshupWebhookResponse(
            accepted=True,
            chatbot=chatbot_response,
            delivery=GupshupDelivery(attempted=False, delivered=False, mode="dry-run"),
        )

    provider_response = await adapter.send_text(parsed.sender, chatbot_response.reply)
    return GupshupWebhookResponse(
        accepted=True,
        chatbot=chatbot_response,
        delivery=GupshupDelivery(
            attempted=True,
            delivered=True,
            mode="live",
            provider_response=provider_response,
        ),
    )
