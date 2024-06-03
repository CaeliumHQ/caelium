from django.contrib import admin

from .models import GoogleToken, User

admin.site.register(User)
admin.site.register(GoogleToken)
