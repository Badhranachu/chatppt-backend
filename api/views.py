import os
import requests
import time
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

OPENROUTER_API_KEY = settings.OPENROUTER_API_KEY
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# fallback model order
AI_MODELS = [
    "deepseek/deepseek-chat",
    "mistralai/mistral-7b-instruct",
    "google/gemini-pro-1.5",
    "qwen/qwen-2-7b-instruct",
]

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://chatppt-frontend.vercel.app",
    "X-Title": "ChatPPT",
}


@api_view(["POST"])
def chat(request):
    user_message = request.data.get("message", "")
    context = request.data.get("context", "")
    image_base64 = request.data.get("image_base64", None)

    # messages payload
    messages = [{"role": "system", "content": settings.CHATPPT_SYSTEM_PROMPT}]
    if context:
        messages.append({"role": "assistant", "content": context})

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

    start_time = time.time()  # ⏳ to prevent 502

    # model failover
    for model in AI_MODELS:
        payload = {"model": model, "messages": messages, "temperature": 0.8}

        for _ in range(2):  # two attempts per model
            try:
                r = requests.post(
                    OPENROUTER_URL,
                    headers=HEADERS,
                    json=payload,
                    timeout=15    # ⛑ response forced within 15s
                )
                if r.status_code == 200:
                    return Response({"answer": r.json()["choices"][0]["message"]["content"]})

                # if 429/503 → wait + retry
                if r.status_code in [429, 503]:
                    time.sleep(1.2)

            except Exception:
                time.sleep(1)

        # ⏱ kills if backend waits too long (prevents 502)
        if time.time() - start_time > 26:
            return Response({"answer": "😵 AI busy — try again in a moment"})

    return Response({"answer": "⚠ All AI models overloaded — try again soon 🙇"})


@api_view(["GET"])
def ping(request):
    return Response({"status": "alive"})
