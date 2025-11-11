from django.contrib import admin

from .models import BaseUser


class UserAdmin(admin.ModelAdmin):
    pass


admin.site.register(BaseUser, UserAdmin)
