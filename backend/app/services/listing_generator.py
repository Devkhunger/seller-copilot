from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def generate_listing(payload) -> dict:
    base_listing = _fallback_listing(payload)
    keyword_plan = _generate_trend_keyword_plan(payload)
    if not keyword_plan:
        return base_listing

    ranked_keywords = keyword_plan["ranked_keywords"]
    top_keyword = ranked_keywords[0]["keyword"] if ranked_keywords else ""
    listing = dict(base_listing)
    listing["keywords"] = [item["keyword"] for item in ranked_keywords]
    listing["keyword_rankings"] = ranked_keywords
    listing["trend_note"] = keyword_plan["trend_note"]
    listing["trend_source"] = keyword_plan["trend_source"]

    if top_keyword:
        listing["seo_title"] = _blend_title_with_keyword(base_listing["seo_title"], top_keyword)
        listing["short_description"] = (
            f"{base_listing['short_description']} Keyword focus: {top_keyword}."
        )
        listing["bullet_points"] = base_listing["bullet_points"] + [
            f"Trending keyword focus: {top_keyword}."
        ]
        listing["platform_text"] = (
            f"{base_listing['platform_text']} Prioritize the ranking keywords in the title, description, bullets, and images."
        )
    return listing


def _generate_trend_keyword_plan(payload) -> dict[str, Any] | None:
    candidates = _gemini_keyword_candidates(payload)
    if not candidates:
        candidates = _fallback_keyword_candidates(payload)

    ranked_keywords = _rank_keywords_with_trends(candidates, payload)
    if not ranked_keywords:
        return None

    trend_source = ranked_keywords[0].get("source", "fallback")
    top = ranked_keywords[0]
    trend_note = (
        f"Top keyword today: {top['keyword']} (trend score {top['trend_score']}/100)."
    )
    if trend_source != "pytrends":
        trend_note = (
            f"Trend scores were estimated because pytrends was unavailable. Top keyword: {top['keyword']}."
        )

    return {
        "ranked_keywords": ranked_keywords,
        "trend_note": trend_note,
        "trend_source": trend_source,
    }


def _gemini_keyword_candidates(payload) -> list[str]:
    if not _has_gemini_key():
        return []

    prompt = _build_keyword_prompt(payload)
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.35,
            "responseMimeType": "application/json",
            "responseJsonSchema": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 8,
                        "maxItems": 20,
                    }
                },
                "required": ["keywords"],
            },
        },
    }

    request = urllib.request.Request(
        GEMINI_API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": _gemini_api_key(),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return []

    text = _extract_gemini_text(raw)
    if not text:
        return []

    try:
        parsed = _extract_json_object(text)
    except ValueError:
        return []

    keywords = parsed.get("keywords", []) if isinstance(parsed, dict) else []
    cleaned = _normalize_keywords(keywords)
    return cleaned[:20]


def _rank_keywords_with_trends(candidates: list[str], payload) -> list[dict[str, Any]]:
    unique_candidates = _normalize_keywords(candidates)
    if not unique_candidates:
        return []

    try:
        from pytrends.request import TrendReq
    except Exception:
        return _rank_keywords_without_trends(unique_candidates, payload)

    trend_client = TrendReq(hl="en-US", tz=330, timeout=(5, 15), retries=1, backoff_factor=0.2)
    ranked: list[dict[str, Any]] = []
    for keyword in unique_candidates:
        trend_score = _trend_score_for_keyword(trend_client, keyword)
        relevance_score = _relevance_score(keyword, payload)
        combined_score = round((trend_score * 0.7) + (relevance_score * 0.3), 1)
        ranked.append(
            {
                "keyword": keyword,
                "trend_score": round(trend_score, 1),
                "relevance_score": round(relevance_score, 1),
                "combined_score": combined_score,
                "source": "pytrends",
            }
        )

    ranked.sort(key=lambda item: (item["combined_score"], item["trend_score"]), reverse=True)
    return ranked


def _rank_keywords_without_trends(candidates: list[str], payload) -> list[dict[str, Any]]:
    ranked = []
    for keyword in candidates:
        relevance_score = _relevance_score(keyword, payload)
        ranked.append(
            {
                "keyword": keyword,
                "trend_score": round(relevance_score, 1),
                "relevance_score": round(relevance_score, 1),
                "combined_score": round(relevance_score, 1),
                "source": "fallback",
            }
        )
    ranked.sort(key=lambda item: item["combined_score"], reverse=True)
    return ranked


def _trend_score_for_keyword(trend_client, keyword: str) -> float:
    try:
        trend_client.build_payload([keyword], cat=0, timeframe="today 12-m", geo="", gprop="")
        interest = trend_client.interest_over_time()
    except Exception:
        return 0.0

    if interest.empty or keyword not in interest.columns:
        return 0.0

    series = interest[keyword].dropna()
    if series.empty:
        return 0.0
    return float(series.tail(26).mean())


def _relevance_score(keyword: str, payload) -> float:
    haystack = " ".join(
        [payload.product_name, payload.fabric, payload.color, payload.size, payload.design, payload.platform]
    ).lower()
    keyword_lower = keyword.lower()
    tokens = [token for token in re.split(r"[^a-z0-9]+", keyword_lower) if token]
    if not tokens:
        return 0.0

    matches = sum(1 for token in tokens if token in haystack)
    exact_hits = 1 if payload.product_name.lower() in keyword_lower else 0
    platform_hits = 1 if payload.platform.lower() in keyword_lower else 0
    score = 20 + (matches * 18) + (exact_hits * 22) + (platform_hits * 10)
    return max(0.0, min(100.0, float(score)))


def _build_keyword_prompt(payload) -> str:
    return f"""
You are an ecommerce SEO specialist.
Generate keyword phrases for a marketplace listing.
Return JSON only with this structure:
{{
  "keywords": ["keyword phrase 1", "keyword phrase 2", "keyword phrase 3"]
}}

Rules:
- Return 12 to 20 keyword phrases.
- Keep phrases short and buyer-focused.
- Use lowercase phrases.
- Avoid duplicate or near-duplicate phrases.
- Include core product, material, color, size, style, and use-case phrases.
- Do not include brand names unless the user explicitly gave one.
- Prefer phrases that help search ranking on {payload.platform}.

Product name: {payload.product_name}
Fabric: {payload.fabric or 'not provided'}
Color: {payload.color or 'not provided'}
Size: {payload.size or 'not provided'}
Design: {payload.design or 'not provided'}
Platform: {payload.platform}
""".strip()


def _extract_gemini_text(raw: dict[str, Any]) -> str:
    candidates = raw.get("candidates") or []
    if not candidates:
        return ""
    content = candidates[0].get("content") or {}
    parts = content.get("parts") or []
    for part in parts:
        text = part.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()
    return ""


def _extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found")
    parsed = json.loads(cleaned[start:end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("Expected JSON object")
    return parsed


def _normalize_keywords(keywords: list[Any]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in keywords:
        keyword = str(item).strip().lower()
        keyword = re.sub(r"\s+", " ", keyword)
        if not keyword:
            continue
        if keyword in seen:
            continue
        seen.add(keyword)
        cleaned.append(keyword)
    return cleaned


def _fallback_keyword_candidates(payload) -> list[str]:
    return _normalize_keywords(
        [
            payload.product_name,
            payload.color,
            payload.fabric,
            payload.size,
            payload.design,
            f"{payload.product_name} online",
            f"{payload.product_name} for home decor",
            f"{payload.color} {payload.product_name}".strip(),
            f"{payload.fabric} {payload.product_name}".strip(),
            f"{payload.size} {payload.product_name}".strip(),
            f"{payload.design} {payload.product_name}".strip(),
            f"{payload.product_name} {payload.platform}".strip(),
            "home decor",
            "sofa decor",
            "premium quality",
            "stylish home furnishing",
        ]
    )


def _fallback_listing(payload) -> dict:
    parts = [payload.color, payload.fabric, payload.product_name, payload.size, payload.design]
    clean_parts = [part.strip() for part in parts if part and part.strip()]
    title = "Premium " + " ".join(clean_parts)
    primary_keyword = payload.product_name.strip()
    if payload.platform.lower() == "amazon":
        title += " for Home Decor, Sofa and Living Room"
    elif payload.platform.lower() == "flipkart":
        title += " | Stylish Home Furnishing"
    else:
        title += " for Reselling and Home Use"
    keywords = _fallback_keyword_candidates(payload)
    if keywords:
        primary_keyword = keywords[0]
        if primary_keyword.lower() not in title.lower():
            title = f"{title} | {primary_keyword.title()}"
    relevance_ranking = [
        {
            "keyword": keyword,
            "trend_score": 0.0,
            "relevance_score": round(_relevance_score(keyword, payload), 1),
            "combined_score": round(_relevance_score(keyword, payload), 1),
            "source": "fallback",
        }
        for keyword in keywords
    ]
    return {
        "seo_title": title[:150],
        "short_description": f"{payload.color} {payload.product_name} made with {payload.fabric}. Keyword focus: {primary_keyword}. Suitable for buyers looking for a neat, durable and attractive product.",
        "bullet_points": [
            f"Material: {payload.fabric or 'quality fabric'} with a comfortable finish.",
            f"Color and design: {payload.color or 'attractive color'} {payload.design or 'modern design'}.",
            f"Size: {payload.size or 'standard marketplace size'}; mention exact dimensions in images.",
            "Use clear photos and care instructions to reduce return and RTO risk.",
        ],
        "keywords": keywords,
        "keyword_rankings": relevance_ranking,
        "trend_note": "Trend scores will appear when Gemini and pytrends are configured.",
        "trend_source": "fallback",
        "platform_text": f"For {payload.platform}, keep the first image clean, mention size early, and include searchable keywords in the title, description, and bullets.",
    }


def _blend_title_with_keyword(title: str, keyword: str) -> str:
    normalized_title = title.strip()
    normalized_keyword = keyword.strip()
    if not normalized_keyword:
        return normalized_title
    if normalized_keyword.lower() in normalized_title.lower():
        return normalized_title
    suffix = f" | {normalized_keyword.title()}"
    return (normalized_title + suffix)[:150]


def _has_gemini_key() -> bool:
    return bool(_gemini_api_key())


def _gemini_api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()
