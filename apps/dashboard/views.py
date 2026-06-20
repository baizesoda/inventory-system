"""
数据看板视图。

提供:
    - 顶部 KPI 指标卡片(商品总数、库存总价值、今日入库、今日出库)
    - 商品分类分布饼图(按数量/金额)
    - 近 30 天出入库趋势折线图
    - 低库存预警列表
    - 最近操作日志
"""
from datetime import timedelta
import json

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from apps.products.models import Product, Category
from apps.inventory.models import InOutRecord
from apps.accounts.models import OperationLog


def _default_date_range(days=30):
    """返回最近 N 天的起止日期。"""
    end = timezone.now().date()
    start = end - timedelta(days=days - 1)
    return start, end


@login_required
def index(request):
    """看板首页。"""
    today = timezone.now().date()
    start_30, end_30 = _default_date_range(30)

    # KPI 指标
    total_products = Product.objects.filter(is_active=True).count()
    total_stock_value = sum(p.stock_value for p in Product.objects.all())
    today_in = InOutRecord.objects.filter(
        type='inbound', created_at__date=today
    ).aggregate(t=Sum('quantity'))['t'] or 0
    today_out = InOutRecord.objects.filter(
        type='outbound', created_at__date=today
    ).aggregate(t=Sum('quantity'))['t'] or 0

    # 低库存预警(取前 10 条)
    low_stock_products = list(
        Product.objects.filter(stock__lte=F('safety_stock'), is_active=True)
        .order_by('stock')[:10]
    )

    # 分类分布(数量与库存金额)
    category_dist = list(
        Category.objects.annotate(
            product_count=Count('products', filter=Q(products__is_active=True)),
            stock_qty=Sum('products__stock'),
        ).values('name', 'product_count', 'stock_qty')
    )

    # 近 30 天出入库趋势
    trend = _build_trend(start_30, end_30)

    # 最近 10 条操作日志
    recent_logs = OperationLog.objects.select_related('user').all()[:10]

    return render(request, 'dashboard/index.html', {
        'kpis': {
            'total_products': total_products,
            'total_stock_value': total_stock_value,
            'today_in': today_in,
            'today_out': today_out,
        },
        'low_stock_products': low_stock_products,
        'category_dist': category_dist,
        'trend_json': json.dumps(trend, ensure_ascii=False),
        'recent_logs': recent_logs,
    })


def _build_trend(start, end):
    """构造近 N 天按日聚合的入库/出库趋势数据。"""
    qs = InOutRecord.objects.filter(
        created_at__date__gte=start, created_at__date__lte=end,
    ).annotate(day=TruncDate('created_at')).values('day', 'type').annotate(
        qty=Sum('quantity')).order_by('day')

    # 构造 day -> {in, out} 映射
    mapping = {}
    cur = start
    while cur <= end:
        mapping[cur] = {'in_qty': 0, 'out_qty': 0}
        cur += timedelta(days=1)
    for row in qs:
        day = row['day']
        if day in mapping:
            if row['type'] == 'inbound':
                mapping[day]['in_qty'] = row['qty']
            else:
                mapping[day]['out_qty'] = row['qty']

    return {
        'days': [d.strftime('%m-%d') for d in sorted(mapping.keys())],
        'in_qty': [mapping[d]['in_qty'] for d in sorted(mapping.keys())],
        'out_qty': [mapping[d]['out_qty'] for d in sorted(mapping.keys())],
    }


@login_required
def trend_api(request):
    """返回趋势 JSON(供前端 AJAX 刷新)。"""
    days = int(request.GET.get('days', 30))
    start, end = _default_date_range(days)
    return JsonResponse(_build_trend(start, end))
