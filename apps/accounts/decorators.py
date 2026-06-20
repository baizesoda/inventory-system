"""
权限装饰器。

提供基于角色的访问控制(RBAC), 在视图层对用户进行权限校验。
用法:
    @login_required
    @role_required('admin', 'keeper')
    def my_view(request):
        ...
"""
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


def role_required(*roles):
    """限制视图只能由指定角色访问。

    参数:
        *roles: 允许访问的角色标识(如 'admin', 'keeper')

    返回:
        装饰器函数。已登录但无权限的用户会被重定向到看板并提示。
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required  # 必须先登录
        def _wrapped(request, *args, **kwargs):
            user_role = getattr(request.user.profile, 'role', None)
            if user_role in roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            messages.error(request, '权限不足, 无法执行此操作。')
            return redirect('dashboard:index')
        return _wrapped
    return decorator


def admin_required(view_func):
    """仅管理员可访问。"""
    return role_required('admin')(view_func)


def editor_required(view_func):
    """管理员或库管员(具备编辑权限)可访问。"""
    return role_required('admin', 'keeper')(view_func)
