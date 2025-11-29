from groq import Groq
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

client = Groq(api_key=settings.GROQ_API_KEY)

@api_view(["POST"])
def chat(request):
    user_message = request.data.get("message", "")
    context = request.data.get("context", "")

    messages = [{"role": "system", "content": settings.CHATPPT_SYSTEM_PROMPT}]
    if context:
        messages.append({"role": "assistant", "content": context})
    messages.append({"role": "user", "content": user_message})

    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",  # FREE & fastest
            messages=messages,
            temperature=0.8,
        )
        reply = completion.choices[0].message.content
        return Response({"answer": reply})

    except Exception as e:
        return Response({"answer": "⚠ AI busy — try again in a momentjbj 🙇"})
