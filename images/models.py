from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from uuid import uuid4
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Image(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="images_created",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(max_length=200, blank=True)
    image = models.ImageField(upload_to="images/%Y/%m/%d/")
    url = models.URLField(max_length=2000, blank=True)
    description = models.TextField(blank=True)
    created = models.DateField(auto_now_add=True)
    users_like = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="images_liked", blank=True
    )
    total_likes = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["-created"]),
            models.Index(fields=["-total_likes"]),
        ]
        ordering = ["-created"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            if self.title:
                self.slug = slugify(self.title)
            else:
                # Fallback to UUID slug if no title provided
                self.slug = str(uuid4())[:8]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("images:detail", args=[self.id, self.slug])


class Comment(models.Model):
    image = models.ForeignKey('Image', on_delete=models.CASCADE,
                              related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'Comment by {self.user} on {self.image}'


class Story(models.Model):
    user = models.ForeignKey(User, related_name='stories',
                             on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created + timedelta(hours=24)

    def viewers(self):
        return self.views.values_list('viewer', flat=True)

    def __str__(self):
        return f"{self.user.username} - {self.created}"


class StoryImage(models.Model):
    story = models.ForeignKey(Story, related_name='images',
                              on_delete=models.CASCADE)
    image = models.ImageField(upload_to='stories/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.story.user.username}'s story"


class StoryView(models.Model):
    story = models.ForeignKey(Story, related_name='views',
                              on_delete=models.CASCADE)
    viewer = models.ForeignKey(User, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('story', 'viewer')
