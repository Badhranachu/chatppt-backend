from django.urls import path
from api.views import chat, ping

urlpatterns = [
    path("chat/", chat, name="chatppt-chat"),
    path("ping/", ping, name="chatppt-ping"),
]
