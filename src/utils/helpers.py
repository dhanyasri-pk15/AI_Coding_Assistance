def extract_text(content) -> str:
    """
    Safely extract string text from model output content.
    Handles raw strings, LangChain message objects, or lists of content dicts (as returned by Gemini).
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                parts.append(part["text"])
            elif isinstance(part, str):
                parts.append(part)
            elif hasattr(part, "text"):
                parts.append(part.text)
            else:
                parts.append(str(part))
        return "".join(parts)
    if hasattr(content, "text"):
        return content.text
    return str(content)
