import os
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from chatppt.settings import CHATPPT_SYSTEM_PROMPT

class ChatPPTView(APIView):
    def post(self, request):
        user_message = request.data.get("message", "").strip()
        context = request.data.get("context", "").strip()
        image_base64 = request.data.get("image_base64", None)

        api_key = getattr(settings, "OPENROUTER_API_KEY", None) or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return Response({"answer": "⚠ OPENROUTER_API_KEY missing on backend"}, status=200)

        # ---- System prompt ----
        messages = [{"role": "system", "content": CHATPPT_SYSTEM_PROMPT}]

        # ---- User message ----
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

        payload = {
            "model": "openai/gpt-4.1-mini",   # <<< correct model
            "messages": messages,
            "max_tokens": 350,
        }

        # ---- Call OpenRouter safely ----
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "X-Title": "ChatPPT"
                },
                json=payload,
                timeout=25
            )
            data = response.json()
        except Exception as e:  # timeout / network problem
            return Response({"answer": f"⚠ Server error: {str(e)}"}, status=200)

        # ---- OpenRouter returned an error ----
        if "error" in data:
            return Response({"answer": f"⚠ OpenRouter Error: {data['error']}"}, status=200)

        # ---- Extract final answer ----
        assistant_reply = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", None)
        )

        if not assistant_reply:
            return Response({"answer": "⚠ Empty response received. Try again."}, status=200)

        return Response({"answer": assistant_reply})
