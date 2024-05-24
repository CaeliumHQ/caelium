from django.contrib import admin

from gallery.models import Album, MediaFile

# Register your models here.
admin.site.register(MediaFile)
admin.site.register(Album)
