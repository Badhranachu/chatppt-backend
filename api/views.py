import os
import requests
import time
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

OPENROUTER_API_KEY = settings.OPENROUTER_API_KEY
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Priority list — if first fails, next model is automatically used
AI_MODELS = [
    "deepseek/deepseek-chat",
    "mistralai/mistral-large",
    "qwen/qwen-2-7b-instruct",
    "google/gemini-pro-1.5",
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

    # Build messages payload
    system_prompt = settings.CHATPPT_SYSTEM_PROMPT
    messages = [{"role": "system", "content": system_prompt}]

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

    # Try models sequentially
    for model in AI_MODELS:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.8,
        }

        # Retry each model max 3 times
        for attempt in range(3):
            try:
                r = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload, timeout=30)
                if r.status_code == 200:
                    answer = r.json()["choices"][0]["message"]["content"]
                    return Response({"answer": answer})
                elif r.status_code in [429, 503]:
                    time.sleep(1.5)  # temporary overload sleep
                else:
                    break
            except Exception:
                time.sleep(1)

    # If everything failed
    return Response({
        "answer": "⚠ AI overloaded. Please try again in a moment 🙇"
    })


@api_view(["GET"])
def ping(request):
    return Response({"status": "alive"})
