from django.contrib import admin
from django.urls import path
from app.views import *
from app.api import *
from dotenv import load_dotenv
import os

load_dotenv()
app_name = os.getenv('PROJECT_NAME')

urlpatterns = [
    path('', general_view.as_view(), name='index'),
    path('add/', add_view.as_view(), name='add'),
    path('book/status/<str:bc>', api__book_status.as_view(), name='api__book_status'),
    path('details/<str:bc>', details_view.as_view(), name='details'),
    path('admin/', admin.site.urls, name='admin'),
    
    # ACCOUNTS
    path('accounts/login/', login_view.as_view(), name='login'),
    path('accounts/login/<str:id_new_user>', login_new_user_view.as_view(), name='first_login'),
    path('accounts/logout/', logout_view.as_view(), name='logout'),
    path('accounts/params/', params_view.as_view(), name='params_view'),
    
    # FRIENDS
    path('friends/', friends_view.as_view(), name='friends'),
    path('friends/<str:link>', friend_view.as_view(), name='friend'),
    
    # API
    #   USER
    path('api/user/update', api__update_user.as_view(), name='api__update_user'),
    path('api/user/add', api__add_user.as_view(), name='api__add_user'),
    
    #   FRIEND
    path('api/friend/add', api__add_friend.as_view(), name='api__add_friend'),
    path('api/friend/accepte/<str:link>', api__accept_friend.as_view(), name='api__accept_friend'),
    path('api/friend/refuse/<str:link>', api__refuse_friend.as_view(), name='api__refuse_friend'),
    
    #   SAGA
    path('api/saga/add', api__add_saga.as_view(), name='api__add_saga'),
    
    #   BOOK
    path('api/book/add', api__add_book.as_view(), name='api__add_book'),
    path('api/book/update/status', api__update_book__status.as_view(), name='api__update_book__status'),
]
