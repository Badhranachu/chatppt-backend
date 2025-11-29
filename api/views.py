from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from groq import Groq

client = Groq(api_key=settings.GROQ_API_KEY)

@api_view(["POST"])
def chat(request):
    try:
        user_message = request.data.get("message", "")
        context = request.data.get("context", "")

        messages = [
            {"role": "system", "content": settings.CHATPPT_SYSTEM_PROMPT}
        ]
        if context:
            messages.append({"role": "assistant", "content": context})
        messages.append({"role": "user", "content": user_message})

        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            temperature=0.7,
        )

        reply = completion.choices[0].message.content
        return Response({"answer": reply})

    except Exception as e:
        return Response({"answer": f"⚠ Error: {str(e)}"})


@api_view(["GET"])
def ping(request):
    return Response({"status": "alive"})
