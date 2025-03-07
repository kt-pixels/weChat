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

    # 
    # path('user-profile/', views.user_profile, name='user_profile'),
    path('profile/<str:username>/', views.user_profile, name='user_profile'),

    # CReate post link
    path('create-post/', views.create_post, name='create_post'),
    path('create-story/', views.create_story, name='create_stroy'),

    # 
    path('stories/<int:user_id>/', views.user_stories_view, name='user_stories'),

]