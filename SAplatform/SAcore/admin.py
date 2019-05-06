from django.contrib import admin
from SAcore.models import *

# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'telephone','balance','Type')
    search_fields = ('username', 'email', 'telephone')
    list_filter = ('Type',)
    ordering = ['username']

admin.site.register(Author)
admin.site.register(Resource)

@admin.register(U2E_apply)
class U2E_Admin(admin.ModelAdmin):
    list_display=(
        'user',
        'name',
        'created_time',
        'instituition',
        'domain',
    )



