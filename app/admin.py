from django.contrib import admin
from .models import CustomUser, Book, Saga, UserBook, Friendship, News

admin.site.register(News)
admin.site.register(CustomUser)
admin.site.register(Friendship)
admin.site.register(Book)
admin.site.register(Saga)
admin.site.register(UserBook)