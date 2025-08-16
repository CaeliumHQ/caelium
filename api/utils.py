from rest_framework_simplejwt.authentication import JWTAuthentication


def get_user_from_jwt(token):
    """
    Helper function to extract user information from JWT token.
    """
    jwt_auth = JWTAuthentication()
    validated_token = jwt_auth.get_validated_token(token)
    return jwt_auth.get_user(validated_token)
