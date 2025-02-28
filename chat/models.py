from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

# Create your models here.
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
    
# STORY MODEL
class Story(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story')
    image = models.ImageField(upload_to="posts/images/", blank=True, null=True)
    video = models.FileField(upload_to="posts/videos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Story By {self.user.username}"
    
    def is_active(self):
        return (now() - self.created_at).total_seconds() < 86400 # 24 hours