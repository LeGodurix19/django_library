import logging
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.views import View
from urllib.parse import unquote
from datetime import datetime, timedelta
from .models import CustomUser, Book, Saga, UserBook, Friendship, News
from .forms import *
from .utils import send_email, random_string, get_books

@method_decorator(login_required, name='dispatch')
class params_view(View):
    def get(self, request):
        form__update_user__password = Update_CustomUser__PasswordForm(instance=request.user)
        form__update_user__avatar = Update_CustomUser__AvatarForm(instance=request.user)
        form__update_user__username = Update_CustomUser__UsernameForm(instance=request.user)
        form__update_user__email = Update_CustomUser__EmailForm(instance=request.user)
        form__add_user = Add__CustomUserForm()
        all_invitations = Friendship.objects.filter(friend=request.user, status=Friendship.Status.PENDING)
        all_waiting = Friendship.objects.filter(user=request.user, status=Friendship.Status.PENDING)
        all_friends = Friendship.objects.filter(user=request.user, status=Friendship.Status.ACCEPTED)
        all_invited = Friendship.objects.filter(user=request.user, status=Friendship.Status.INVITED)
        friends = {}
        if all_friends:
            friends['Amis'] = all_friends
        if all_waiting:
            friends['En attente'] = all_waiting
        if all_invited:
            friends['Amis invites'] = all_invited
        return render(request, 'params_user.html', context={
            'user': request.user, 
            'form__update_user__password': form__update_user__password,
            'form__update_user__avatar': form__update_user__avatar,
            'form__update_user__username': form__update_user__username,
            'form__update_user__email': form__update_user__email,
            'from__add_user': form__add_user,
            'all_invitations': all_invitations,
            'friends': friends,
        })

class login_view(View): 
    def get(self, request):
        return render(request, 'login.html')
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        if username and password:
            user_tmp = authenticate(username=username, password=password)
            if user_tmp:
                login(request, user_tmp)
                return redirect('index')
        return render(request, 'login.html', context={'error': 'Mauvais identifiants'})

class login_new_user_view(View):
    def get(self, request, id_new_user):
        if CustomUser.objects.filter(new_user_link_url=id_new_user).exists():
            user = CustomUser.objects.get(new_user_link_url=id_new_user)
            limit_date = user.new_user_link_date + timedelta(days=1)
            limit_date = limit_date.replace(tzinfo=None)
            if user.new_user and datetime.now(tz=None) < limit_date:
                form = CustomUserForm(instance=user)
                return render(request, 'login_new_user.html', context={'form': form, 'id_new_user': id_new_user})
        return redirect('login')
    
    def post(self, request, id_new_user):
        if not CustomUser.objects.filter(new_user_link_url=id_new_user).exists() and not CustomUser.objects.get(new_user_link_url=id_new_user).new_user and not CustomUser.objects.get(new_user_link_url=id_new_user).new_user_link_date + timedelta(days=1) < datetime.now(tz=None):
            return redirect('login')
        user = CustomUser.objects.get(new_user_link_url=id_new_user)
        form = CustomUserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = CustomUser.objects.get(new_user_link_url=id_new_user)
            user.username = form.cleaned_data['username']
            user.email = form.cleaned_data['email']
            user.set_password(form.cleaned_data['password'])
            user.avatar = form.cleaned_data['avatar']
            user.new_user = False
            user.save()
            login(request, user)
            return redirect('index')
        return render(request, 'login_new_user.html', context={'form': form, 'id_new_user': id_new_user})

@method_decorator(login_required, name='dispatch')
class logout_view(View):
    def get(self, request):
        logout(request)
        return redirect('login')

@method_decorator(login_required, name='dispatch')
class general_view(View):
    def get(self, request):
        user = request.user
        books = get_books(user)
        logging.warning(books)
        return render(request, 'index.html', context={'books': books, "user": user})
          
@method_decorator(login_required, name='dispatch')
class details_view(View):
    def get(self, request, bc):
        bc = unquote(bc)
        try:
            book = Book.objects.get(title=bc)
            book = UserBook.objects.get(user=request.user, book=book)
            return render(request, 'details.html', context={'book': book})     
        except:
            saga = Saga.objects.get(name=bc)
            userBook = UserBook.objects.filter(user=request.user, book__saga=saga)
            userBook = sorted(userBook, key=lambda x: x.book.tome)
            return render(request, 'details.html', context={'books': userBook, 'saga': saga})   
    
@method_decorator(login_required, name='dispatch')
class add_view(View):
    def get(self, request):
        return render(request, 'add_data.html')        
    
class friends_view(View):
    def get(self, request):
        user = request.user
        friends = Friendship.objects.filter(user=user, status=Friendship.Status.ACCEPTED) | Friendship.objects.filter(user=user, status=Friendship.Status.INVITED)
        #news de tous les amis
        news = News.objects.filter(user__in=[friend.friend for friend in friends]).order_by('-created_at')

        return render(request, 'friends.html', context={'news': news})
    
class friend_view(View):
    def get(self, request, link):
        user = CustomUser.objects.get(new_user_link_url=link)
        books = get_books(user)
        return render(request, 'friend.html', context={
            'books': books, 
            'user': user,
            'link': link,
        })