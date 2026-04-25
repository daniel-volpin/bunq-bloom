import json


def build_verification_prompt(gig: dict) -> str:
    title = str(gig.get("title") or "").strip()
    description = str(gig.get("description") or "").strip()
    checklist = gig.get("verification_checklist") or []
    checklist_items = [str(item).strip() for item in checklist if str(item).strip()]
    checklist_text = "\n".join(f"- {item}" for item in checklist_items) or "- task improved"

    return (
        "You are verifying a kid's completed gig using BEFORE and AFTER photos.\n"
        "Compare both photos against the gig details and checklist.\n"
        "Be strict, fair, and concise.\n\n"
        "Return JSON only with this exact schema:\n"
        "{\n"
        '  "approved": boolean,\n'
        '  "confidence": number between 0 and 1,\n'
        '  "tags": ["short tag"],\n'
        '  "message_for_kid": "short encouraging sentence",\n'
        '  "reasoning_summary": "short reason for parent/backend"\n'
        "}\n\n"
        "Rules:\n"
        "- If required evidence is missing, set approved to false.\n"
        "- Keep tags short and relevant to checklist evidence.\n"
        "- Do not include markdown, prose, or extra keys.\n\n"
        f"Gig title: {title}\n"
        f"Gig description: {description}\n"
        f"Checklist:\n{checklist_text}\n"
    )


def build_snap_and_learn_prompt() -> str:
    return (
        "You are analyzing a product photo for a kid-friendly savings app.\n"
        "Identify the item and estimate a plausible EUR price.\n"
        "Return JSON only with this exact schema:\n"
        "{\n"
        '  "item_name": "short product name",\n'
        '  "estimated_price": "12.99",\n'
        '  "currency": "EUR",\n'
        '  "confidence": number between 0 and 1,\n'
        '  "reasoning_summary": "short explanation"\n'
        "}\n"
        "Rules:\n"
        "- Keep item_name short and specific.\n"
        "- estimated_price must be a string decimal in EUR.\n"
        "- Do not add markdown or extra keys.\n"
    )


def build_weekly_report_prompt(report_context: dict) -> str:
    return (
        "You are writing a short, kid-friendly weekly family money recap.\n"
        "Use only the provided structured stats.\n"
        "Return JSON only with this exact schema:\n"
        "{\n"
        '  "highlights": [{"title": "short title", "detail": "short detail"}],\n'
        '  "savings_insight": "one short sentence",\n'
        '  "conversation_starter": "one short question"\n'
        "}\n"
        "Rules:\n"
        "- Keep highlights short and specific.\n"
        "- Do not invent facts beyond the provided report context.\n"
        "- Do not add markdown or extra keys.\n\n"
        f"Report context: {json.dumps(report_context)}"
    )
