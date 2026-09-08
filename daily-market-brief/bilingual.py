from __future__ import annotations

from functools import lru_cache

import requests


class TranslationError(RuntimeError):
    """Raised when a news item cannot be translated into Chinese."""


def bilingual_block(title_zh: str, title_en: str, summary_zh: str, summary_en: str) -> str:
    return (
        f"中文：{title_zh}\n"
        f"English: {title_en}\n"
        f"中文摘要：{summary_zh}\n"
        f"English summary：{summary_en}"
    )


def parse_mymemory_response(payload: dict) -> str:
    return str(payload.get("responseData", {}).get("translatedText", "")).strip()


def _has_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


@lru_cache(maxsize=256)
def translate_to_chinese(text: str) -> str:
    text = (text or "").strip()
    if not text or _has_cjk(text):
        return text
    errors: list[str] = []
    headers = {"User-Agent": "daily-market-brief/1.0"}

    try:
        response = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "auto", "tl": "zh-CN", "dt": "t", "q": text},
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        translated = "".join(part[0] for part in payload[0] if part and part[0])
        if _has_cjk(translated):
            return translated.strip()
        errors.append("Google Translate returned no Chinese characters")
    except Exception as exc:
        errors.append(f"Google Translate: {exc}")

    try:
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": "en|zh-CN"},
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        translated = parse_mymemory_response(response.json())
        if _has_cjk(translated):
            return translated
        errors.append("MyMemory returned no Chinese characters")
    except Exception as exc:
        errors.append(f"MyMemory: {exc}")

    raise TranslationError(
        "No Chinese translation was produced; refusing to send an untranslated report. "
        + " | ".join(errors)
    )
