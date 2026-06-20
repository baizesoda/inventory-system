"""
账户模块表单。

包含用户登录、注册以及个人档案修改的表单。
"""
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
    PasswordChangeForm,
)

from .models import UserProfile


class LoginForm(AuthenticationForm):
    """登录表单, 仅复用 Django 内置 AuthenticationForm 并汉化。"""
    username = forms.CharField(label='用户名', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': '请输入用户名'}))
    password = forms.CharField(label='密码', widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': '请输入密码'}))


class RegisterForm(UserCreationForm):
    """用户注册表单, 注册时同时选择角色。"""
    email = forms.EmailField(label='邮箱', required=False,
                             widget=forms.EmailInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(
        label='角色',
        choices=[(r, l) for r, l in UserProfile.ROLE_CHOICES if r != 'admin'],
        initial='viewer',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = User
        fields = ('username', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        """保存用户并创建对应角色的 UserProfile。"""
        user = super().save(commit=commit)
        if commit:
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'role': self.cleaned_data['role']},
            )
        return user


class UserProfileForm(forms.ModelForm):
    """用户档案编辑表单(自己可改头像、电话; 角色由管理员控制)。"""
    email = forms.EmailField(label='邮箱', required=False,
                             widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label='姓名', required=False,
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = UserProfile
        fields = ('phone', 'avatar')
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        if commit:
            user.save()
            profile.save()
        return profile


class UserAdminForm(forms.ModelForm):
    """管理员后台用的用户管理表单(可修改角色)。"""
    role = forms.ChoiceField(
        label='角色',
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['role'].initial = self.instance.profile.role

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = self.cleaned_data['role']
            profile.save()
        return user
