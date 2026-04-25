import json


def extract_json_text(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            body = lines[1:-1]
            if body and body[0].strip().lower() == "json":
                body = body[1:]
            stripped = "\n".join(body).strip()

    if _is_complete_json(stripped):
        return stripped

    decoder = json.JSONDecoder()
    for index, char in enumerate(stripped):
        if char not in "[{":
            continue

        try:
            _, end_index = decoder.raw_decode(stripped[index:])
        except json.JSONDecodeError:
            continue

        return stripped[index : index + end_index]

    return stripped


def _is_complete_json(value: str) -> bool:
    if not value:
        return False

    try:
        json.loads(value)
    except json.JSONDecodeError:
        return False

    return True