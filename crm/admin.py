from django.contrib import admin
from .models import Property, Client

@admin.action(description='Пометить как "Неактуально"')
def mark_as_not_actual(modeladmin, request, queryset):
    queryset.update(status='not_actual')

@admin.action(description='Пометить как "Актуально"')
def mark_as_actual(modeladmin, request, queryset):
    queryset.update(status='actual')

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('id', 'address', 'deal_type', 'formatted_price', 'manager', 'status')
    
    # ИЗМЕНЕНИЕ: Ищем по логину или имени связанного пользователя
    search_fields = ('address', 'owner_name', 'phone', 'manager__username', 'manager__first_name')
    
    list_filter = ('status', 'deal_type', 'manager')
    actions = [mark_as_not_actual, mark_as_actual]

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'request_type', 'budget', 'manager', 'status')
    
    # ИЗМЕНЕНИЕ: Ищем по логину или имени связанного пользователя
    search_fields = ('name', 'phone', 'company_name', 'manager__username', 'manager__first_name')
    
    list_filter = ('status', 'request_type', 'manager')
    actions = [mark_as_not_actual, mark_as_actual]