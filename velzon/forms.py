from crispy_forms.helper import FormHelper
from allauth.account.forms import LoginForm,SignupForm,ChangePasswordForm,ResetPasswordForm,ResetPasswordKeyForm,SetPasswordForm
from django.contrib.auth.forms import AuthenticationForm
from django import forms


class UserLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.fields['login'].widget = forms.TextInput(attrs={'class': 'form-control mb-2','placeholder':'Login','id':'username'})
        self.fields['login'].label="Login"
        self.fields['password'].widget = forms.PasswordInput(attrs={'class': 'form-control mb-2 position-relative','placeholder':'Senha','id':'password'})
        self.fields['password'].label="Senha"
        self.fields['remember'].widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})
        self.fields['remember'].label="Lembrar-me"
        
class UserRegistrationForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.fields['email'].widget = forms.EmailInput(attrs={'class': 'form-control mb-2','placeholder':'Enter Email','id':'email'})
        self.fields['email'].label="E-mail"
        if 'username' in self.fields:
            self.fields['username'].widget = forms.TextInput(attrs={'class': 'form-control mb-2','placeholder':'Login','id':'username1'})
        if 'password1' in self.fields:
            self.fields['password1'].widget = forms.PasswordInput(attrs={'class': 'form-control mb-2','placeholder':'Senha','id':'password'})
            self.fields['password1'].label = "Senha"
        if 'password2' in self.fields:
            self.fields['password2'].widget = forms.PasswordInput(attrs={'class': 'form-control mb-2','placeholder':'Confirme a senha','id':'password2'})
            self.fields['password2'].label = "Confirmar Senha"
class PasswordChangeForm(ChangePasswordForm):
      def __init__(self, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)

        self.fields['oldpassword'].widget = forms.PasswordInput(attrs={'class': 'form-control mb-2','placeholder':'Senha atual','id':'password3'})
        self.fields['oldpassword'].label="Senha Atual"
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class': 'form-control mb-2','placeholder':'Nova senha','id':'password4'})
        self.fields['password1'].label="Nova Senha"
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class': 'form-control mb-2','placeholder':'Confirme a senha','id':'password5'})
        self.fields['password2'].label="Confirmar Senha"
class PasswordResetForm(ResetPasswordForm):
      def __init__(self, *args, **kwargs):
        super(PasswordResetForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)

        self.fields['email'].widget = forms.EmailInput(attrs={'class': 'form-control mb-2','placeholder':' E-mail','id':'email1'})
        self.fields['email'].label="E-mail"
class PasswordResetKeyForm(ResetPasswordKeyForm):
      def __init__(self, *args, **kwargs):
        super(PasswordResetKeyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class': 'form-control mb-2','placeholder':'Nova senha','id':'password6'})
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class': 'form-control mb-2','placeholder':'Confirmar senha','id':'password7'})
        self.fields['password2'].label="Confirmar Senha"
class PasswordSetForm(SetPasswordForm):
      def __init__(self, *args, **kwargs):
        super(PasswordSetForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class': 'form-control mb-2','placeholder':'Nova senha','id':'password8'})
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class': 'form-control','placeholder':'Confirmar senha','id':'password9'})
        self.fields['password2'].label="Confirmar Senha"
