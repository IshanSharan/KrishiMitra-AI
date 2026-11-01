"""Clarify a farmer's problem before generating a final advisory."""
import json
import re
from backend.llm import generate_response


def assess_question(problem, details, crop, location, language, history=""):
    """Return {status: ask|ready, question: ...} using Gemini.

    The assistant asks for only decision-relevant missing details. It does not
    provide a diagnosis or recommendation during this intake stage.
    """
    prompt = f"""
You are the intake assistant for KrishiMitra, an agricultural chatbot.
Your task is ONLY to decide whether there is enough information to give a safe,
useful answer to the farmer's latest problem. Do not answer the farming problem.

Farmer location: {location}
Crop: {crop}
Language: {language}
Farmer's original problem: {problem}
Farmer's additional details so far: {details or 'None'}
Earlier conversation context: {history or 'None'}

Rules:
- If a crucial detail is missing, ask concise targeted clarification question(s).
- For crop symptoms, useful details may include crop growth stage/age, which leaves/parts are affected,
  when it started, whether the whole field or patches are affected, recent rain/irrigation,
  and fertilizer/pesticide recently applied. Ask only what is relevant; do not ask all by default.
- For fertilizer questions, ask soil test values and crop stage if needed before suggesting nutrients.
- For irrigation questions, ask soil moisture/recent rain and crop stage if needed.
- For schedule requests, require sowing/transplanting date and variety/season when materially relevant.
- Do not ask for details already supplied.
- Ask no more than 2 or 3 short questions in one turn.
- If sufficient details are available, status is ready.
- Never ask for sensitive personal information.
- Output must be in {language}.

Return ONLY valid JSON, no markdown:
{{"status":"ask" or "ready", "question":"short clarification question(s), or empty when ready"}}
"""
    raw = (generate_response(prompt) or "").strip()
    # tolerate fenced JSON and surrounding text
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            status = str(data.get("status", "")).lower().strip()
            question = str(data.get("question", "")).strip()
            if status in {"ask", "ready"}:
                return {"status": status, "question": question}
        except (json.JSONDecodeError, TypeError):
            pass
    # Fail safely: request a little more context rather than guessing.
    fallback = (
        "कृपया फसल की अवस्था/उम्र और समस्या कब से है, यह बताइए।"
        if language.lower() == "hindi" else
        "Please share the crop growth stage/age and when the problem started."
    )
    return {"status": "ask", "question": fallback}
