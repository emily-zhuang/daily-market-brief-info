from __future__ import annotations

from functools import lru_cache

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
    try:
        import requests

        response = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "auto", "tl": "zh-CN", "dt": "t", "q": text},
            timeout=15,
        )
        response.raise_for_status()
        translated = "".join(part[0] for part in response.json()[0] if part and part[0])
        if translated.strip():
            return translated.strip()
    except Exception:
        pass

    try:
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": "en|zh-CN"},
            timeout=15,
        )
        response.raise_for_status()
        translated = parse_mymemory_response(response.json())
        return translated or text
    except Exception:
        return text
