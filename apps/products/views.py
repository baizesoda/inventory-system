"""
商品模块视图。

提供商品与分类的 CRUD 接口及列表页搜索。
所有写操作都要求 editor_required(管理员或库管员)权限。
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, F, Count
from django.shortcuts import render, redirect, get_object_or_404

from apps.accounts.decorators import editor_required
from apps.accounts.models import OperationLog
from django.conf import settings

from .models import Category, Product
from .forms import (
    CategoryForm, ProductForm, ProductSearchForm,
)


def _log(request, action, target, detail=''):
    """记录操作日志的内部工具。"""
    OperationLog.objects.create(
        user=request.user, action=action, target=target, detail=detail,
    )


# ============== 商品列表与详情 ==============
@login_required
def product_list(request):
    """商品列表(支持关键字、分类、低库存筛选)。"""
    products = Product.objects.select_related('category').all()
    form = ProductSearchForm(request.GET or None)

    if form.is_valid():
        kw = form.cleaned_data.get('keyword', '').strip()
        if kw:
            products = products.filter(Q(sku__icontains=kw) | Q(name__icontains=kw))
        cat = form.cleaned_data.get('category')
        if cat:
            products = products.filter(category=cat)
        if form.cleaned_data.get('low_stock_only'):
            products = products.filter(stock__lte=F('safety_stock'))

    products = products.order_by('sku')
    paginator = Paginator(products, settings.PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'products/product_list.html', {
        'page_obj': page_obj, 'search_form': form,
    })


@login_required
def product_detail(request, pk):
    """商品详情页, 包含最近 20 条出入库流水。"""
    product = get_object_or_404(Product, pk=pk)
    records = product.inout_records.select_related('operator').order_by('-created_at')[:20]
    return render(request, 'products/product_detail.html', {
        'product': product, 'records': records,
    })


# ============== 商品 CRUD ==============
@editor_required
def product_create(request):
    """新增商品。"""
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        product = form.save()
        _log(request, 'create', target=f'商品:{product.sku}',
             detail=f'名称 {product.name}, 初始库存 {product.stock}')
        messages.success(request, f'商品 {product.sku} 已创建。')
        return redirect('products:detail', pk=product.pk)
    return render(request, 'products/product_form.html', {
        'form': form, 'title': '新增商品',
    })


@editor_required
def product_update(request, pk):
    """编辑商品。"""
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        _log(request, 'update', target=f'商品:{product.sku}')
        messages.success(request, '商品信息已更新。')
        return redirect('products:detail', pk=product.pk)
    return render(request, 'products/product_form.html', {
        'form': form, 'title': '编辑商品', 'product': product,
    })


@editor_required
def product_delete(request, pk):
    """删除商品(POST 提交)。"""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        sku = product.sku
        product.delete()
        _log(request, 'delete', target=f'商品:{sku}')
        messages.success(request, f'商品 {sku} 已删除。')
        return redirect('products:list')
    return render(request, 'products/product_confirm_delete.html', {'product': product})


# ============== 分类 CRUD ==============
@login_required
def category_list(request):
    """分类列表(附带每分类的商品数量)。"""
    categories = Category.objects.annotate(product_count=Count('products')).all()
    return render(request, 'products/category_list.html', {'categories': categories})


@editor_required
def category_create(request):
    """新增分类。"""
    form = CategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        category = form.save()
        _log(request, 'create', target=f'分类:{category.name}')
        messages.success(request, '分类已创建。')
        return redirect('products:category_list')
    return render(request, 'products/category_form.html',
                  {'form': form, 'title': '新增分类'})


@editor_required
def category_update(request, pk):
    """编辑分类。"""
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == 'POST' and form.is_valid():
        form.save()
        _log(request, 'update', target=f'分类:{category.name}')
        messages.success(request, '分类已更新。')
        return redirect('products:category_list')
    return render(request, 'products/category_form.html',
                  {'form': form, 'title': '编辑分类', 'category': category})


@editor_required
def category_delete(request, pk):
    """删除分类(若仍有商品关联, 提示禁止删除)。"""
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        if category.products.exists():
            messages.error(request, f'分类 {category.name} 下仍有商品, 无法删除。')
            return redirect('products:category_list')
        name = category.name
        category.delete()
        _log(request, 'delete', target=f'分类:{name}')
        messages.success(request, f'分类 {name} 已删除。')
        return redirect('products:category_list')
    return render(request, 'products/category_confirm_delete.html',
                  {'category': category})
