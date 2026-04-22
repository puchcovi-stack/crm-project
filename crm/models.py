from django.db import models
from django.contrib.auth.models import User
import re

class Property(models.Model):
    DEAL_CHOICES = [('sale', 'Продажа'), ('rent', 'Аренда')]
    STATUS_CHOICES = [('actual', 'Актуально'), ('not_actual', 'Неактуально')]

    deal_type = models.CharField(max_length=10, choices=DEAL_CHOICES, verbose_name="Тип сделки", default='sale')
    
    owner_name = models.CharField(max_length=100, verbose_name="Имя (Владелец/Контакт)", blank=True, null=True)
    phone = models.CharField(max_length=20, verbose_name="Телефон", blank=True, null=True)
    address = models.CharField(max_length=200, verbose_name="Адрес объекта", blank=True, null=True)
    
    area = models.FloatField(verbose_name="Площадь (м2)", blank=True, null=True)
    price = models.IntegerField(verbose_name="Стоимость (Общая)", blank=True, null=True)
    
    floor = models.CharField(max_length=50, null=True, blank=True, verbose_name="Этаж")
    total_floors = models.CharField(max_length=50, null=True, blank=True, verbose_name="Всего этажей")
    levels = models.IntegerField(verbose_name="Кол-во уровней", blank=True, null=True, default=1)
    
    notes = models.TextField(verbose_name="Примечание", blank=True, null=True)
    
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Менеджер", related_name="properties")
    
    date_added = models.DateTimeField(auto_now_add=True, verbose_name="Дата актуализации")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='actual', verbose_name="Статус")

    class Meta:
        ordering = ['id']

    @property
    def price_per_m2(self):
        if self.area and self.price and self.area > 0:
            return round(self.price / self.area)
        return 0

    @property
    def formatted_address(self):
        if not self.address:
            return "-"
        addr = str(self.address)
        addr = re.sub(r'(?i)\b(россия|рф|российская федерация)\b,?\s*', '', addr)
        addr = re.sub(r'(?i)(г\.\s*)?\bбелгород\b,?\s*', '', addr)
        return addr.strip(' ,')

    @property
    def formatted_price(self):
        return f"{self.price:,}".replace(',', ' ') if self.price else "0"

    @property
    def formatted_price_per_m2(self):
        m2_price = self.price_per_m2
        return f"{m2_price:,}".replace(',', ' ') if m2_price else "0"

    def __str__(self):
        addr_name = self.address if self.address else "Объект без адреса"
        return f"{addr_name} [{self.get_deal_type_display()}]"


class Client(models.Model):
    REQUEST_CHOICES = [('buy', 'Покупка'), ('rent', 'Аренда')]
    STATUS_CHOICES = [('actual', 'Актуально'), ('not_actual', 'Неактуально')]

    request_type = models.CharField(max_length=10, choices=REQUEST_CHOICES, verbose_name="Тип заявки", default='buy')
    
    name = models.CharField(max_length=100, verbose_name="Имя контакта", blank=True, null=True)
    phone = models.CharField(max_length=20, verbose_name="Телефон", blank=True, null=True)
    company_name = models.CharField(max_length=100, verbose_name="Название компании", blank=True, null=True)
    activity_type = models.CharField(max_length=100, verbose_name="Вид деятельности", blank=True, null=True)
    
    property_type = models.CharField(max_length=100, verbose_name="Что ищет", blank=True, null=True)
    location = models.CharField(max_length=200, verbose_name="Желаемое место/район", blank=True, null=True)
    
    area_required = models.CharField(max_length=100, verbose_name="Желаемая площадь", blank=True, null=True) 
    budget = models.IntegerField(verbose_name="Бюджет (до)", blank=True, null=True)
    floor_pref = models.CharField(max_length=50, verbose_name="Желаемый этаж", blank=True, null=True)
    
    notes = models.TextField(verbose_name="Примечание", blank=True, null=True)
    
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Менеджер", related_name="clients")
    
    date_added = models.DateTimeField(auto_now_add=True, verbose_name="Дата актуализации")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='actual', verbose_name="Статус")

    class Meta:
        ordering = ['id']

    @property
    def formatted_budget(self):
        return f"{self.budget:,}".replace(',', ' ') if self.budget else "0"

    def __str__(self):
        c_name = self.name if self.name else "Неизвестный клиент"
        return f"Заявка от {c_name} ({self.get_request_type_display()})"
