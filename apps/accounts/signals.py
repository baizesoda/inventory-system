"""
信号处理器。

监听 User 创建事件, 自动为其创建关联的 UserProfile, 避免业务代码
访问 request.user.profile 时出现 DoesNotExist 异常。
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """新用户创建时自动生成 UserProfile。"""
    if created and not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """保存 User 时同步保存 UserProfile。"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
