from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home_page, name='home_page'),
    path('register/', views.signUp_view, name="signUp_view"),
    path('login/', views.login_view, name="login_view"),
    path('logout/', views.logout_view, name="logout_view"),

    # 
    path('edit-profile/', views.edit_user_profile, name='edit_user_profile'),

    # 
    path('chat/<str:username>/', views.chat_room, name='chat_room'),
    path('messages/<str:username>/', views.message_fetching_view, name='messages_fetching'),
    path("delete-message/<int:message_id>/", views.delete_message, name="delete-message"),
]