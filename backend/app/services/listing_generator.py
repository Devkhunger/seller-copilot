from app.services.ai_service import has_llm_key


def generate_listing(payload) -> dict:
    if has_llm_key():
        # Provider-specific LLM code can be added here later.
        return _fallback_listing(payload)
    return _fallback_listing(payload)


def _fallback_listing(payload) -> dict:
    parts = [payload.color, payload.fabric, payload.product_name, payload.size, payload.design]
    clean_parts = [part.strip() for part in parts if part and part.strip()]
    title = "Premium " + " ".join(clean_parts)
    if payload.platform.lower() == "amazon":
        title += " for Home Decor, Sofa and Living Room"
    elif payload.platform.lower() == "flipkart":
        title += " | Stylish Home Furnishing"
    else:
        title += " for Reselling and Home Use"
    keywords = [
        payload.product_name,
        payload.color,
        payload.fabric,
        payload.size,
        payload.design,
        "home decor",
        "sofa",
        "premium quality",
    ]
    keywords = [item for item in dict.fromkeys([k.strip().lower() for k in keywords if k.strip()])]
    return {
        "seo_title": title[:150],
        "short_description": f"{payload.color} {payload.product_name} made with {payload.fabric}. Suitable for buyers looking for a neat, durable and attractive product.",
        "bullet_points": [
            f"Material: {payload.fabric or 'quality fabric'} with a comfortable finish.",
            f"Color and design: {payload.color or 'attractive color'} {payload.design or 'modern design'}.",
            f"Size: {payload.size or 'standard marketplace size'}; mention exact dimensions in images.",
            "Use clear photos and care instructions to reduce return and RTO risk.",
        ],
        "keywords": keywords,
        "platform_text": f"For {payload.platform}, keep the first image clean, mention size early, and include searchable words from title in bullets.",
    }

