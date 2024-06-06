import json
import os

import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response

from accounts.models import GoogleToken, User


def update_token(code):
    response = requests.get(
        url="https://oauth2.googleapis.com/token", data={"code": code}, timeout=10
    )


@api_view(["GET"])
def get_images(request):
    user = User.objects.get(email=request.user.email)
    token = GoogleToken.objects.get(user=user).access_token

    response = requests.get(
        url="https://photoslibrary.googleapis.com/v1/mediaItems/media-item-id",
        timeout=10,
        headers={
            "Content-type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )
    if response.status_code != 200:
        print(response.content)
        error = json.loads(response.content)["error"]["details"][0]["reason"]
        if error == "ACCESS_TOKEN_SCOPE_INSUFFICIENT":
            url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={os.environ['GOOGLE_CLIENT_ID']}&response_type=code&state=state_parameter_passthrough_value&scope=https://www.googleapis.com/auth/photoslibrary.readonly&redirect_uri=http://127.0.0.1:8000/api/auth/google/add_scope/&prompt=consent"
            return Response({"type": "error", "url": url}, status=203)
    else:
        return Response(json.loads(response.content))
    return Response(({"name": user.name, "data": json.loads(response.content)}))


o = "4/0AdLIrYck08wPkimpJ_j_dBrFp6RHyGQMF_As64JuWwzSFOByMLsvuhZ_z6jnbTH2EEM2Kg"
