from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home_page, name='home_page'),
    path('register/', views.signUp_view, name="signUp_view"),
    path('login/', views.login_view, name="login_view"),
    path('logout/', views.logout_view, name="logout_view"),

    # Availibility
    path('check-username/', views.check_username, name='check_username'),
    path('check-email/', views.check_email, name='check_email'),

    # 
    path('edit-profile/', views.edit_user_profile, name='edit_user_profile'),

    # 
    path('chat/<str:username>/', views.chat_room, name='chat_room'),
    path('messages/<str:username>/', views.message_fetching_view, name='messages_fetching'),
    path("delete-message/<int:message_id>/", views.delete_message, name="delete-message"),
    path('typing-status/', views.typing_status, name='typing_status'),

    # 
    # path('user-profile/', views.user_profile, name='user_profile'),
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('user-profile/<str:username>/', views.profile, name='main_user_profile'),

    # CReate post link
    path('create-post/', views.create_post, name='create_post'),
    path('create-story/', views.create_story, name='create_stroy'),

    # 
    # path('stories/<int:user_id>/', views.user_stories_view, name='user_stories'),
    path('follow/<str:username>/', views.follow_user, name='follow_user'),

    # NOTIFICATION
    path('get-notifications/', views.get_notifications, name='get_notifications'),
    path('mark-notifications-read/<int:notification_id>', views.mark_notification_as_read, name='mark_notifications_as_read'),
    path('notifications/', views.notifications_view, name='all_notifications'),

    # Message room
    path('message-to/', views.followers_message_room, name="message_room"),
    path('followers/', views.followers_view, name="followed_users"),
    path('get-unread-messages/', views.get_unread_messages, name='get_unread_messages'),

]