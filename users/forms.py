from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm, UserCreationForm, UserChangeForm, PasswordChangeForm
)
from .models import User, Comment
# from django_recaptcha.fields import ReCaptchaField


class UserLoginForm(AuthenticationForm):

    username = forms.CharField(
        widget=forms.TextInput(attrs={"autofocus": True,
                                      "placeholder": "Login"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password",
                                          "placeholder": "Password"})
    )

    class Meta:
        model = User


class UserRegistrationForm(UserCreationForm):
    # Явно определяем поле email, чтобы оно было в форме
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "Email"}),
        help_text="Required. Example: user@example.com" # Необязательно, но полезно
    )

    # Можно кастомизировать и другие поля, если нужно
    username = forms.CharField(
        label="Login",
        widget=forms.TextInput(attrs={"placeholder": "Login"})
    )
    # password1 и password2 уже есть в UserCreationForm, но их виджеты можно переопределить здесь
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", # лучше new-password для регистрации
                                          "placeholder": "Password"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password",
                                          "placeholder": "Confirm password"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email


class ProfileForm(forms.ModelForm): # Меняем на forms.ModelForm
    # username и email будут обрабатываться отдельно во view, если они на основной модели User
    # Здесь оставляем поля, которые есть на модели User и которые мы хотим редактировать через эту форму
    # avatar, bio, banner_color - они у тебя в модели User
    
    bio = forms.CharField(
        widget=forms.Textarea(attrs={"placeholder": "Write something about yourself...", "rows": 3, "maxlength": "160"}), # Добавляем maxlength в виджет
        required=False,
        max_length=160 # И в поле формы
    )
    avatar = forms.ImageField(required=False)
    # header = forms.ImageField(required=False) # Если ты его тоже хочешь редактировать здесь
    banner_color = forms.CharField(max_length=100, required=False)

    class Meta:
        model = User
        fields = ['bio', 'avatar', 'banner_color']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'bio'):
            self.fields['bio'].initial = self.instance.bio

    def clean_banner_color(self):
        banner_color = self.cleaned_data.get('banner_color')
        if banner_color == "_REMOVE_BANNER_":
            return None
        return banner_color

    # Валидация для bio (на всякий случай, если в виджете maxlength не сработает или JS будет обойден)
    def clean_bio(self):
        bio = self.cleaned_data.get('bio')
        if bio and len(bio) > 160:
            raise forms.ValidationError("Bio cannot be longer than 160 characters.")
        return bio


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["title", "content"]


# --- НОВЫЕ ФОРМЫ ДЛЯ НАСТРОЕК АККАУНТА ---

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Old password",
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'autofocus': True, 'placeholder': 'Old Password'})
    )
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': 'New Password'})
    )
    new_password2 = forms.CharField(
        label="New password confirmation",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': 'Confirm New Password'})
    )

    class Meta:
        model = User # Хотя PasswordChangeForm не ModelForm, указание модели не повредит
        fields = ('old_password', 'new_password1', 'new_password2')


class EmailChangeForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'New Email', 'autocomplete': 'email'}),
        help_text="Enter your new email address."
    )

    class Meta:
        model = User
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Проверяем, что такой email еще не занят другим пользователем
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email address is already in use. Please use a different one.")
        return email
