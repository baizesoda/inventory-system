"""
库存模块数据模型。

核心模型 InOutRecord 记录每一条出入库流水, 通过事务保证与 Product.stock 的一致性。

设计要点:
    - 出入库类型(inbound/outbound)与商品库存为反向修改关系
    - 使用 Django 事务 (atomic) 保证一致性
    - 通过 related_name='inout_records' 与 Product 关联
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone

from apps.products.models import Product


class InOutRecord(models.Model):
    """出入库流水记录。"""

    TYPE_CHOICES = [
        ('inbound', '入库'),    # 入库: 库存 += quantity
        ('outbound', '出库'),   # 出库: 库存 -= quantity
    ]

    product = models.ForeignKey(
        Product, on_delete=models.PROTECT,
        related_name='inout_records', verbose_name='商品',
    )
    type = models.CharField('类型', max_length=10, choices=TYPE_CHOICES)
    quantity = models.PositiveIntegerField(
        '数量', validators=[MinValueValidator(1)],
    )
    unit_price = models.DecimalField(
        '单价(元)', max_digits=10, decimal_places=2, default=0,
        help_text='本次出入库单价, 用于成本/销售统计',
    )
    operator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='inout_records', verbose_name='操作人',
    )
    remark = models.CharField('备注', max_length=200, blank=True)
    created_at = models.DateTimeField('操作时间', default=timezone.now)

    class Meta:
        verbose_name = '出入库流水'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['type', 'created_at']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f'[{self.created_at:%Y-%m-%d %H:%M}] {self.get_type_display()} ' \
               f'{self.product.sku} x {self.quantity}'

    @property
    def total_amount(self):
        """本条流水的总金额。"""
        return float(self.quantity) * float(self.unit_price)


class StockCheck(models.Model):
    """库存盘点记录(可选模块, 用于定期盘点差异)。"""

    product = models.ForeignKey(
        Product, on_delete=models.PROTECT,
        related_name='stock_checks', verbose_name='商品',
    )
    recorded_stock = models.IntegerField('系统库存')
    actual_stock = models.IntegerField('实际盘点库存')
    difference = models.IntegerField('差异', editable=False)
    operator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='stock_checks', verbose_name='盘点人',
    )
    remark = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('盘点时间', auto_now_add=True)

    class Meta:
        verbose_name = '盘点记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """保存时自动计算差异。"""
        self.difference = self.actual_stock - self.recorded_stock
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.product.sku} 差异 {self.difference} ({self.created_at:%Y-%m-%d})'
