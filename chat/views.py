from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .models import ChatRoom, Message
from django.http import JsonResponse

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
            Message.objects.create(chatroom=chatroom, sender=user1, text=message_text) 
    
    messages = Message.objects.filter(chatroom=chatroom).order_by('timestamp')

    context = {
        "chatroom": chatroom,
        "messages": messages,
        "receiver": user2
    }

    return render(request, "chatRoom.html", context)


# CHAT ROOM
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
            "sender": msg.sender.username,
            "text": msg.text,
            "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M")
        }
        for msg in messages
    ]

    return JsonResponse({'messages': messages_data})
