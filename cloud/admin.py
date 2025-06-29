from django.contrib import admin

from cloud.models import Directory, FileTag, SharedItem, Tag, CloudFile, MediaFile


@admin.register(Directory)
class DirectoryAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "get_path", "created_at", "modified_at")
    list_filter = ("owner", "created_at", "modified_at")
    search_fields = ("name", "owner__username")
    date_hierarchy = "created_at"

    def get_path(self, obj):
        return obj.path

    get_path.short_description = "Path"



@admin.register(SharedItem)
class SharedItemAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "get_shared_item", "permission", "created_at")
    list_filter = ("permission", "created_at", "user")
    search_fields = ("user__username", "content__name", "directory__name")
    date_hierarchy = "created_at"

    def get_shared_item(self, obj):
        if obj.content:
            return f"File: {obj.content.name}"
        return f"Directory: {obj.directory.name}"

    get_shared_item.short_description = "Shared Item"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "related_user", "created_at")
    list_filter = ("owner", "created_at")
    search_fields = ("name", "owner__username", "related_user__username")
    date_hierarchy = "created_at"


@admin.register(FileTag)
class FileTagAdmin(admin.ModelAdmin):
    list_display = ("file", "tag", "created_at")
    list_filter = ("tag", "created_at")
    search_fields = ("file__name", "tag__name")
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("file", "tag")


admin.site.register(CloudFile)
admin.site.register(MediaFile)
