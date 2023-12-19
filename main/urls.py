from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('api/auth/', include('accounts.urls')),
    path('admin/', admin.site.urls),
]
