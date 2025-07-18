from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

admin.site.site_header = "Caelium HQ"
admin.site.site_title = "Caelium HQ"
admin.site.index_title = "Caelium HQ"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("base.urls")),
    path("api/auth/", include("accounts.urls")),
    path("api/chats/", include("chats.urls")),
    path("api/cloud/", include("cloud.urls")),
    path('api/externals/', include('api.urls')),
    path("dash/", include("dash.urls")),
    path("", lambda request: redirect("admin/", permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
