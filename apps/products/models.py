"""
商品模块数据模型。

包含两个核心模型:
    - Category: 商品分类(如电子产品、办公用品)
    - Product:  商品(含 SKU 编号、名称、规格、单价、警戒库存等)

商品与库存量是一对一关系, 但实际"当前库存"由 inventory 模块通过
InOutRecord 流水自动维护(避免双写不一致)。
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify


class Category(models.Model):
    """商品分类。"""

    name = models.CharField('分类名称', max_length=50, unique=True)
    code = models.CharField('分类编码', max_length=20, unique=True,
                            help_text='用于报表汇总, 建议英文/数字')
    description = models.TextField('分类描述', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '商品分类'
        verbose_name_plural = verbose_name
        ordering = ['code']

    def __str__(self):
        return self.name


class Product(models.Model):
    """商品信息。"""

    UNIT_CHOICES = [
        ('件', '件'), ('套', '套'), ('箱', '箱'),
        ('千克', '千克'), ('米', '米'), ('台', '台'), ('个', '个'),
    ]

    sku = models.CharField(
        'SKU 编号', max_length=50, unique=True,
        help_text='商品唯一标识, 如 P0001',
    )
    name = models.CharField('商品名称', max_length=100)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT,
        related_name='products', verbose_name='所属分类',
    )
    specification = models.CharField('规格型号', max_length=100, blank=True,
                                     help_text='如 "1.5L 红色"')
    unit = models.CharField('计量单位', max_length=10, choices=UNIT_CHOICES, default='件')
    price = models.DecimalField(
        '单价(元)', max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    cost = models.DecimalField(
        '成本价(元)', max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
    )
    # 当前库存量, 由 inventory 模块通过流水自动维护
    stock = models.IntegerField('当前库存', default=0,
                                validators=[MinValueValidator(0)])
    safety_stock = models.IntegerField(
        '安全库存警戒线', default=10,
        help_text='低于此值视为库存不足, 看板会高亮提醒',
    )
    image = models.ImageField('商品图片', upload_to='products/', blank=True, null=True)
    remark = models.TextField('备注', blank=True)
    is_active = models.BooleanField('在用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '商品'
        verbose_name_plural = verbose_name
        ordering = ['sku']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f'[{self.sku}] {self.name}'

    @property
    def is_low_stock(self):
        """库存是否低于安全警戒线。"""
        return self.stock <= self.safety_stock

    @property
    def stock_value(self):
        """当前库存价值(按成本价)。"""
        return float(self.stock) * float(self.cost)
