import os
import time
from groq import Groq
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

client = Groq(api_key=settings.GROQ_API_KEY)

GROQ_MODELS = [
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b",
    "gemma2-9b-it",
    "gemma-7b-it",
    "llama3-groq-70b-tool-use",
]


@api_view(["POST"])
def chat(request):
    """
    Expected JSON from frontend:
    {
        "message": "hi",
        "theme": "annyan" or "ambi",
        "image_base64": null or "...",
        "history": [
            {"role": "user", "content": "hai", "theme": "annyan"},
            {"role": "assistant", "content": "heyy myree", "theme": "annyan"}
        ]
    }
    """

    user_message = request.data.get("message", "") or ""
    theme = request.data.get("theme", "annyan")
    image_base64 = request.data.get("image_base64", None)
    history = request.data.get("history", [])

    # Safety: ensure history is a list
    if not isinstance(history, list):
        history = []

    # SYSTEM PROMPT BASED ON PERSONALITY
    if theme == "ambi":
        system_prompt = settings.CHATPPT_AMBI_PROMPT
    else:
        theme = "annyan"
        system_prompt = settings.CHATPPT_ANNYAN_PROMPT

    messages = [{"role": "system", "content": system_prompt}]

    # Add ONLY previous messages from SAME theme
    for msg in history:
        try:
            if msg.get("theme") != theme:
                continue
            if msg.get("role") not in ("user", "assistant"):
                continue
            content = msg.get("content")
            if not isinstance(content, str) or not content.strip():
                continue

            messages.append({"role": msg.get("role"), "content": content})
        except:
            continue

    # Add NEW USER MESSAGE
    if image_base64:
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_message},
                {"type": "image_url", "image_url": f"data:image/png;base64,{image_base64}"}
            ]
        })
    else:
        messages.append({"role": "user", "content": user_message})

    # MULTI-MODEL FAILOVER
    start = time.time()
    for model in GROQ_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.8,
                timeout=18,
            )
            answer = response.choices[0].message.content

            # MUST include theme — React needs this so typing animation works
            return Response({
                "answer": answer,
                "theme": theme
            })

        except Exception:
            if time.time() - start > 25:
                break

    # FALLBACK
    return Response({
        "answer": "😵 All Groq models busy — try again shortly.",
        "theme": theme
    })
