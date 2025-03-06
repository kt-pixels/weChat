from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import ChatRoom, Message, Follow, Post, Story, CustomUser
from django.http import JsonResponse
from .forms import PostForm, StoryForm
from datetime import timedelta
from django.utils.timezone import now
import random
import re

# Create your views here.
# SIGN UP VIEW
def signUp_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if len(username) < 8:
            return render(request, 'signup.html', {"error": "Username must be at least 8 characters long."})
        if "_" not in username:
            return render(request, 'signup.html', {"error": "Username must contain at least one underscore (_)."})
        
        # Automatically add '@' if not present at the start
        if not username.startswith("@"):
            username = "@" + username

         # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {"error": "Username is already taken"})
        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {"error": "This Email already exists"})
        
        # Check password match
        if password != confirm_password:
            return render(request, 'signup.html', {"error": "Passwords do not match"})

        
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        # CustomUser model me bhi ek entry create karein
        custom_user = CustomUser.objects.create(user=user)
        custom_user.save()

        return redirect('home_page')
    
    return render(request, 'signup.html')


# CHECK USERNAME IS AVAILABLE OR NOT
def check_username(request):
    username = request.GET.get('username', '').strip()

    if not username:  # Agar username empty hai toh error return karein
        return JsonResponse({'error': "Please enter a username."})

    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': "This username is not available..."})
    
    return JsonResponse({'success': "This username is available."})

# EMAIL EXIST
def check_email(request):
    email = request.GET.get('email', '').strip()

    if not email:  # Agar username empty hai toh error return karein
        return JsonResponse({'error': "Please enter a email."})

    if User.objects.filter(email=email).exists():
        return JsonResponse({'error': "This Email is already exist"})
    
    return JsonResponse({'success': "This emial is available."})
        

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
@login_required(login_url='login_view')
def home_page(request):
    if request.user.is_authenticated:
        users = User.objects.exclude(id=request.user.id).select_related('customuser')

        # Try to get CustomUser, agar nahi mile to None assign kar do
        try:
            user = CustomUser.objects.get(user=request.user)
        except CustomUser.DoesNotExist:
            user = None
    else:
        users = User.objects.all().select_related('customuser')
        user = None

     # Active stories (only stories which are not older than 24 hours)
    active_stories = Story.objects.filter(created_at__gte=now() - timedelta(hours=24))

    # User ne dekhi ya nahi dekhi, us basis par sort karein
    unseen_stories = []
    seen_stories = []

    # Grouping stories by user
    # user_stories = {}

    for story in active_stories:
        if request.user not in story.viewers.all():
            seen_stories.append(story)
        else:
            unseen_stories.append(story)

    # Unseen stories pehle aur seen stories baad me dikhayenge
    sorted_stories = unseen_stories + seen_stories

    # Stories ko group karna users ke basis par
    user_stories = {}
    for story in sorted_stories:
        if story.user not in user_stories:
            user_stories[story.user] = []
        user_stories[story.user].append(story)

    latest_post = Post.objects.order_by('-created_at')[:10]
    all_post = list(Post.objects.all())
    random.shuffle(all_post)
    random_post = all_post[:10]

    context = {
        'user_stories': user_stories,
        "users": users, 
        "custom_user": user,
        "latest_posts": latest_post,
        "random_post": random_post,
        "current_time": now(),
    }
    return render(request, 'base.html', context)

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
            return redirect('home_page')
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
            return redirect('home_page')
    else:
        form = StoryForm()
    
    return render(request, 'create_story.html', {"form": form}) 

def mark_story_viewed(request, story_id):
    if request.user.is_authenticated:
        story = Story.objects.get(id=story_id)
        story.viewers.add(request.user)
        return JsonResponse({"status": "viewed"})
    return JsonResponse({"error": "Unauthorized"}, status=403)

def user_stories_view(request, user_id):
    user_stories = Story.objects.filter(user_id=user_id).order_by('created_at')

    if not user_stories:
        return render(request, 'no_stories.html')  # Agar stories na ho toh ek simple message dikha do

    return render(request, 'stories_view.html', {'stories': user_stories})

def delete_old_stories():
    Story.objects.filter(created_at__lt=now()-timedelta(hours=24)).delete()


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
    custom_user, created = CustomUser.objects.get_or_create(user=request.user)

    if request.method == "POST":
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone_number')
        bio = request.POST.get('bio')
        gender = request.POST.get('gender')
        dob = request.POST.get('date_of_birth')
        address = request.POST.get('address')
        facebook_link = request.POST.get('facebook_link')
        instagram_link = request.POST.get('instagram_link')
        twitter_link = request.POST.get('twitter_link')
        linkedin_link = request.POST.get('linkedin_link')

        profile_img = request.FILES.get('profile_img')
        cover_img = request.FILES.get('cover_img')

        # USER MODEL
        user = request.user
        user.first_name = firstname
        user.last_name = lastname
        user.username = username
        user.email = email
        print(username)
        user.save()

        custom_user.phone = phone
        custom_user.bio = bio
        custom_user.gender = gender
        custom_user.date_of_birth = dob
        custom_user.address = address
        custom_user.facebook_link = facebook_link
        custom_user.instagram_link = instagram_link
        custom_user.twitter_link = twitter_link
        custom_user.linkedin_link = linkedin_link
        
        if profile_img:
            custom_user.profile_img = profile_img
        if cover_img:
            custom_user.cover_img = cover_img

        custom_user.save()

        return redirect('edit_user_profile')

    return render(request, 'edit_profile.html', {"custom_user": custom_user})

# USER_MEDIA AND PROFILE PAGE
def user_profile(request):
    media_type = request.GET.get('media', 'photo')

    if media_type == 'video':
        posts = Post.objects.filter(user=request.user, video__isnull=False).order_by('-created_at')
    else:
        posts = Post.objects.filter(user=request.user, image__isnull=False).order_by('-created_at')

    return render(request, 'user_profile.html', {"posts": posts, "media_type": media_type})
