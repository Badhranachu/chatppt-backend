from django.urls import path
from api.views import chat

urlpatterns = [
    path("chat/", chat, name="chatppt-chat"),
]
