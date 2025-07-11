from datetime import datetime
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from mongoengine import Document, StringField, FloatField, DateTimeField, BooleanField, EmailField, IntField

class BrowsingLog(Document):
    parent_email = EmailField(max_length=254)
    child_email = EmailField(max_length=254)
    title = StringField(max_length=300)
    url = StringField()
    query = StringField(max_length=300, required=False)
    duration_sec = IntField()
    is_night_time = BooleanField()
    label = StringField(max_length=20)
    timestamp = DateTimeField(default=datetime.utcnow)
    email_sent = BooleanField(default=False)
    reason = StringField(max_length=100, default="")
    summary = StringField(default="")

    meta = {
        'collection': 'browsing_logs'
    }

class ParentUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class ParentUser(AbstractBaseUser):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    children = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    objects = ParentUserManager()

    def __str__(self):
        return self.email

class RiskAlert(models.Model):
    child_email = models.EmailField()
    reason = models.CharField(max_length=300)
    page_url = models.URLField()
    triggered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert for {self.child_email} - {self.reason}"
