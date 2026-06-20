"""
账户模块视图。

负责用户登录、退出、注册、查看与修改个人档案、管理员管理用户列表等。
"""
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .forms import (
    LoginForm, RegisterForm, UserProfileForm, UserAdminForm,
)
from .models import OperationLog, UserProfile
from .decorators import admin_required, editor_required
from django.conf import settings


def _log_action(user, action, target='', detail=''):
    """记录操作日志的内部工具函数。"""
    OperationLog.objects.create(
        user=user, action=action, target=target, detail=detail
    )


def login_view(request):
    """用户登录视图。

    GET : 显示登录表单
    POST: 校验凭据, 成功则跳转到 next 或看板首页
    """
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        _log_action(user, 'login', detail=f'IP: {request.META.get("REMOTE_ADDR")}')
        messages.success(request, f'欢迎回来, {user.username}!')
        next_url = request.GET.get('next') or 'dashboard:index'
        return redirect(next_url)

    return render(request, 'registration/login.html', {'form': form})


def register_view(request):
    """用户注册视图(默认仅创建 viewer/keeper 角色, 不能创建 admin)。"""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        _log_action(user, 'create', target=f'用户:{user.username}')
        messages.success(request, '注册成功, 请使用新账号登录。')
        return redirect('accounts:login')

    return render(request, 'registration/register.html', {'form': form})


@login_required
def logout_view(request):
    """用户退出登录。"""
    _log_action(request.user, 'logout')
    logout(request)
    messages.info(request, '您已成功退出。')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """查看与修改个人档案。"""
    profile = request.user.profile
    form = UserProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '个人资料已更新。')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'form': form, 'profile': profile})


@admin_required
def user_list_view(request):
    """管理员查看全部用户列表(可改角色、停用账号)。"""
    users = User.objects.select_related('profile').all().order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {'users': users})


@admin_required
def user_edit_view(request, pk):
    """管理员编辑某用户的角色与基本信息。"""
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser and request.user.pk != user.pk:
        messages.error(request, '无法编辑超级管理员。')
        return redirect('accounts:user_list')

    form = UserAdminForm(request.POST or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        _log_action(request.user, 'update', target=f'用户:{user.username}',
                    detail=f'角色调整为 {form.cleaned_data["role"]}')
        messages.success(request, '用户信息已更新。')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_edit.html', {'form': form, 'target_user': user})


@require_POST
@admin_required
def user_toggle_active_view(request, pk):
    """启用/停用账号(管理员)。"""
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser:
        messages.error(request, '无法停用超级管理员。')
        return redirect('accounts:user_list')
    user.is_active = not user.is_active
    user.save()
    status = '启用' if user.is_active else '停用'
    _log_action(request.user, 'update', target=f'用户:{user.username}',
                detail=f'账号状态:{status}')
    messages.success(request, f'账号 {user.username} 已{status}。')
    return redirect('accounts:user_list')


@login_required
def operation_log_view(request):
    """操作日志查询页(所有用户可查看, 仅本人相关或所有, 取决于角色)。"""
    logs = OperationLog.objects.select_related('user').all()
    # 普通查看者只看自己的日志
    if not (request.user.is_superuser or request.user.profile.can_edit()):
        logs = logs.filter(user=request.user)
    logs = logs[:200]  # 最多展示最近 200 条
    return render(request, 'accounts/logs.html', {'logs': logs})
