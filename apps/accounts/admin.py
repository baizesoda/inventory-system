"""
账户模块管理员配置。

将 UserProfile 与 OperationLog 注册到 Django 自带的 admin 后台,
便于超级管理员直接进行数据维护。
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import UserProfile, OperationLog


class UserProfileInline(admin.StackedInline):
    """在 User 编辑页内联显示 UserProfile。"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = '用户档案'


class CustomUserAdmin(UserAdmin):
    """扩展内置 UserAdmin, 显示关联的 Profile。"""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'is_staff', 'get_role')

    def get_role(self, obj):
        return obj.profile.get_role_display() if hasattr(obj, 'profile') else '-'
    get_role.short_description = '角色'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    """操作日志只读展示。"""
    list_display = ('user', 'action', 'target', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'target', 'detail')
    readonly_fields = ('user', 'action', 'target', 'detail', 'created_at')

    def has_add_permission(self, request):
        # 日志由系统自动生成, 不允许手动新增
        return False
