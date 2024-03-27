from django.core.mail import send_mail
import logging
import random
import string
import os
import requests
import json 
from openai import OpenAI
from .models import CustomUser, Book, Saga, UserBook, Friendship, News

########
# RANDOM
########

def random_string(length):
    possible_characters = string.ascii_lowercase + string.digits
    random_chars = [random.choice(possible_characters) for _ in range(length)]
    random_string = ''.join(random_chars)

    return random_string

########
# EMAIL
########

def send_email(request, url_linl, to_email):
    try:
        send_mail(
            "Invitation a MyBookcase.online",
            """Bonjour,

    Bienvenue sur MyBookcase.online !

    Pour commencer à utiliser votre compte, veuillez cliquer sur le bouton ci-dessous :

    [Commencer](""" + os.getenv('URL_LOCAL') + """/accounts/login/""" + url_linl + """)

    Cordialement,
    L'équipe MyBookcase.online""",
            "contact@mybookcase.online",
            [to_email],
            fail_silently=False,
        )
        logging.warning(f"Email envoyé à {to_email}")
        return True
    except:
        return False
    
########
# Get BOKKS
########

def get_books(user):
    output_books= {}
    all_books = UserBook.objects.filter(user=user)
    if all_books:
        for tmp_book in all_books:
            book = tmp_book.book
            if book.saga != None:
                saga = book.saga.name
                if saga in output_books:
                    output_books[saga].append(book.tome)
                else:
                    output_books[saga] = [book.tome]
            else:
                if not book.title in output_books:
                    output_books[book.title] = ""
        logging.warning(output_books)
        return sorted([(saga, sorted(tomes)) for saga, tomes in output_books.items()], key=lambda x: x[0])
    
########
# MESSAGES NEWs
########

class MessagesNews:
    def title_book(self, book):
        title = ""
        if book.title == "Pas de titre":
            if book.saga is None or book.tome == -1:
                title = f"Probleme avec le livre {book.isbn}"
            else:
                title = f"{book.saga.name} - tome {book.tome}"
        else:
            title = book.title
        return title
  
    def new_book(self, user, book):
        return f'{user.username} vient d\'ajouter le livre "{self.title_book(book)}" à sa bibliothèque'
    
    def update_status_book_1(self, user, book):
        return f'{user.username} vient de commencer à lire le livre "{self.title_book(book)}"'
    
    def update_status_book_2(self, user, book):
        return f'{user.username} vient de finir de lire le livre "{self.title_book(book)}"'
    
    def update_status_book_3(self, user, book):
       
        return f'{user.username} vient d\'abandonner la lecture du livre "{self.title_book(book)}"'
    
    def add_news(self, user, status, book=None):
        if book is None or (status < 0 or status > 3) or user is None:
            return
        message = "Probleme avec cette news"
        if status == 0:
            message = self.new_book(user, book)
        elif status == 1:
            message = self.update_status_book_1(user, book)
        elif status == 2:
            message = self.update_status_book_2(user, book)
        elif status == 3:
            message = self.update_status_book_3(user, book)
        News.objects.create(user=user, content=message, book=book)
        
########
# API EXT BOOK
########
# 9782723493062

def get_book_from_isbn(isbn):
    api_response = requests.get(
        f"https://api2.isbndb.com/book/{isbn}", 
        headers={
            'Authorization': os.getenv('API_KEY_ISBNDB')
            })
    api_response = api_response.json()
    if "errorMessage" in api_response:
        return None

    client = OpenAI()
    response = client.chat.completions.create(
        # model="gpt-4",
        model="gpt-3.5-turbo",
        messages=[
            {
            "role": "system",
            "content": "L'input est le titre long de la db de isbn. Retourne en format json reprenant le titre, le volume et la saga. Si il y a un numero de tome mais pas de saga alors la saga est dans le titre. Si il y n'y a pas de numero de tome alors il ne doit pas y avoir de saga. Voici le template doutput  { title: (string), volume: (int), saga: (string)}N'hesite pas a aller voir sur des sites specialise pour voir le vrai titre et nom de saga"
            },
            {
            "role": "user",
            "content": "isbn : " + api_response['book']['title_long']
            }
        ],
        temperature=0,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    json_datas = json.loads(response.choices[0].message.content)    
    return json_datas['title'], json_datas['volume'], json_datas['saga']


        