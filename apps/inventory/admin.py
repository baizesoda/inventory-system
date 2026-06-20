"""库存模块 admin 配置。"""
from django.contrib import admin

from .models import InOutRecord, StockCheck


@admin.register(InOutRecord)
class InOutRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'type', 'quantity', 'unit_price',
                    'operator', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('product__sku', 'product__name', 'remark')
    readonly_fields = ('created_at',)


@admin.register(StockCheck)
class StockCheckAdmin(admin.ModelAdmin):
    list_display = ('product', 'recorded_stock', 'actual_stock',
                    'difference', 'operator', 'created_at')
    list_filter = ('created_at',)
    readonly_fields = ('difference', 'created_at')
