from django.urls import path

from gallery import views

urlpatterns = [
    path("", views.get_images, name="get_photos"),
    path('update_token/', views.UpdateToken.as_view(), name='update_token')
]
