from __future__ import annotations

import re
import unicodedata

from taja_bot.models import LanguageCode, LanguageOption


LANGUAGE_OPTIONS = [
    LanguageOption(code=LanguageCode.ENGLISH, name="English", native_name="English", menu_number=1),
    LanguageOption(code=LanguageCode.HAUSA, name="Hausa", native_name="Hausa", menu_number=2),
    LanguageOption(code=LanguageCode.IGBO, name="Igbo", native_name="Igbo", menu_number=3),
    LanguageOption(code=LanguageCode.PIDGIN, name="Nigerian Pidgin", native_name="Naija Pidgin", menu_number=4),
    LanguageOption(code=LanguageCode.YORUBA, name="Yoruba", native_name="Yorùbá", menu_number=5),
]

MENU_SELECTIONS = {str(option.menu_number): option.code for option in LANGUAGE_OPTIONS}
ALIASES: dict[str, LanguageCode] = {
    "english": LanguageCode.ENGLISH,
    "en": LanguageCode.ENGLISH,
    "hausa": LanguageCode.HAUSA,
    "ha": LanguageCode.HAUSA,
    "igbo": LanguageCode.IGBO,
    "ig": LanguageCode.IGBO,
    "pidgin": LanguageCode.PIDGIN,
    "nigerian pidgin": LanguageCode.PIDGIN,
    "naija pidgin": LanguageCode.PIDGIN,
    "pcm": LanguageCode.PIDGIN,
    "yoruba": LanguageCode.YORUBA,
    "yorùbá": LanguageCode.YORUBA,
    "yo": LanguageCode.YORUBA,
}

LANGUAGE_HINTS: dict[LanguageCode, set[str]] = {
    LanguageCode.PIDGIN: {
        "abeg", "dey", "wetin", "una", "fit", "no be", "how far", "make i", "my money never",
    },
    LanguageCode.HAUSA: {
        "yaya", "kudi", "ina", "ta yaya", "zan", "ake", "don Allah", "aika", "asusun",
    },
    LanguageCode.IGBO: {
        "kedu", "ego", "biko", "anyị", "ị", "ọrụ", "zipu", "akaụntụ", "ọtụtụ",
    },
    LanguageCode.YORUBA: {
        "bawo", "jọwọ", "owó", "owo", "ṣe", "ní", "lati", "mo fẹ", "fi ranṣẹ", "àkọọlẹ",
    },
}


class LanguageService:
    """Resolve explicit selections and perform conservative language detection."""

    @staticmethod
    def normalise(value: str) -> str:
        value = unicodedata.normalize("NFKC", value).casefold().strip()
        value = re.sub(r"\s+", " ", value)
        return value

    def parse_selection(self, value: str) -> LanguageCode | None:
        normalised = self.normalise(value)
        return MENU_SELECTIONS.get(normalised) or ALIASES.get(normalised)

    def detect(self, message: str) -> LanguageCode:
        normalised = self.normalise(message)
        scores: dict[LanguageCode, int] = {language: 0 for language in LANGUAGE_HINTS}
        for language, hints in LANGUAGE_HINTS.items():
            for hint in hints:
                if self.normalise(hint) in normalised:
                    scores[language] += max(1, len(hint.split()))
        best_language, best_score = max(scores.items(), key=lambda item: item[1])
        return best_language if best_score > 0 else LanguageCode.ENGLISH

    def resolve(
        self,
        *,
        explicit: LanguageCode | None,
        message: str,
        stored: LanguageCode | None,
    ) -> LanguageCode:
        if explicit is not None:
            return explicit
        if stored is not None:
            return stored
        selected = self.parse_selection(message)
        if selected is not None:
            return selected
        return self.detect(message)

    @staticmethod
    def options() -> list[LanguageOption]:
        return LANGUAGE_OPTIONS.copy()
