from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .models import ChatRoom, Message, Follow, Post, Story
from django.http import JsonResponse
from .forms import PostForm, StoryForm

# Create your views here.
# SIGN UP VIEW
def signUp_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            return render(request, 'signup.html', {"error": "Passwords do not match"})
        elif User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {"error": "Username is already taken"})
        elif User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {"error": "Email already exists"})
        
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        login(request, user)
        return redirect('home_page')
    
    return render(request, 'signup.html')

# LOGIN VIEW
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home_page')
        return render(request, 'login.html', {"error": "Invalid Credentials"})
    return render(request, 'login.html')

# LOGOUT VIEW
def logout_view(request):
    logout(request)
    return redirect('login_view')

# HOME VIEW
def home_page(request):
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'base.html', {"users": users})

# CHAT ROOM 
def chat_room(request, username):
    user1 = request.user
    user2 = get_object_or_404(User, username=username)

    if user1.id is None or user2.id is None:
        return render(request, 'error.html', {"error": "User Id is blank"})
    
    if user1.id < user2.id:
        chatroom , created = ChatRoom.objects.get_or_create(user1=user1, user2=user2)
    else:
        chatroom , created = ChatRoom.objects.get_or_create(user1=user2, user2=user1)
    
    if request.method == "POST":
        message_text = request.POST.get("message")
        
        if message_text:
            Message.objects.create(
                chatroom=chatroom,
                sender=user1,
                text=message_text,
            )
    
    messages = Message.objects.filter(chatroom=chatroom).order_by('timestamp')

    context = {
        "chatroom": chatroom,
        "messages": messages,
        "receiver": user2
    }

    return render(request, "chatRoom.html", context)


# MESSAGE FETCHING VIEW
def message_fetching_view(request, username):
    user1 = request.user
    user2 = get_object_or_404(User, username=username)

    if user1.id < user2.id:
        chatroom , created = ChatRoom.objects.get_or_create(user1=user1, user2=user2)
    else:
        chatroom , created = ChatRoom.objects.get_or_create(user1=user2, user2=user1)
    
    if not chatroom:
        return JsonResponse({'messages': []})
    
    messages = Message.objects.filter(chatroom=chatroom).order_by('timestamp')
    
    messages_data = [
        {
            "id": msg.id,
            "sender": msg.sender.username,
            "text": msg.text,
            "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M")
        }
        for msg in messages
    ]

    return JsonResponse({'messages': messages_data})


def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if message.sender == request.user:  # Sirf sender delete kar sakta hai
        message.delete()
        return redirect('chat_room', username=message.chatroom.user2.username)
    return redirect('chat_room', username=message.chatroom.user2.username)

# FOLLOWER
def follow_user(request, username):
    if request.method == 'POST':
        user_to_follow = get_object_or_404(User, username=username)
        follow, created = Follow.objects.get_or_create(follower=request.user, following=user_to_follow)

        if not created:
            follow.delete() # unfollow
            return JsonResponse({"message": "Unfollow Successfully"})
        return JsonResponse({"message": "Follow Success"})
    
    return JsonResponse({"error": "Invalid request"}, status=400)


# Post view
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('timelines')
    else:
        form = PostForm()
    
    return render(request, 'create_post.html', {"form": form}) 

# Story view
def create_story(request):
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES)
        if form.is_valid():
            story = form.save(commit=False)
            story.user = request.user
            story.save()
            return redirect('timelines')
    else:
        form = StoryForm()
    
    return render(request, 'create_story.html', {"form": form}) 

# FOLLOWING USERS POST AND STORIES
def timeline(request):
    # Get list of users the current user is following
    following_users = Follow.objects.filter(follower=request.user).values_list("following", flat=True)

    # Get posts & stories only from followed users
    posts = Post.objects.filter(user__id__in=following_users).order_by("-created_at")
    stories = Story.objects.filter(user__id__in=following_users).order_by("-created_at")

    return render(request, "timeline.html", {"posts": posts, "stories": stories})


# EDIT PROFILE
def edit_user_profile(request):
    return render(request, 'edit_profile.html')