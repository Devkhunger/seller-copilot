import os

from app.services.analytics import calculate_sku_scores, dashboard_metrics, rto_risk_analysis
from app.services.recommender import generate_recommendations


def has_llm_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY"))


def generate_ai_summary(metrics: dict, sku_scores: list[dict], risk: dict) -> str:
    if has_llm_key():
        prompt = _seller_context_prompt(
            "Write a concise daily business summary for the seller. Keep it practical and avoid making up facts."
        )
        return _call_openai(prompt) or _fallback_summary(metrics, sku_scores, risk)
    return _fallback_summary(metrics, sku_scores, risk)


def answer_seller_question(question: str) -> dict:
    fallback_answer = _fallback_answer(question)
    if not has_llm_key():
        return {"answer": fallback_answer, "mode": "rule_based"}

    prompt = _seller_context_prompt(
        f"Seller question: {question}\n\nAnswer in plain language with 3-5 practical bullets. Use only the business data provided."
    )
    answer = _call_openai(prompt)
    return {"answer": answer or fallback_answer, "mode": "llm" if answer else "rule_based"}


def _call_openai(prompt: str) -> str | None:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY"))
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-5.2"),
            input=prompt,
        )
        return response.output_text.strip()
    except Exception:
        return None


def _seller_context_prompt(task: str) -> str:
    metrics = dashboard_metrics()
    sku_scores = calculate_sku_scores()
    risk = rto_risk_analysis()
    recs = generate_recommendations()
    return f"""
You are an AI Seller Copilot for a small ecommerce seller.
Answer only from the uploaded order data and the analysis below.
Do not invent platform fees, profit margins, or customer details.
If data is missing, say what is missing and give a cautious next step.

Dashboard metrics:
{metrics}

Top SKU scores:
{sku_scores[:10]}

RTO risk:
{risk}

Recommendations:
{recs}

Task:
{task}
""".strip()


def _fallback_answer(question: str) -> str:
    metrics = dashboard_metrics()
    sku_scores = calculate_sku_scores()
    risk = rto_risk_analysis()
    recs = generate_recommendations()
    lower = question.lower()

    if "promote" in lower or "push" in lower or "ad" in lower:
        if recs["promote_skus"]:
            sku = recs["promote_skus"][0]
            return f"Promote {sku['product_name']} first. It has score {sku['score']} and RTO {sku['rto_rate']}%, so it is safer for ad spend than weaker SKUs."
        return "I do not see a clearly safe SKU to promote yet. Upload more orders or improve delivery quality before increasing ad spend."

    if "pause" in lower or "stop" in lower or "loss" in lower:
        if recs["pause_skus"]:
            sku = recs["pause_skus"][0]
            return f"Pause or reduce spend on {sku['product_name']}. It has score {sku['score']} and RTO {sku['rto_rate']}%, which can hurt profitable orders."
        return "No SKU clearly needs pausing based on the current rules. Keep watching RTO and cancellation rates."

    if "rto" in lower or "return" in lower:
        combos = risk.get("high_risk_combos", [])
        if combos:
            combo = combos[0]
            return f"Highest RTO warning: {combo['customer_state']} with {combo['sku']} has {combo['rto_rate']}% RTO across {combo['orders']} orders. Avoid scaling paid ads for this combination."
        return f"Current RTO orders are {metrics['rto_orders']} out of {metrics['total_orders']} total quantity. No state crossed the high-risk threshold."

    best = sku_scores[0] if sku_scores else None
    worst = sku_scores[-1] if sku_scores else None
    if not best:
        return "Upload an order CSV first, then I can answer using SKU scores, RTO risk, and recommendations."
    return (
        f"Today, focus on {best['product_name']} because it has the strongest SKU score ({best['score']}). "
        f"Watch or improve {worst['product_name']} because it is the weakest SKU in the current data. "
        f"Total orders are {metrics['total_orders']}, delivered orders are {metrics['delivered_orders']}, and RTO orders are {metrics['rto_orders']}."
    )


def _fallback_summary(metrics: dict, sku_scores: list[dict], risk: dict) -> str:
    best = sku_scores[0]["product_name"] if sku_scores else "your best SKU"
    worst = metrics.get("worst_performing_sku") or "a weak SKU"
    risky_states = ", ".join(item["customer_state"] for item in risk.get("high_risk_states", [])[:2])
    source_note = (
        f"Ad orders were {metrics.get('ad_orders', 0)} and natural orders were {metrics.get('natural_orders', 0)}."
    )
    risk_sentence = (
        f"RTO risk is high in {risky_states}." if risky_states else "No state crossed the high-risk RTO threshold."
    )
    return (
        f"Today you have {metrics.get('total_orders', 0)} total orders in the uploaded report. "
        f"{best} performed best, while {worst} needs attention. "
        f"{risk_sentence} {source_note} "
        "Focus on pushing profitable SKUs, pausing risky combinations, and improving listings with weak natural demand."
    )
