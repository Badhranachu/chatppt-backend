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
    "llama3-groq-70b-tool-use"
]

@api_view(["POST"])
def chat(request):
    user_message = request.data.get("message", "")
    context = request.data.get("context", "")
    theme = request.data.get("theme", "annyan")  # default
    image_base64 = request.data.get("image_base64", None)

    # Select correct system prompt
    system_prompt = (
        settings.CHATPPT_AMBI_PROMPT
        if theme == "ambi"
        else settings.CHATPPT_ANNYAN_PROMPT
    )

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

    start_time = time.time()

    for model in GROQ_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.8,
                timeout=18
            )
            return Response({"answer": response.choices[0].message.content})
        except Exception:
            if time.time() - start_time > 25:
                break

    return Response({"answer": "😵 All Groq models busy — try again shortly."})
