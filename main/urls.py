from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('api/auth/', include('accounts.urls')),
    path('api/chats/', include('chats.urls')),
    path('api/crafts/', include('crafts.urls')),
    path('admin/', admin.site.urls),
    path('api/', include('base.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
