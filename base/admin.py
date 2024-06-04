from django.contrib import admin

from base.models import Couple, Event, Family, Task, Work

# Register your models here.

admin.site.register(Couple)
admin.site.register(Family)
admin.site.register(Work)
admin.site.register(Task)
admin.site.register(Event)
