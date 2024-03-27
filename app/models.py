from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.contrib.auth import get_user_model

class CustomUserManager(BaseUserManager):
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

class CustomUser(AbstractUser):
    nb_added_friends = models.IntegerField(default=0)
    objects = CustomUserManager()
    new_user = models.BooleanField(default=True)
    new_user_link_url = models.CharField(max_length=10, blank=True, null=True)
    new_user_link_date = models.DateTimeField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return self.username if self.username != "" else self.email if self.email != "" else "Utilisateur sans nom"

class Friendship(models.Model):
    class Status(models.TextChoices):
        PENDING = 'En attente'
        ACCEPTED = 'Accepté'
        INVITED = 'Invité'
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='friendships')
    friend = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='friendships_friend')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.friend.username} - {self.status}"

class UserBook(models.Model):
    class Status(models.TextChoices):
        TO_READ = 'A lire'
        READING = 'En cours'
        READ = 'Lu'
        ABANDONED = 'Abandonné'
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_books')
    book = models.ForeignKey('Book', on_delete=models.CASCADE, related_name='user_books')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.TO_READ)
    date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title} - {self.status}"

class Saga(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Book(models.Model):
    isbn = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    tome = models.IntegerField(blank=True, null=True)
    saga = models.ForeignKey(Saga, on_delete=models.CASCADE, related_name='books', blank=True, null=True)
    
    def __str__(self):
        if self.saga is None and self.title == "Pas de titre" and self.tome == -1:
            return f"{self.isbn} - Pas de titre - Pas de tome - Pas de saga"
        if self.saga is None:
            return f"{self.isbn} - {self.title} - tome {self.tome} - Pas de saga"
        return f"{self.isbn} - {self.title} - tome {self.tome} - {self.saga.name}"

class News(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, blank=True, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self) -> str:
        return f"{self.content}"