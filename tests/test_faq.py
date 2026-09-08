from taja_bot.models import LanguageCode
from taja_bot.services.faq import FaqService


def test_direct_menu_match(settings) -> None:
    service = FaqService(settings.faq_data_path)
    result = service.match("3", LanguageCode.ENGLISH)
    assert result.faq["id"] == "crypto-to-cash"
    assert result.score == 1.0


def test_multilingual_retrieval(settings) -> None:
    service = FaqService(settings.faq_data_path)
    cases = [
        ("How long does transfer take?", LanguageCode.ENGLISH, "transfer-speed"),
        ("I wan cash out crypto", LanguageCode.PIDGIN, "crypto-to-cash"),
        ("Wadanne kasashe ake tallafawa?", LanguageCode.HAUSA, "supported-countries"),
        ("Akaụntụ m ọ dị nchebe?", LanguageCode.IGBO, "security"),
        ("Mo fẹ ṣẹda akọọlẹ", LanguageCode.YORUBA, "get-started"),
    ]
    for query, language, expected in cases:
        result = service.match(query, language)
        assert result.faq["id"] == expected
        assert result.score >= 0.52


def test_public_faqs_include_sources(settings) -> None:
    service = FaqService(settings.faq_data_path)
    faqs = service.public_faqs(LanguageCode.ENGLISH)
    assert len(faqs) == 7
    assert all(faq.sources for faq in faqs)
