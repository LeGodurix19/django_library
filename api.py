import logging
from typing import Any
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.http import HttpRequest, JsonResponse
from django.forms.models import model_to_dict
from django.views import View
from urllib.parse import unquote
from datetime import datetime
import json
from .models import CustomUser, Book, Saga, UserBook, Friendship, News
from .forms import CustomUserForm, BookForm, SagaForm, Add__CustomUserForm
from .utils import send_email, random_string, MessagesNews, get_book_from_isbn
import base64
from django.core.files.base import ContentFile

messageNews = MessagesNews()   

#Mother class for all api       
class Api(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Vous devez être connecté pour accéder à cette page.'})
        return super().dispatch(request, *args, **kwargs)

class api__add_book(Api):
    def post(self, request):
        data = json.loads(request.body)
        if not ('isbn' in data and data['isbn']):
            return JsonResponse({
                'error': 'Pas de code barre fourni'
            })
        isbn = data['isbn']
        user = request.user
        if Book.objects.filter(isbn=isbn).exists() and UserBook.objects.filter(user=user, book=Book.objects.get(isbn=isbn)).exists():
            return JsonResponse({
                'error': 'Tu possedes deja ce livre dans ta bibliotheque'
            })
        if not Book.objects.filter(isbn=isbn).exists():
            title = data['title']
            tome = data['tome']
            saga = data['saga']
            book_tmp = Book.objects.create( isbn=isbn,
                                            title=title if title !="undefined" else "Pas de titre",
                                            tome=tome if tome !="" else -1,
                                            saga=Saga.objects.get(id=saga) if saga !="-1" else None)
            context = {
                'message': "Le livre " + book_tmp.title + " a ete cree et ajoute a ta bibliotheque",
            }
        else:
            book_tmp = Book.objects.get(isbn=isbn)
            context = {
                'message': "Le livre " + book_tmp.title + " a ete ajoute a ta bibliotheque (Les informations seront completes sous peu)",
            }
        UserBook.objects.create(user=user, book=book_tmp, status="A lire")
        messageNews.add_news(user, 0, book_tmp)
        return JsonResponse(context)

class api__update_book__status(Api):
    def post(self, request):
        data = json.loads(request.body)
        logging.warning(data)
        bc = data['bc']
        status = data['status']
        context = {
            'error': "Le livre " + bc + " n'existe pas",
        }
        if bc and status:
            user = CustomUser.objects.get(id=request.user.id)
            book = Book.objects.get(isbn=bc)
            userBook = UserBook.objects.get(user=user, book=book)
            userBook.status = status
            userBook.save()
            if book.saga:
                context = {
                    'message': "Le livre " + book.saga.name + ": " + str(book.tome) + " a ete mis a jour"
                }
            else:
                context = {
                    'message': "Le livre " + book.title + " a ete mis a jour"
                }
            if status == "Lu":
                messageNews.add_news(user, 2, book)
            elif status == "Abandonné":
                messageNews.add_news(user, 3, book)
            else:
                messageNews.add_news(user, 1, book)
        return JsonResponse(context)

class api__add_saga(Api):
    def post(self, request):
        if request.user.is_staff:
            data =  json.loads(request.body)
            if not ('saga' in data and data['saga']):
                return JsonResponse({
                    'error': 'Pas de saga fournie'
                })
            name = data['saga']
            if name:
                if Saga.objects.filter(name=name).exists():
                    context = {
                        'message': "La saga " + saga_tmp.name + " existe deja",
                    }
                else:
                    saga_tmp = Saga.objects.create(name=name)
                    saga_tmp.save()
                    context = {
                        'message': "La saga " + saga_tmp.name + " a ete cree",
                    }
        else:
            context = {
                'error': "Vous n'avez pas les droits necessaires",
            }
        return JsonResponse(context)

class api__update_user(Api):
    def post(self, request):
        form = json.loads(request.body)
        user = CustomUser.objects.get(id=request.user.id)
        updated = False
        if 'username' in form and form['username']:
            if CustomUser.objects.filter(username=form['username']).exists():
                return JsonResponse({
                    'error': 'Ce nom d utilisateur est deja utilise'
                })
            user.username = form['username']
            updated = True
        if 'email' in form and form['email']:
            if CustomUser.objects.filter(email=form['email']).exists():
                return JsonResponse({
                    'error': 'Cet email est deja utilise'
                })
            user.email = form['email']
            updated = True
        if 'password' in form and form['password']:
            user.set_password(form['password'])
            updated = True
        if 'avatar' in form and form['avatar']:
            format, imgstr = form['avatar'].split(';base64,') 
            ext = format.split('/')[-1] 
            data_file = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
            user.avatar.save(str(user.id) + '_avatar.' + ext, data_file)
            updated = True
        user.save()
        if updated:
            return JsonResponse({
                'message': 'Ton profil a ete mis a jour'
            })
        return JsonResponse({
            'error': 'Pas de donnees fournies'
        })

class api__add_user(Api):
    def post(self, request):
        data = json.loads(request.body)
        if CustomUser.objects.filter(email=data['email']).exists():
            return JsonResponse({
                'error': 'Cet email est deja utilise'
            })
        user = request.user
        if user.nb_added_friends > 3:
            return JsonResponse({
                'error': 'Tu ne peux pas ajouter plus de 3 amis'
            })
        user.nb_added_friends += 1
        user.save()
        random = random_string(10)
        while CustomUser.objects.filter(new_user_link_url=random).exists():
            random = random_string(10)
        new_user = CustomUser.objects.create_user(email=data['email'], new_user_link_url=random, new_user_link_date=datetime.now())
        new_user.save()
        Friendship.objects.create(user=user, friend=new_user, status="Invité")
        Friendship.objects.create(user=new_user, friend=user, status="Invité")
        send_email(request, random, user.email)
        return JsonResponse({
            'message': 'Un email a ete envoye a ' + data['email']
        })

class api__book_status(Api):
    def get(self, request, bc):
        if bc:
            if Book.objects.filter(isbn=bc).exists() and UserBook.objects.filter(user=request.user, book=Book.objects.get(isbn=bc)).exists():
                title =""
                try:
                    if Book.objects.get(isbn=bc).title == "Pas de titre":
                        title = Book.objects.get(isbn=bc).saga.name + " tome " + str(Book.objects.get(isbn=bc).tome)
                    else:
                        title = Book.objects.get(isbn=bc).title
                except:
                    title = " Titre a definir"
                return JsonResponse({
                    'message': "Tu possedes deja " + title,
                    'status': "owned"
                })
            context = {
                'message': "Tu ne possedes pas ce livre \nVeux tu l'ajouter a ta bibliotheque",
                'isbn': bc,
                'saga': sorted([ model_to_dict(saga) for saga in Saga.objects.all() ], key=lambda x: x['name'])
            }  
            if not Book.objects.filter(isbn=bc).exists():
                # try:
                #     title, tome, saga = get_book_from_isbn(bc)
                #     if saga:
                #         saga = Saga.objects.create(name=saga) if not Saga.objects.filter(name=saga).exists() else None
                #     else:
                #         saga = None
                #     if not title: title = "Pas de titre"
                #     if not tome: tome = -1
                #     context['book'] = {
                #         'title': title,
                #         'tome': tome,
                #         'saga': saga,
                #     }
                #     context['status'] = "not owned|staff"
                # except:
                #     logging.warning("Probleme avec le livre " + bc)
                context['status'] = "not owned|staff"
                context['book'] = {
                    'title': "",
                }
            else:
                context['status'] = "not owned|not staff"
                context['book'] = model_to_dict(Book.objects.get(isbn=bc)) if Book.objects.filter(isbn=bc).exists() else "none"
            return JsonResponse(context)
        return JsonResponse({
            'error': 'Pas de code barre fourni'
        })

class api__add_friend(Api):
    def post(self, request):
        data = json.loads(request.body)
        if not ('username' in data and data['username']):
            return JsonResponse({
                'error': 'Pas d utilisateur fourni'
            })
        username = data['username']
        if CustomUser.objects.filter(username=username).exists():
            user = request.user
            friend = CustomUser.objects.get(username=username)
            if Friendship.objects.filter(user=user, friend=friend).exists():
                return JsonResponse({
                    'error': 'Tu es deja ami avec ' + friend.username
                })
            Friendship.objects.create(user=user, friend=friend, status="En attente")
            return JsonResponse({
                'message': 'Une invitation a ete envoyee a ' + friend.username
            })
        return JsonResponse({
            'error': 'L utilisateur n existe pas'
        })

class api__accept_friend(Api):
    def post(self, request, link):
        if link:
            if Friendship.objects.filter(friend=request.user, status="En attente", user__new_user_link_url=link).exists():
                friendship = Friendship.objects.get(friend=request.user, status="En attente", user__new_user_link_url=link)
                friendship.status = "Accepté"
                friendship.save()
                friend = friendship.user
                friendship = Friendship.objects.create(user=request.user, status="Accepté", friend=friend)
                context = {
                    'message': "L'invitation a ete acceptee",
                }
            else:
                context = {
                    'error': "La relation n'existe pas",  
                }
        else:
            context = {
                'error': "Pas d'utilisateur fourni",
            }
        return JsonResponse(context)

class api__refuse_friend(Api):
    def post(self, request, link):
        if link:
            if Friendship.objects.filter(friend=request.user, user__new_user_link_url=link).exists() and Friendship.objects.filter(user=request.user, friend__new_user_link_url=link).exists():
                friendship = Friendship.objects.get(friend=request.user, user__new_user_link_url=link)
                friendship.delete()
                friendship = Friendship.objects.get(user=request.user, friend__new_user_link_url=link)
                friendship.delete()
                context = {
                    'message': "La relation a ete supprimee",
                }
            elif Friendship.objects.filter(friend=request.user, status="En attente", user__new_user_link_url=link).exists():
                friendship = Friendship.objects.get(friend=request.user, status="En attente", user__new_user_link_url=link)
                friendship.delete()
                context = {
                    'message': "L'invitation a ete refusee",
                }
            elif Friendship.objects.filter(user=request.user, status="En attente", friend__new_user_link_url=link).exists():
                friendship = Friendship.objects.get(user=request.user, status="En attente", friend__new_user_link_url=link)
                friendship.delete()
                context = {
                    'message': "L'invitation a ete annulee",
                }
            else:
                context = {
                    'error': "La relation n'existe pas",  
                }
        else:
            context = {
                'error': "Pas d'utilisateur fourni",
            }
        return JsonResponse(context)
