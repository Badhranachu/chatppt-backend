import os
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from chatppt.settings import CHATPPT_SYSTEM_PROMPT


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class ChatPPTView(APIView):

    def call_model(self, api_key, messages, model):
        """Calls OpenRouter with protection"""
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
            return Response({"answer": "⚠ API key missing on backend"}, status=200)

        # system + context prompt
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

        # Primary model
        models = [
            "openai/gpt-4.1-mini",      # fast & smart
            "openai/gpt-3.5-turbo"      # fallback if first fails
        ]

        for model in models:
            try:
                data = self.call_model(api_key, messages, model)

                # real response
                if "choices" in data and data["choices"]:
                    reply = data["choices"][0]["message"]["content"]
                    if reply and reply.strip():
                        return Response({"answer": reply}, status=200)

            except Exception:
                pass  # continue to next model

        # Final fallback - never return empty
        return Response(
            {"answer": "Server overloaded. Try again in 5 seconds 😴"},
            status=200
        )
