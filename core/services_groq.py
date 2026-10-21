"""
core/services_groq.py

Groq AI integration for generating planner insights.
Uses llama-3.1-8b-instant (fast, free tier).
Requires GROQ_API_KEY in settings / environment.
"""
import json
import urllib.request
import urllib.error
from django.conf import settings
from django.core.cache import cache


_GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
_MODEL = "qwen/qwen3.8-27b"
_CACHE_TTL = 3600  # 1 jam per plan


def _build_prompt(plan) -> str:
    """Build a concise Indonesian-language prompt for the given EventPlan."""
    kategori = plan.event_category.name if plan.event_category else "Event Umum"
    kota = plan.city or "Indonesia"
    pax = plan.estimated_pax or 0
    budget_min = int(plan.budget_min or 0)
    budget_max = int(plan.budget_max or 0)
    event_date = plan.event_date.strftime("%d %B %Y") if plan.event_date else "belum ditentukan"

    import datetime
    days_left = max((plan.event_date - datetime.date.today()).days, 0) if plan.event_date else 0

    services_raw = plan.selected_services or []
    services_str = ", ".join(services_raw) if services_raw else "tidak disebutkan"

    cost_per_pax = round(budget_max / pax) if pax else 0
    cost_per_pax_fmt = f"Rp {cost_per_pax:,}".replace(",", ".")

    if plan.event_date:
        time_desc = f"{days_left} hari lagi" if days_left > 0 else "Hari-H sudah dekat / terlewat"
    else:
        time_desc = "tanggal belum ditentukan"

    return (
        "Kamu adalah Lead Event Director & Wedding Consultant senior di Indonesia yang sangat paham standar harga pasar nyata dan dinamika vendor lapangan.\n\n"
        "Berikan analisis profesional dan 'reality check' yang tajam namun solutif untuk rencana acara berikut:\n\n"
        f"- Jenis Acara: {kategori}\n"
        f"- Kota: {kota}\n"
        f"- Estimasi Tamu: {pax:,} orang\n"
        f"- Pagu Budget: Rp {budget_min:,} - Rp {budget_max:,}\n"
        f"- Estimasi Biaya/Tamu: {cost_per_pax_fmt}\n"
        f"- Tanggal Acara: {event_date} ({time_desc})\n"
        f"- Kebutuhan Layanan: {services_str}\n\n"
        "Analisis dari sudut pandang industri nyata dalam 3 poin esensial (gunakan bullet point '- '):\n"
        f"1. Reality Check Anggaran: Tinjau secara jujur apakah {cost_per_pax_fmt}/tamu realistis untuk {kategori} di {kota}. Jika ketat, sebutkan penyesuaian katering/venue yang paling masuk akal.\n"
        "2. Strategi Kunci Vendor: Vendor mana yang wajib di-booking/DP pertama kali untuk mengamankan tanggal & harga sebelum sold out?\n"
        f"3. Langkah Taktis ({time_desc}): Aksi paling mendesak dalam 1-2 minggu ke depan untuk menghindari risiko pembengkakan biaya atau vendor bentrok.\n\n"
        "Gaya bahasa: Praktis, lugas, berwibawa, dan sangat solutif. Maksimal 140 kata."
    )


def get_ai_planner_insight(plan) -> dict:
    """
    Returns {'insight': str, 'cached': bool, 'error': str|None}.
    If GROQ_API_KEY is not configured, returns a graceful fallback.
    """
    cache_key = f"groq_insight_plan_{plan.id}"
    cached = cache.get(cache_key)
    if cached:
        return {'insight': cached, 'cached': True, 'error': None}

    api_key = getattr(settings, 'GROQ_API_KEY', '')
    if not api_key:
        return {'insight': None, 'cached': False, 'error': 'GROQ_API_KEY not configured'}

    prompt = _build_prompt(plan)
    payload = json.dumps({
        "model": _MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 450,
        "temperature": 0.7,
    }).encode("utf-8")

    req = urllib.request.Request(
        _GROQ_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Vendoraman-App/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            insight = body["choices"][0]["message"]["content"].strip()
            cache.set(cache_key, insight, _CACHE_TTL)
            return {'insight': insight, 'cached': False, 'error': None}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return {'insight': None, 'cached': False, 'error': f"HTTP {e.code}: {err_body[:200]}"}
    except Exception as e:
        return {'insight': None, 'cached': False, 'error': str(e)}
