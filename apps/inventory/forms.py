"""
库存模块表单。
"""
from django import forms
from django.core.exceptions import ValidationError

from apps.products.models import Product
from .models import InOutRecord, StockCheck


class InOutRecordForm(forms.ModelForm):
    """出入库流水表单。提交时根据 type 自动调整库存。"""

    class Meta:
        model = InOutRecord
        fields = ('product', 'type', 'quantity', 'unit_price', 'remark')
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'remark': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 仅显示"在用"商品
        self.fields['product'].queryset = Product.objects.filter(is_active=True)

    def clean(self):
        cleaned = super().clean()
        product = cleaned.get('product')
        quantity = cleaned.get('quantity')
        rtype = cleaned.get('type')
        # 出库数量不能超过当前库存
        if product and quantity and rtype == 'outbound':
            if quantity > product.stock:
                raise ValidationError(
                    f'出库失败: 当前库存 {product.stock} 不足, 无法出库 {quantity}。'
                )
        return cleaned


class StockCheckForm(forms.ModelForm):
    """库存盘点表单。"""

    class Meta:
        model = StockCheck
        fields = ('product', 'actual_stock', 'remark')
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'actual_stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True)
