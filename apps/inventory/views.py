"""
库存模块视图。

提供出入库流水查询、新增入库/出库、库存盘点等功能。
所有写操作必须由 editor_required 角色(管理员、库管员)执行, 在事务中
更新 Product.stock, 并写入 InOutRecord 流水。
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import render, redirect, get_object_or_404

from apps.accounts.decorators import editor_required
from apps.accounts.models import OperationLog
from apps.products.models import Product
from django.conf import settings

from .models import InOutRecord, StockCheck
from .forms import InOutRecordForm, StockCheckForm


def _log(request, action, target, detail=''):
    OperationLog.objects.create(
        user=request.user, action=action, target=target, detail=detail,
    )


@login_required
def record_list(request):
    """出入库流水列表(支持按商品、类型、日期筛选)。"""
    records = InOutRecord.objects.select_related('product', 'operator').all()

    keyword = request.GET.get('keyword', '').strip()
    if keyword:
        records = records.filter(
            Q(product__sku__icontains=keyword) |
            Q(product__name__icontains=keyword) |
            Q(remark__icontains=keyword)
        )

    rtype = request.GET.get('type')
    if rtype in ('inbound', 'outbound'):
        records = records.filter(type=rtype)

    date_from = request.GET.get('date_from')
    if date_from:
        records = records.filter(created_at__date__gte=date_from)
    date_to = request.GET.get('date_to')
    if date_to:
        records = records.filter(created_at__date__lte=date_to)

    records = records.order_by('-created_at')
    paginator = Paginator(records, settings.PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get('page'))

    # 顶部统计当前筛选范围内的入库/出库汇总
    summary = records.aggregate(
        in_qty=Sum('quantity', filter=Q(type='inbound')),
        out_qty=Sum('quantity', filter=Q(type='outbound')),
    )
    return render(request, 'inventory/record_list.html', {
        'page_obj': page_obj,
        'summary': {
            'in_qty': summary['in_qty'] or 0,
            'out_qty': summary['out_qty'] or 0,
        },
        'filters': request.GET,
    })


@editor_required
def record_create(request):
    """新增出入库流水(在同一事务中调整库存)。"""
    form = InOutRecordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            record = form.save(commit=False)
            record.operator = request.user
            product = Product.objects.select_for_update().get(pk=record.product.pk)
            if record.type == 'inbound':
                product.stock += record.quantity
            else:
                # 二次校验, 避免并发场景下库存超扣
                if record.quantity > product.stock:
                    messages.error(
                        request,
                        f'出库失败: 当前库存仅剩 {product.stock}, 不足以出库 {record.quantity}。'
                    )
                    return render(request, 'inventory/record_form.html',
                                  {'form': form, 'title': '新增出入库'})
                product.stock -= record.quantity
            product.save(update_fields=['stock', 'updated_at'])
            record.save()
            _log(request, record.type,
                 target=f'商品:{product.sku}',
                 detail=f'数量 {record.quantity}, 类型 {record.get_type_display()}')
        messages.success(request, f'{record.get_type_display()}记录已生成, 库存已更新。')
        return redirect('inventory:record_list')
    return render(request, 'inventory/record_form.html',
                  {'form': form, 'title': '新增出入库'})


@login_required
def record_detail(request, pk):
    """流水详情。"""
    record = get_object_or_404(InOutRecord.objects.select_related('product', 'operator'),
                               pk=pk)
    return render(request, 'inventory/record_detail.html', {'record': record})


@editor_required
def record_delete(request, pk):
    """撤销流水(在同一事务中回滚库存)。"""
    record = get_object_or_404(InOutRecord, pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=record.product.pk)
            # 反向调整库存
            if record.type == 'inbound':
                product.stock = max(0, product.stock - record.quantity)
            else:
                product.stock += record.quantity
            product.save(update_fields=['stock', 'updated_at'])
            _log(request, 'delete',
                 target=f'流水:{record.pk}',
                 detail=f'撤销 {record.get_type_display()} {record.product.sku} x {record.quantity}')
            record.delete()
        messages.success(request, '流水已撤销, 库存已回滚。')
        return redirect('inventory:record_list')
    return render(request, 'inventory/record_confirm_delete.html', {'record': record})


# ============== 库存盘点 ==============
@login_required
def check_list(request):
    """盘点记录列表。"""
    checks = StockCheck.objects.select_related('product', 'operator').all()
    paginator = Paginator(checks, settings.PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'inventory/check_list.html', {'page_obj': page_obj})


@editor_required
def check_create(request):
    """新建盘点记录(若存在差异, 自动同步库存到实际值)。"""
    form = StockCheckForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            product = Product.objects.select_for_update().get(
                pk=form.cleaned_data['product'].pk)
            check = form.save(commit=False)
            check.recorded_stock = product.stock
            check.operator = request.user
            check.save()
            # 差异不为 0 时, 自动同步实际库存并生成一条流水
            if check.difference != 0:
                record = InOutRecord.objects.create(
                    product=product,
                    type='inbound' if check.difference > 0 else 'outbound',
                    quantity=abs(check.difference),
                    unit_price=product.cost,
                    operator=request.user,
                    remark=f'盘点差异调整(盘点单 {check.pk})',
                )
                product.stock = check.actual_stock
                product.save(update_fields=['stock', 'updated_at'])
                _log(request, record.type,
                     target=f'商品:{product.sku}',
                     detail=f'盘点差异 {check.difference}')
        messages.success(request, f'盘点完成, 差异 {check.difference} 已同步。')
        return redirect('inventory:check_list')
    return render(request, 'inventory/check_form.html',
                  {'form': form, 'title': '新增盘点'})
