from django.urls import path
from api.views import chat

urlpatterns = [
    path("chat/", chat.as_view(), name="chatppt-chat"),
]
