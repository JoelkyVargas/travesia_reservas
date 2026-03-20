from django.urls import path
from .views import profile_redirect
urlpatterns = [path("perfil/", profile_redirect, name="profile_redirect")]
