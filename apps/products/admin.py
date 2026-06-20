"""
商品模块 admin 配置。
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'description', 'created_at')
    search_fields = ('name', 'code')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'specification', 'unit',
                    'price', 'stock', '_safety', '_status')
    list_filter = ('category', 'is_active', 'unit')
    search_fields = ('sku', 'name', 'specification')
    readonly_fields = ('stock', 'created_at', 'updated_at')

    def _safety(self, obj):
        color = 'red' if obj.is_low_stock else 'green'
        return format_html('<span style="color:{};">{}/{}</span>',
                           color, obj.stock, obj.safety_stock)
    _safety.short_description = '库存/警戒'

    def _status(self, obj):
        return '在用' if obj.is_active else '停用'
    _status.short_description = '状态'
