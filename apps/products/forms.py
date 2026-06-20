"""
商品模块表单。
"""
from django import forms

from .models import Category, Product


class CategoryForm(forms.ModelForm):
    """商品分类新增/编辑表单。"""

    class Meta:
        model = Category
        fields = ('name', 'code', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}),
        }


class ProductForm(forms.ModelForm):
    """商品新增/编辑表单。"""

    class Meta:
        model = Product
        fields = (
            'sku', 'barcode', 'name', 'category', 'specification', 'unit',
            'price', 'cost', 'safety_stock', 'image', 'remark', 'is_active',
        )
        widgets = {
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'barcode': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '扫码或输入条形码, 留空则不绑定'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'specification': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'safety_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_sku(self):
        """SKU 编号统一大写, 防止重复。"""
        sku = self.cleaned_data['sku'].strip().upper()
        return sku


class ProductSearchForm(forms.Form):
    """商品列表搜索表单。"""
    keyword = forms.CharField(
        label='关键字', required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'SKU 或名称'}),
    )
    category = forms.ModelChoiceField(
        label='分类', required=False, queryset=Category.objects.all(),
        empty_label='全部', widget=forms.Select(attrs={'class': 'form-select'}),
    )
    low_stock_only = forms.BooleanField(
        label='仅低库存', required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
