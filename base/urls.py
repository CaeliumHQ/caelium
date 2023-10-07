from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('welcome/', views.welcome, name='welcome'),
    path('invite/',views.invite, name='invite'),
    path('invitation/<str:invite_code>/', views.invitation, name='invitation'),
    path('profile/', views.profile, name='profile'),

    path('manifest.json', views.ManifestView.as_view(), name='manifest'),
    path('service-worker.js', views.ServiceWorkerView.as_view(), name='service_worker'),
]
