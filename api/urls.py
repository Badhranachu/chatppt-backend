from django.urls import path
from api.views import ChatPPTView

urlpatterns = [
    path("chat/", ChatPPTView.as_view(), name="chatppt-chat"),
]
