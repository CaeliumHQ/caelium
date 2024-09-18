from django.contrib import admin

from .models import FCMToken, GoogleToken, User

admin.site.register(User)
admin.site.register(GoogleToken)
admin.site.register(FCMToken)
