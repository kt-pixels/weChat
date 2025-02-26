from django.contrib import admin
from .models import ChatRoom, Message

# Register your models here.

class MessageInline(admin.TabularInline):
    model = Message
    readonly_fields = ('sender', 'text', 'timestamp')
    can_delete = False
    extra = 1

class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('user1', 'user2')
    inlines = [MessageInline]

admin.site.register(ChatRoom, ChatRoomAdmin)