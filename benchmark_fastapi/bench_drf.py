import time
import django
from django.conf import settings

settings.configure(
    DEBUG=False,
    SECRET_KEY="bench-only",
    ALLOWED_HOSTS=["*"],
    ROOT_URLCONF=__name__,
    INSTALLED_APPS=["rest_framework"],
    REST_FRAMEWORK={"UNAUTHENTICATED_USER": None},
)
django.setup()

from django.urls import path
from django.core.wsgi import get_wsgi_application
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response


class ItemSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1)
    price = serializers.FloatField(min_value=0.01)


class ItemView(APIView):                   # Bài A
    def post(self, request):
        s = ItemSerializer(data=request.data)
        s.is_valid(raise_exception=True)   # sai -> 400
        return Response(s.data, status=201)


class IoView(APIView):                     # Bài B
    def get(self, request):
        time.sleep(0.1)
        return Response({"ok": True})


urlpatterns = [path("items/", ItemView.as_view()), path("io/", IoView.as_view())]
application = get_wsgi_application()
