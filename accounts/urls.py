from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from . import views

urlpatterns = [
    path('token/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('accounts/', views.UserViewSet.as_view({'get': 'list'}), name='all_users'),
    path('accounts/<int:pk>/', views.UserDetailsView.as_view(), name='user-details'),
    path('update/<int:pk>/', views.UserUpdateView.as_view(), name='user-update'),
]
