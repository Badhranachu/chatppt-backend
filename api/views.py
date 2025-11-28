import os
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from chatppt.settings import CHATPPT_SYSTEM_PROMPT
class ChatPPTView(APIView):
    def post(self, request):
        user_message = request.data.get("message", "").strip()
        context = request.data.get("context", "").strip()
        image_base64 = request.data.get("image_base64", None)

        api_key = getattr(settings, "OPENROUTER_API_KEY", None) or os.getenv("OPENROUTER_API_KEY")
        print(api_key,"HHHHHHHHHH")
        if not api_key:
            return Response({"error": "Missing OpenRouter key"}, status=500)

        # main system prompt
        system_prompt = settings.CHATPPT_SYSTEM_PROMPT

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # attach user prompt
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
            "model": "openai/gpt-4o",
            "messages": messages,
            "max_tokens": 300,
        }

        response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "X-Title": "ChatPPT"
                },
                json=payload,
                timeout=35  # avoid infinite loading
            )

        data = response.json()
        assistant_reply = data.get("choices", [{}])[0].get("message", {}).get("content", None)

        if not assistant_reply:
            return Response(
                {"answer": "chatppt crashed while trying to roast reality. Try again."},
                status=200
            )

        return Response({"answer": assistant_reply})