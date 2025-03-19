from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import ChatRoom, Message, Follow, Post, Story, CustomUser, Notification, StoryView
from django.http import JsonResponse
from .forms import PostForm, StoryForm
from datetime import timedelta
from django.utils.timezone import now, localtime
import random
from django.db.models import Max, Q
from django.contrib import messages
from django.utils.text import Truncator

# Create your views here.
# ++++++++++ REGISTRATION FUNCTIONALITY START HERE ++++++++++++++++++++++

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
        remember_me = request.POST.get('remember_me')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)

            # Agar 'Remember Me' unchecked hai, to session expiry ko kam kar dein
            if not remember_me:
                request.session.set_expiry(0)

            return redirect('home_page')
        
        return render(request, 'login.html', {"error": "Invalid Credentials"})
    return render(request, 'login.html')

# LOGOUT VIEW
def logout_view(request):
    logout(request)
    return redirect('login_view')

# ++++++++++++++ REGISTRATION FUNCTIONALITY FINISH HERE +++++++++++++++++

# HOME VIEW
@login_required(login_url='login_view')
def home_page(request):
    if request.user.is_authenticated:
        users = User.objects.exclude(id=request.user.id).select_related('customuser')

        try:
            user = CustomUser.objects.get(user=request.user)
        except CustomUser.DoesNotExist:
            user = None
    else:
        users = User.objects.all().select_related('customuser')
        user = None

    notification_unread = Notification.objects.filter(user=request.user, is_read=False).count()

    # Active stories filter karein (24 hours ke andar wali)
    followed_users = User.objects.filter(followers__follower=request.user)
    active_stories = Story.objects.filter(
        user__in=followed_users,
        created_at__gte=now() - timedelta(hours=24)
    )

    # Stories ko unseen aur seen ke basis pe alag karein
    unseen_stories = []
    seen_stories = []

    for story in active_stories:
        if request.user not in story.viewers.all():
            unseen_stories.append(story)  # Unseen pehle rakhein
        else:
            seen_stories.append(story)

    sorted_stories = unseen_stories + seen_stories

    # Sirf un users ko dikhayein jinke paas active stories hain
    user_stories = {}
    for story in sorted_stories:
        if story.user not in user_stories:
            user_stories[story.user] = []
        user_stories[story.user].append(story)

    # **Current user ki active stories bhi fetch karein**
    user_story = Story.objects.filter(user=request.user, created_at__gte=now() - timedelta(hours=24))

    latest_post = Post.objects.order_by('-created_at')[:10]
    all_post = list(Post.objects.all())
    random.shuffle(all_post)
    random_post = all_post[:10]

    context = {
        'user_story': user_story,  # Sirf active stories
        'user_stories': user_stories,  # Sirf unke jo stories upload kar chuke hain
        "users": users, 
        "custom_user": user,
        "latest_posts": latest_post,
        "random_post": random_post,
        "current_time": now(),
        "notification_unread": notification_unread,
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

    Message.objects.filter(
        chatroom=chatroom, 
        is_read=False
    ).exclude(sender=user1).update(is_read=True, seen_at=now())
    
    if request.method == "POST":
        message_text = request.POST.get("message")
        
        if message_text:
            Message.objects.create(
                chatroom=chatroom,
                sender=user1,
                text=message_text,
                is_read=False
            )
    
    messages = Message.objects.filter(chatroom=chatroom).order_by('timestamp')

    context = {
        "chatroom": chatroom,
        "messages": messages,
        "receiver": user2
    }

    return render(request, "chatRoom.html", context)

# Typing status
typing_status_data = {}

def typing_status(request):
    global typing_status_data

    from_user = request.GET.get('from')
    to_user = request.GET.get('to')
    status = request.GET.get('status')

    # Typing status update logic
    if status:
        if to_user not in typing_status_data:
            typing_status_data[to_user] = {}
        typing_status_data[to_user][from_user] = True if status == 'typing' else False
        return JsonResponse({"status": "success"})

     # Typing status fetch logic
    is_typing = any(typing_status_data.get(request.user.username, {}).values())
    return JsonResponse({'is_typing': is_typing})

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
    user_to_follow = get_object_or_404(User, username=username)

    if user_to_follow == request.user:
        messages.error(request, "You cannot follow yourself.")
        return redirect('user_profile', username=username)
    
    follow, created = Follow.objects.get_or_create(follower=request.user, following=user_to_follow)

    if not created:
        follow.delete()  # Unfollow
        messages.success(request, f"You have unfollowed {user_to_follow.username}")
    else:
        Notification.objects.create(
            user=user_to_follow,
            sender=request.user,
            message=f"{request.user.username} started following you.",
        )
        messages.success(request, f"You are now following {user_to_follow.username}")

    return redirect('user_profile', username=username)

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

@login_required
def story_view(request, user_id):
    twenty_four_hours_ago = now() - timedelta(hours=24)
    stories = Story.objects.filter(user_id=user_id, created_at__gte=twenty_four_hours_ago).order_by('created_at')
    
    if stories.exists():
        for story in stories:
            if story.user != request.user:  # Apni khud ki story dekhne par count na ho
                story_view, created = StoryView.objects.get_or_create(story=story, viewer=request.user)
                if created:  # Agar naya entry bani hai tabhi timestamp update karein
                    story_view.viewed_at = now()
                    story_view.save()

    return render(request, 'stories_view.html', {'stories': stories})

@login_required
def get_story_viewers(request, story_id):
    story = Story.objects.get(id=story_id)

    story_views = StoryView.objects.filter(story=story).exclude(viewer=story.user).select_related('viewer') #Owner ko exclude kr diya

    viewers_data = []
    current_time = now()

    for view in story_views:
        local_time = localtime(view.viewed_at)
        if local_time.date() == current_time.date():
            viewed_time = local_time.strftime("%I:%M %p")
        elif local_time.date() == (current_time.date() - timedelta(days=1)):
            viewed_time = f"Yesterday {local_time.strftime('%I:%M %p')}"
        else:
            viewed_time = local_time.strftime("%d %b %Y, %I:%M %p")

        viewers_data.append({
            "username": view.viewer.username,
            "profile_img": view.viewer.customuser.profile_img.url if view.viewer.customuser.profile_img else "/media/users/default.png",
            "viewed_at": viewed_time
        })
    
    return JsonResponse({'viewers': viewers_data, 'is_owner': request.user == story.user})

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
def user_profile(request, username):
    profile_user = get_object_or_404(CustomUser, user__username=username)
    media_type = request.GET.get('media', 'photo')

    if media_type == 'video':
        posts = Post.objects.filter(user=profile_user.user, video__isnull=False).order_by('-created_at')
    else:
        posts = Post.objects.filter(user=profile_user.user, image__isnull=False).order_by('-created_at')

    return render(request, 'user_profile.html', {"posts": posts, "profile_user": profile_user, "media_type": media_type})

def profile(request, username):
    profile_user = get_object_or_404(CustomUser, user__username=username)
    is_following = Follow.objects.filter(follower=request.user, following=profile_user.user).exists()
    media_type = request.GET.get('media', 'photo')

    if media_type == 'video':
        posts = Post.objects.filter(user=profile_user.user, video__isnull=False).order_by('-created_at')
    else:
        posts = Post.objects.filter(user=profile_user.user, image__isnull=False).order_by('-created_at')
    # return render(request, 'profile.html', {"profile_user" : profile_user, "is_following": is_following})
    return render(request, 'profile.html', {"posts": posts, "profile_user": profile_user, "media_type": media_type ,"is_following": is_following})

# GET NOTIFICATION
def get_notifications(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False)

    data = [
        {
            "message": notification.message,
            "created_at": notification.created_at.strftime("%d/%m/%Y, %H:%M:%S")
        }

        for notification in notifications
    ]
    return JsonResponse({'notifications': data})

# ✅ Mark Notifications as Read
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('all_notifications')

# notification page
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).select_related('sender__customuser').order_by('-created_at')
    return render(request, 'allNotifications.html', {"notifications": notifications})


# MESSAGE ROOM
def followers_message_room(request):
    chatrooms = ChatRoom.objects.filter(Q(user1=request.user) | Q(user2=request.user))

    # Latest messages ko fetch karein (User1 ya User2 ke hisaab se check karna hoga)
    latest_messages = (
        Message.objects.filter(chatroom__in=chatrooms)
        .values('chatroom__user1', 'chatroom__user2')
        .annotate(latest_time=Max('timestamp'))
        .order_by('-latest_time')
    )

    # Dictionary to store user details with their latest message
    user_message_data = []

    for msg in latest_messages:
        user_id = msg['chatroom__user1'] if msg['chatroom__user1'] != request.user.id else msg['chatroom__user2']

        # User ka detail fetch karen
        try:
            user = User.objects.get(id=user_id)
            latest_message = Message.objects.filter(
                Q(chatroom__user1=user, chatroom__user2=request.user) |
                Q(chatroom__user2=user, chatroom__user1=request.user)
            ).order_by('-timestamp').first()

            user_message_data.append({
                'username': user.username,
                'profile_img': user.customuser.profile_img.url  if hasattr(user, 'customuser') else '/media/users/default.png',
                'latest_message': Truncator(latest_message.text).chars(30) if latest_message else "No messages yet",
                'timestamp': latest_message.timestamp.strftime("%d/%m/%Y, %H:%M") if latest_message else None,
                'unread_count': Message.objects.filter(
                    Q(chatroom__user1=user, chatroom__user2=request.user, is_read=False) |
                    Q(chatroom__user2=user, chatroom__user1=request.user, is_read=False)
                ).exclude(sender=request.user).count()
            })
        except User.DoesNotExist:
            continue

    # 🔹 Latest message ke basis par sorting
    user_message_data.sort(key=lambda x: x['timestamp'], reverse=True)

    # 🔹 AJAX request ka JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'user_message_data': user_message_data})

    return render(request, 'messageTo.html', {"user_message_data": user_message_data})

def get_unread_messages(request):
    if request.user.is_authenticated:
        unread_messages = Message.objects.filter(
            ~Q(sender=request.user),  # Sirf doosre user ke messages ko count kare
            Q(chatroom__user1=request.user) | Q(chatroom__user2=request.user)
        ).filter(is_read=False).count()
        return JsonResponse({'unread_messages': unread_messages})
    return JsonResponse({'unread_messages': 0})

# FOLLOWERS
def followers_view(request):
    followed_users = Follow.objects.filter(follower=request.user).select_related('following')
    return render(request, 'followers.html', {'followed_users': followed_users})


# SEARCH
def search_users(request):
    query = request.GET.get("q", "")
    if query:
        users = (
            User.objects.filter(first_name__icontains=query) | 
            User.objects.filter(username__icontains=query)
        ).exclude(id=request.user.id)
        
        user_list = []
        for user in users:
            custom_user = CustomUser.objects.filter(user=user).first()
            profile_img_url = custom_user.profile_img.url

            user_list.append({
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username,
                'profile_img': profile_img_url
            })
    else:
        user_list = []

    return JsonResponse({'users': user_list})


# 
# @login_required
# def create_group(request):
#     if request.method == "POST":
#         name = request.POST.get("name")
#         image = request.FILES.get("image")
#         selected_users = request.POST.getlist("members")
        
#         if name:
#             group = Group.objects.create(name=name, image=image, admin=request.user)
#             GroupMembership.objects.create(user=request.user, group=group, role='admin')
#             for user_id in selected_users:
#                 user = User.objects.get(id=user_id)
#                 GroupMembership.objects.create(user=user, group=group, role='member')
#             return redirect("group_list")
    
#     users = User.objects.exclude(id=request.user.id)
#     return render(request, "groups/create_group.html", {"users": users})