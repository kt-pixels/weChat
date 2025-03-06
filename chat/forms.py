from django import forms
from .models import Post, Story, CustomUser

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["caption", "image", "video"]

class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ["image", "video"]
