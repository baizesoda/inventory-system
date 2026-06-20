"""
初始化演示数据的自定义管理命令。

用途:
    python manage.py init_demo

行为:
    1. 创建三个演示用户(admin / keeper / viewer)与对应角色
    2. 创建若干商品分类与商品
    3. 生成若干出入库流水, 使看板有数据可看
    4. 创建一个超级管理员账号(admin / admin123), 用于登录 Django admin

可重复执行, 不会重复创建已存在的数据。
"""
import os
import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.products.models import Category, Product
from apps.inventory.models import InOutRecord
from django.conf import settings


DEMO_USERS = [
    {'username': 'admin',  'password': 'admin123',  'role': settings.ROLE_ADMIN,  'name': '系统管理员'},
    {'username': 'keeper', 'password': 'keeper123', 'role': settings.ROLE_KEEPER, 'name': '库管员张三'},
    {'username': 'viewer', 'password': 'viewer123', 'role': settings.ROLE_VIEWER, 'name': '查看者李四'},
]

DEMO_CATEGORIES = [
    ('ELEC', '电子产品', '电脑、配件、办公电子'),
    ('OFFICE', '办公用品', '日常办公文具'),
    ('FOOD', '食品饮料', '员工茶水间物资'),
    ('TOOL', '工具耗材', '维修与日常工具'),
]

DEMO_PRODUCTS = [
    ('P0001', 'ThinkPad 笔记本', 'ELEC', 'X1 Carbon 16G/512G', '台', 12000, 9000, 5),
    ('P0002', '机械键盘', 'ELEC', 'Cherry 红轴 87 键', '件', 350, 200, 10),
    ('P0003', '无线鼠标', 'ELEC', 'Logitech M275', '个', 90, 55, 20),
    ('P0004', '4K 显示器', 'ELEC', 'Dell 27 寸', '台', 2200, 1700, 3),
    ('P0005', 'A4 打印纸', 'OFFICE', '500 张/包', '包', 30, 22, 50),
    ('P0006', '签字笔', 'OFFICE', '0.5mm 黑色', '支', 3, 1.8, 100),
    ('P0007', '便利贴', 'OFFICE', '76x76mm 100 张', '本', 5, 3, 80),
    ('P0008', '瓶装矿泉水', 'FOOD', '550ml 24 瓶/箱', '箱', 36, 28, 5),
    ('P0009', '速溶咖啡', 'FOOD', '100 条/盒', '盒', 80, 60, 5),
    ('P0010', '螺丝刀套装', 'TOOL', '12 件套', '套', 50, 35, 8),
    ('P0011', 'USB-C 数据线', 'ELEC', '1 米编织线', '根', 25, 12, 30),
    ('P0012', '电池组', 'TOOL', '5 号 24 粒', '盒', 28, 18, 10),
]


class Command(BaseCommand):
    help = '初始化演示数据(用户、商品、出入库流水)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('开始初始化演示数据...'))

        # 1. 创建用户
        admin_user = None
        for u in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=u['username'],
                defaults={
                    'email': f'{u["username"]}@example.com',
                    'first_name': u['name'],
                    'is_staff': u['role'] == settings.ROLE_ADMIN,
                }
            )
            if created:
                user.set_password(u['password'])
                user.save()
                UserProfile.objects.update_or_create(user=user, defaults={'role': u['role']})
                self.stdout.write(f'  + 创建用户 {user.username} ({u["role"]})')
            else:
                self.stdout.write(f'  = 用户 {user.username} 已存在, 跳过')
            if u['role'] == settings.ROLE_ADMIN:
                admin_user = user

        # 2. 创建超级管理员(用于 Django admin 登录)
        if not User.objects.filter(is_superuser=True).exists():
            su = User.objects.create_superuser(
                username='superadmin', password='admin123',
                email='superadmin@example.com')
            UserProfile.objects.update_or_create(user=su, defaults={'role': settings.ROLE_ADMIN})
            self.stdout.write(self.style.SUCCESS('  + 创建超级管理员 superadmin / admin123'))
        else:
            self.stdout.write('  = 超级管理员已存在')

        # 3. 创建分类
        cat_map = {}
        for code, name, desc in DEMO_CATEGORIES:
            cat, created = Category.objects.get_or_create(
                code=code, defaults={'name': name, 'description': desc})
            cat_map[code] = cat
            if created:
                self.stdout.write(f'  + 创建分类 {name}')

        # 4. 创建商品
        prod_map = {}
        for sku, name, cat_code, spec, unit, price, cost, safety in DEMO_PRODUCTS:
            prod, created = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    'name': name, 'category': cat_map[cat_code],
                    'specification': spec, 'unit': unit,
                    'price': price, 'cost': cost, 'safety_stock': safety,
                    'stock': random.randint(0, safety * 2),
                })
            prod_map[sku] = prod
            if created:
                self.stdout.write(f'  + 创建商品 {sku} {name}')

        # 5. 生成 30 天的随机流水(让看板有图可看)
        if not InOutRecord.objects.exists():
            self.stdout.write('  + 开始生成 30 天随机出入库流水...')
            now = timezone.now()
            operator = admin_user or User.objects.first()
            products = list(Product.objects.all())
            for day in range(30, 0, -1):
                # 每天生成 2-6 条流水
                for _ in range(random.randint(2, 6)):
                    p = random.choice(products)
                    rtype = random.choice(['inbound', 'outbound', 'inbound'])  # 入库偏多
                    qty = random.randint(1, 20)
                    InOutRecord.objects.create(
                        product=p, type=rtype, quantity=qty,
                        unit_price=p.cost if rtype == 'inbound' else p.price,
                        operator=operator,
                        remark='演示数据',
                        created_at=now - timedelta(days=day, hours=random.randint(0, 23)),
                    )
            self.stdout.write(self.style.SUCCESS('  + 流水生成完成'))

        self.stdout.write(self.style.SUCCESS('\n演示数据初始化完成!'))
        self.stdout.write(self.style.SUCCESS('\n可用账号:'))
        self.stdout.write('  admin  / admin123  (系统管理员)')
        self.stdout.write('  keeper / keeper123 (库管员)')
        self.stdout.write('  viewer / viewer123 (查看者)')
        self.stdout.write('  superadmin / admin123 (Django 超级管理员)')
