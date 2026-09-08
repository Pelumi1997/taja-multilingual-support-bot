from taja_bot.models import LanguageCode
from taja_bot.services.language import LanguageService


def test_menu_selection() -> None:
    service = LanguageService()
    assert service.parse_selection("1") == LanguageCode.ENGLISH
    assert service.parse_selection("4") == LanguageCode.PIDGIN
    assert service.parse_selection("Yorùbá") == LanguageCode.YORUBA


def test_conservative_detection() -> None:
    service = LanguageService()
    assert service.detect("Abeg how long transfer go take?") == LanguageCode.PIDGIN
    assert service.detect("Ta yaya zan fara?") == LanguageCode.HAUSA
    assert service.detect("Kedu ka m ga-esi malite?") == LanguageCode.IGBO
    assert service.detect("Jọwọ, bawo ni mo ṣe le bẹrẹ?") == LanguageCode.YORUBA
    assert service.detect("How do I start?") == LanguageCode.ENGLISH
