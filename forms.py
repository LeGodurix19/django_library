from django import forms
from .models import CustomUser, Book, Saga, Friendship

class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'avatar']
        widgets = {
            'password': forms.PasswordInput(),
        }
       
class Update_CustomUser__PasswordForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['password']
        widgets = {
            'password': forms.PasswordInput(),
        }

class Update_CustomUser__AvatarForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['avatar']
        
class Update_CustomUser__UsernameForm(forms.ModelForm):
    username = forms.CharField(
        help_text='',
    )
    
    class Meta:
        model = CustomUser
        fields = ['username']
        
class Update_CustomUser__EmailForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email']
 
class Add__CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email']
        
class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['isbn', 'title', 'tome', 'saga']
        
class SagaForm(forms.ModelForm):
    class Meta:
        model = Saga
        fields = ['name']

class Add__FriendshipForm(forms.ModelForm):
    class Meta:
        model = Friendship
        fields = ['friend']