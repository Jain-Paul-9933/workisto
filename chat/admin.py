from django.contrib import admin

from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "booking", "sender", "created_at")
    search_fields = ("booking__id", "sender__email", "body")
    readonly_fields = ("created_at",)
