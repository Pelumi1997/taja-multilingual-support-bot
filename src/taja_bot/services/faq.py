from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rapidfuzz.fuzz import WRatio
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from taja_bot.models import LanguageCode, PublicFaq, SourceReference


@dataclass(frozen=True)
class MatchResult:
    faq: dict[str, Any]
    score: float


class FaqService:
    """Load, validate and retrieve multilingual FAQ entries."""

    def __init__(self, data_path: Path) -> None:
        self.data_path = data_path
        self.data = json.loads(data_path.read_text(encoding="utf-8"))
        self._validate()
        self.faqs: list[dict[str, Any]] = self.data["faqs"]
        self.ui: dict[str, dict[str, str]] = self.data["ui"]
        self.languages: tuple[str, ...] = tuple(self.data["languages"])
        self._candidate_rows: list[tuple[int, str]] = []
        corpus: list[str] = []
        for faq_index, faq in enumerate(self.faqs):
            for language in self.languages:
                phrases = faq["questions"].get(language, []) + faq["keywords"].get(language, [])
                if not phrases:
                    continue
                document = " ".join(phrases)
                self._candidate_rows.append((faq_index, language))
                corpus.append(document)
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            lowercase=True,
            strip_accents="unicode",
            min_df=1,
        )
        self.matrix = self.vectorizer.fit_transform(corpus)

    def _validate(self) -> None:
        required_languages = {language.value for language in LanguageCode}
        if set(self.data.get("languages", [])) != required_languages:
            raise ValueError("Knowledge base languages must exactly match the supported language codes")
        seen: set[str] = set()
        for faq in self.data.get("faqs", []):
            faq_id = faq.get("id")
            if not faq_id or faq_id in seen:
                raise ValueError(f"FAQ id must be present and unique: {faq_id!r}")
            seen.add(faq_id)
            for field in ("questions", "answers", "keywords"):
                if field not in faq:
                    raise ValueError(f"FAQ {faq_id} is missing {field}")
            for language in required_languages:
                if language not in faq["answers"]:
                    raise ValueError(f"FAQ {faq_id} has no answer for {language}")
            if not faq.get("sources"):
                raise ValueError(f"FAQ {faq_id} must include at least one source")

    @staticmethod
    def normalise(value: str) -> str:
        value = unicodedata.normalize("NFKC", value).casefold()
        value = re.sub(r"[^\w\s'-]", " ", value, flags=re.UNICODE)
        return re.sub(r"\s+", " ", value).strip()

    def __len__(self) -> int:
        return len(self.faqs)

    def text(self, key: str, language: LanguageCode) -> str:
        language_map = self.ui.get(key, {})
        return language_map.get(language.value) or language_map.get("en") or key

    def menu(self, language: LanguageCode) -> str:
        lines = [self.text("faq_menu_intro", language)]
        for index, faq in enumerate(self.faqs[:6], start=1):
            question = faq["questions"][language.value][0]
            lines.append(f"{index}. {question}")
        lines.append(self.text("menu_help", language))
        return "\n".join(lines)

    def language_menu(self) -> str:
        return self.text("language_menu", LanguageCode.ENGLISH)

    def _direct_number_match(self, message: str) -> MatchResult | None:
        value = self.normalise(message)
        if value.isdigit():
            index = int(value) - 1
            if 0 <= index < min(6, len(self.faqs)):
                return MatchResult(self.faqs[index], 1.0)
        return None

    def match(self, message: str, language: LanguageCode) -> MatchResult:
        direct = self._direct_number_match(message)
        if direct is not None:
            return direct

        query = self.normalise(message)
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.matrix)[0]

        scores: dict[int, float] = {}
        for row_index, (faq_index, candidate_language) in enumerate(self._candidate_rows):
            if candidate_language not in {language.value, "en"}:
                language_weight = 0.86
            else:
                language_weight = 1.0
            faq = self.faqs[faq_index]
            phrases = faq["questions"].get(candidate_language, []) + faq["keywords"].get(candidate_language, [])
            fuzzy = max((WRatio(query, self.normalise(phrase)) for phrase in phrases), default=0) / 100.0
            score = (0.72 * float(similarities[row_index]) + 0.28 * fuzzy) * language_weight

            keyword_hits = sum(
                1
                for keyword in faq["keywords"].get(language.value, [])
                if self.normalise(keyword) and self.normalise(keyword) in query
            )
            if keyword_hits:
                score = min(1.0, score + min(0.16, 0.04 * keyword_hits))
            scores[faq_index] = max(scores.get(faq_index, 0.0), score)

        best_index, best_score = max(scores.items(), key=lambda item: item[1])
        return MatchResult(self.faqs[best_index], round(float(best_score), 4))

    @staticmethod
    def sources(faq: dict[str, Any]) -> list[SourceReference]:
        return [SourceReference.model_validate(source) for source in faq["sources"]]

    def answer(self, faq: dict[str, Any], language: LanguageCode) -> str:
        return faq["answers"].get(language.value) or faq["answers"]["en"]

    def public_faqs(self, language: LanguageCode) -> list[PublicFaq]:
        result: list[PublicFaq] = []
        for faq in self.faqs:
            result.append(
                PublicFaq(
                    id=faq["id"],
                    category=faq["category"],
                    question=faq["questions"][language.value][0],
                    answer=self.answer(faq, language),
                    sources=self.sources(faq),
                )
            )
        return result
