import os
import requests
import threading
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from chatppt.settings import CHATPPT_SYSTEM_PROMPT

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def keep_alive():
    """Prevents Render backend from sleeping"""
    while True:
        try:
            requests.get("https://chatppt-backend.onrender.com/api/chat/")
        except:
            pass
        import time
        time.sleep(600)  # 10 minutes


threading.Thread(target=keep_alive, daemon=True).start()


class ChatPPTView(APIView):

    def call_model(self, api_key, messages, model):
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 450
        }

        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://chatppt-frontend.vercel.app",
                "X-Title": "ChatPPT"
            },
            json=payload,
            timeout=45,
        )
        return response.json()

    def post(self, request):
        user_message = request.data.get("message", "").strip()
        context = request.data.get("context", "").strip()
        image_base64 = request.data.get("image_base64", None)

        api_key = getattr(settings, "OPENROUTER_API_KEY", None) or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return Response({"answer": "⚠ API key missing"}, status=200)

        messages = [{"role": "system", "content": CHATPPT_SYSTEM_PROMPT}]
        if image_base64:
            messages.append({
                "role": "user",
                "content": [
                  {"type": "text", "text": user_message},
                  {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_base64}"}
                ]
            })
        else:
            combined = f"{context}\n\nUser: {user_message}" if context else user_message
            messages.append({"role": "user", "content": combined})

        models = [
            "openai/gpt-4.1-mini",
            "openai/gpt-3.5-turbo"
        ]

        for model in models:
            try:
                data = self.call_model(api_key, messages, model)
                if "choices" in data and data["choices"]:
                    reply = data["choices"][0]["message"]["content"]
                    if reply:
                        return Response({"answer": reply}, status=200)
            except Exception:
                continue

        return Response({"answer": "Server overloaded. Try again in 5 seconds 😴"}, status=200)
