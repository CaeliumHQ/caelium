from django.urls import path

from gallery import views

urlpatterns = [
    path("", views.get_images, name="get_photos"),
]
