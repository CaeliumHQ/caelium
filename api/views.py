from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken

from api.utils import get_user_from_jwt
from cloud.models import MediaFile


@api_view(["POST"])
@permission_classes([IsAdminUser])
def verify_jwt_user(request):
    """
    Accepts a JWT token in the Authorization header, verifies it, and checks if it is a real user.
    """
    token = request.data.get("accessToken")
    if not token:
        return Response({"detail": "accessToken not provided in POST data."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        UntypedToken(token)
        user = get_user_from_jwt(token)
        if user and user.is_active:
            return Response({"valid": True, "user_id": user.id, "username": user.username})
        else:
            return Response({"detail": "User not found or inactive."}, status=status.HTTP_404_NOT_FOUND)
    except (InvalidToken, TokenError) as e:
        return Response({"detail": "Invalid token.", "error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({"detail": "Error verifying token.", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def create_media(request):
    """
    Endpoint to upload media files. It verifies the JWT token and uploads files to storage.
    """
    token = request.data.get("accessToken")

    if not token:
        return Response({"error": "accessToken not provided"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        UntypedToken(token)
        user = get_user_from_jwt(token)
        if not user or not user.is_active:
            return Response({"error": "User is not valid or authentication failed"}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            MediaFile.objects.create(user=user, file=request.FILES["media"])
            return Response({"success": True, "message": "Media file uploaded successfully"}, status=status.HTTP_201_CREATED)
    except (InvalidToken, TokenError) as e:
        return Response({"error": "Invalid token", "details": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response(
            {"error": "An error occurred while uploading media", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
