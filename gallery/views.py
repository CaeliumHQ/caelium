import json
import os

import requests
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import GoogleToken, User
from accounts.views import get_auth_tokens, refresh_access


class UpdateToken(APIView):
    def post(self, request):
        user = User.objects.get(email=request.user.email)
        print(request.data)
        tokens = get_auth_tokens(
            request.data["code"], f"{os.environ['CLIENT_HOST']}/api/gallery/callback"
        )
        print(tokens)
        google_access_token = tokens["access_token"]
        google_refresh_token = tokens["refresh_token"]
        google_token = GoogleToken.objects.get(user=user)
        google_token.access_token = google_access_token
        google_token.refresh_token = google_refresh_token
        google_token.save()
        return Response({"data": "success"}, status=200)


@api_view(["GET"])
def get_images(request):
    user = User.objects.get(email=request.user.email)
    token = GoogleToken.objects.get(user=user)

    def fetch_images(access_token):
        response = requests.get(
            url="https://photoslibrary.googleapis.com/v1/mediaItems",
            timeout=10,
            headers={
                "Content-type": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
            # params={
            #     "pageSize": "20",
            # },
        )
        return response

    response = fetch_images(token.access_token)

    if response.status_code != 200:
        try:
            error = json.loads(response.content)["error"]["details"][0]["reason"]
            if error == "ACCESS_TOKEN_SCOPE_INSUFFICIENT":
                request_url = requests.Request(
                    "GET",
                    "https://accounts.google.com/o/oauth2/v2/auth",
                    params={
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "redirect_uri": f"{os.environ['CLIENT_HOST']}/api/gallery/callback",
                        "response_type": "code",
                        "scope": "https://www.googleapis.com/auth/photoslibrary.readonly",
                        "access_type": "offline",
                        "prompt": "consent",
                        "include_granted_scopes": "true",
                        "login_hint": request.user.email,
                    },
                )
                url = request_url.prepare().url
                return Response({"type": "error", "url": url}, status=203)
        except (KeyError, IndexError):
            refreshed_tokens = refresh_access(token.refresh_token)
            token.access_token = refreshed_tokens["access_token"]
            token.save()
            response = fetch_images(token.access_token)

    if response.status_code != 200:
        return Response(
            {"error": "Failed to fetch images"}, status=response.status_code
        )

    return Response(
        [
            {
                "id": item["id"],
                "url": item["baseUrl"],
                "filename": item["filename"],
                "timestamp": item["mediaMetadata"]["creationTime"],
            }
            for item in json.loads(response.content)["mediaItems"]
        ]
    )


@api_view(["GET"])
def detail_image(request, image_id):
    user = User.objects.get(email=request.user.email)
    tokens = GoogleToken.objects.get(user=user)

    def fetch_image(access_token):
        response = requests.get(
            url=f"https://photoslibrary.googleapis.com/v1/mediaItems/{image_id}",
            timeout=10,
            headers={
                "Content-type": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        return response

    response = fetch_image(tokens.access_token)
    if response.status_code == 401:
        refreshed_tokens = refresh_access(tokens.refresh_token)
        tokens.access_token = refreshed_tokens["access_token"]
        tokens.save()
        response = fetch_image(tokens.access_token)
    data = response.json()
    return Response(
        {
            "id": data["id"],
            "url": data["baseUrl"],
            "filename": data["filename"],
            "timestamp": data["mediaMetadata"]["creationTime"],
        }
    )


@api_view(["GET"])
def get_albums(request):
    user = User.objects.get(email=request.user.email)
    tokens = GoogleToken.objects.get(user=user)

    def get_album_data(album_id):
        response = requests.post(
            url="https://photoslibrary.googleapis.com/v1/mediaItems:search",
            headers={
                "Content-type": "application/json",
                "Authorization": f"Bearer {tokens.access_token}",
            },
            timeout=10,
            params={"albumId": album_id},
        )
        data = [
            {
                "id": item["id"],
                "url": item["baseUrl"],
                "filename": item["filename"],
                "timestamp": item["mediaMetadata"]["creationTime"],
            }
            for item in json.loads(response.content)["mediaItems"]
        ]
        return data

    def album_list():
        return requests.get(
            url="https://photoslibrary.googleapis.com/v1/albums",
            headers={
                "Content-type": "application/json",
                "Authorization": f"Bearer {tokens.access_token}",
            },
            timeout=10,
        )

    response = album_list()
    if response.status_code == 401:
        refreshed_tokens = refresh_access(tokens.refresh_token)
        tokens.access_token = refreshed_tokens["access_token"]
        tokens.save()
        response = album_list()

    data = [
        {
            "id": items["id"],
            "title": items["title"],
            "images": get_album_data(items["id"]),
        }
        for items in response.json()["albums"]
    ]
    return Response(data)
