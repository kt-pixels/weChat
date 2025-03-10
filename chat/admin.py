from django.contrib import admin
from .models import ChatRoom, Message, CustomUser, Post, Story, Follow, Notification
from django.contrib.auth.models import User

# Register your models here.

# CUSTOME USER INCLUDE START
class CustomUserInline(admin.StackedInline):
    model = CustomUser
    can_delete = False

class CustomUserAdmin(admin.ModelAdmin):
    inlines = [CustomUserInline]

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
# CUSTOME USER INCLUDE END


# MESSAGE MODEL ADD WITH CHATROOM START
class MessageInline(admin.TabularInline):
    model = Message
    readonly_fields = ('sender', 'text', 'timestamp')
    can_delete = False
    extra = 1

class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('user1', 'user2')
    inlines = [MessageInline]

admin.site.register(ChatRoom, ChatRoomAdmin)
# MESSAGE MODEL ADD WITH CHATROOM END

admin.site.register(Post)
admin.site.register(Story)
admin.site.register(Follow)
admin.site.register(Notification)


# registering follow model inside to user model

