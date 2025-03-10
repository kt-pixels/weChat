from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

# Create your models here.

# CUSTOM USER
class CustomUser(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_img = models.ImageField(upload_to='users/profile_pics/', default='users/default.jpg')
    cover_img = models.ImageField(upload_to='users/cover_pics/', blank=True, null=True)
    
    phone = models.CharField(max_length=10, unique=True, blank=True, null=True)
    bio = models.TextField(max_length=1200, blank=True)
    address = models.TextField(max_length=455, blank=True, null=True)
    
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    facebook_link = models.URLField(blank=True, null=True)
    instagram_link = models.URLField(blank=True, null=True)
    twitter_link = models.URLField(blank=True, null=True)
    linkedin_link = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

# 
class ChatRoom(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_user2')

    def __str__(self):
        return f"Chat between {self.user1.username} and {self.user2.username}"
    
class Message(models.Model):
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=1500)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False) 

    def __str__(self):
        return f"{self.id} : {self.sender.username} :- {self.text[:20]}"
    

# POST MODEL
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    caption = models.TextField(blank=True)
    image = models.ImageField(upload_to="posts/images/", blank=True, null=True)
    video = models.FileField(upload_to="posts/videos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Post By {self.user.username}"
    
# FOLLOW SYSTEM
class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
    
    def __str__(self):
        return f"{self.follower} follows {self.following}"
    

# Notification for follower page
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"

# STORY MODEL
class Story(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    image = models.ImageField(upload_to="stories/images/", blank=True, null=True)
    video = models.FileField(upload_to="stories/videos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    viewers = models.ManyToManyField(User, related_name='viewed_stories', blank=True)

    def __str__(self):
        return f"Story By {self.user.username}"
    
    def is_active(self):
        return (now() - self.created_at).total_seconds() < 86400 # 24 hours