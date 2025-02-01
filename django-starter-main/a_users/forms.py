from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import User
from .models import *

class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'displayname', 'info' ]
        widgets = {
            'image': forms.FileInput(),
            'displayname' : forms.TextInput(attrs={'placeholder': 'Add display name'}),
            'info' : forms.Textarea(attrs={'rows':3, 'placeholder': 'Add information'})
        }
        
        
class EmailForm(ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['email']


class ChangeAvatarForm(forms.Form):
    selected_avatar = forms.ChoiceField(
        choices=Profile.AVATAR_CHOICES,
        widget=forms.RadioSelect,
        label="Choose an Avatar",
    )
