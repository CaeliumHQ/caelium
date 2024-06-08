from django.urls import path

from gallery import views

urlpatterns = [
    path("", views.get_images, name="get_photos"),
    path("update_token/", views.UpdateToken.as_view(), name="update_token"),
    path("get/<slug:image_id>/", views.detail_image, name="detailed_image"),
    path("albums/", views.get_albums, name="albums"),
]
