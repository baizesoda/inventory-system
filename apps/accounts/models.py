"""
账户模块数据模型。

本系统采用 Django 内置 auth.User 作为用户基础, 通过 Profile 扩展业务字段,
并通过自定义角色(Group + Permission)实现 RBAC 权限控制。

主要模型:
    - UserProfile: 用户扩展信息(角色、电话、头像等)
    - OperationLog: 关键操作审计日志(谁、何时、做了什么)
"""
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class UserProfile(models.Model):
    """用户扩展信息。

    Django 自带的 auth.User 已经包含 username/password/email/first_name 等
    基础字段, 本模型用于存储与业务相关的额外字段(如角色、电话)。

    角色通过 role 字段标记, 配合 decorators.py 中的权限装饰器实现 RBAC。
    """

    ROLE_CHOICES = [
        (settings.ROLE_ADMIN, '系统管理员'),
        (settings.ROLE_KEEPER, '库管员'),
        (settings.ROLE_VIEWER, '查看者'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='关联用户',
    )
    role = models.CharField(
        '角色',
        max_length=20,
        choices=ROLE_CHOICES,
        default=settings.ROLE_VIEWER,
        help_text='决定该用户在系统中的权限范围',
    )
    phone = models.CharField('联系电话', max_length=20, blank=True)
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '用户档案'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.user.username}({self.get_role_display()})'

    # ====== 角色判断快捷方法, 供模板和视图调用 ======
    @property
    def is_admin(self):
        return self.role == settings.ROLE_ADMIN

    @property
    def is_keeper(self):
        return self.role == settings.ROLE_KEEPER

    @property
    def is_viewer(self):
        return self.role == settings.ROLE_VIEWER

    def can_edit(self):
        """是否具备编辑权限(管理员、库管员)。"""
        return self.is_admin or self.is_keeper


class OperationLog(models.Model):
    """关键操作审计日志。

    用于追踪入库、出库、商品增删改等敏感操作, 便于责任追溯。
    """

    ACTION_CHOICES = [
        ('create', '新增'),
        ('update', '修改'),
        ('delete', '删除'),
        ('inbound', '入库'),
        ('outbound', '出库'),
        ('login', '登录'),
        ('logout', '退出'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='操作人',
    )
    action = models.CharField('操作类型', max_length=20, choices=ACTION_CHOICES)
    target = models.CharField('操作对象', max_length=200, blank=True)
    detail = models.TextField('详细描述', blank=True)
    created_at = models.DateTimeField('操作时间', auto_now_add=True)

    class Meta:
        verbose_name = '操作日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.created_at:%Y-%m-%d %H:%M}] {self.user} {self.get_action_display()} {self.target}'
