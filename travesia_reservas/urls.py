from django.conf import settings
from django.conf.urls.i18n import set_language
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/setlang/", set_language, name="set_language"),
    path("", include("core.urls")),
    path("", include("reservations.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/", include("users.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
