from django.contrib import admin
from SAcore.models import *

# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'telephone','balance','Type')
    search_fields = ('username', 'email', 'telephone')
    list_filter = ('Type',)
    ordering = ['username']

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'instituition',
        'domain'
    )
    ordering=['name']

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'Type',
        'price'
    )
    ordering = ['title']

def make_approved(modeladmin, request, queryset):
    for a in queryset:
        a.approve()
make_approved.short_description = "approve"


@admin.register(U2E_apply)
class U2E_Admin(admin.ModelAdmin):
    list_display=(
        'user',
        'name',
        'created_time',
        'instituition',
        'domain',
    )
    actions = [make_approved]

@admin.register(publish_apply)
class publishAdmin(admin.ModelAdmin):
    list_display=(
        'title',
        'au',
        'Type',
        'created_time',
    )
    actions = [make_approved]

@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_play = (
        'start_au',
        'resource',
        'started_time',
        'period',
        'price',
        'candidate'
    )

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        'text',
        'created_time',
        'to_user'
    )

admin.site.register(UserToken)




