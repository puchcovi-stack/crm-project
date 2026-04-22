from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta, datetime
from .models import Property, Client

# Словарь для русского перевода месяцев
MONTHS_RU = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август", 
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

def get_counts():
    prop_counts = Property.objects.aggregate(
        sale=Count('id', filter=Q(deal_type='sale')),
        rent=Count('id', filter=Q(deal_type='rent'))
    )
    client_counts = Client.objects.aggregate(
        buyers=Count('id', filter=Q(request_type='buy')),
        renters=Count('id', filter=Q(request_type='rent'))
    )
    return {
        'sale': prop_counts['sale'],
        'rent': prop_counts['rent'],
        'buyers': client_counts['buyers'],
        'renters': client_counts['renters'],
    }

def get_base_context(active_tab, items):
    thirty_days_ago = timezone.now() - timedelta(days=30)
    return {
        'items': items.select_related('manager') if items else [],
        'active_tab': active_tab,
        'counts': get_counts(),
        'users': User.objects.filter(is_active=True).order_by('username'),
        'thirty_days_ago': thirty_days_ago
    }

@login_required
def properties_sale(request):
    items = Property.objects.filter(deal_type='sale')
    return render(request, 'crm/properties_table.html', get_base_context('sale', items))

@login_required
def properties_rent(request):
    items = Property.objects.filter(deal_type='rent')
    return render(request, 'crm/properties_table.html', get_base_context('rent', items))

@login_required
def buyers_list(request):
    items = Client.objects.filter(request_type='buy')
    return render(request, 'crm/clients_table.html', get_base_context('buyers', items))

@login_required
def renters_list(request):
    items = Client.objects.filter(request_type='rent')
    return render(request, 'crm/clients_table.html', get_base_context('renters', items))

@login_required
def reports_view(request):
    if not request.user.is_staff:
        return redirect('home')

    period = request.GET.get('period', 'month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    today = timezone.now()
    
    if period == 'year':
        start = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = today
        report_label = f"За {today.year} год"
    elif period == 'custom' and start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            start = timezone.make_aware(start)
            end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            end = timezone.make_aware(end)
            report_label = f"С {start.strftime('%d.%m.%Y')} по {end.strftime('%d.%m.%Y')}"
        except ValueError:
            return redirect('reports')
    else:
        start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = today
        month_name = MONTHS_RU.get(today.month)
        report_label = f"За {month_name} {today.year} года"
        period = 'month'

    report_data = User.objects.filter(is_active=True, is_staff=False).annotate(
        p_sale=Count('properties', filter=Q(properties__deal_type='sale', properties__created_at__range=(start, end)), distinct=True),
        p_rent=Count('properties', filter=Q(properties__deal_type='rent', properties__created_at__range=(start, end)), distinct=True),
        c_buy=Count('clients', filter=Q(clients__request_type='buy', clients__created_at__range=(start, end)), distinct=True),
        c_rent=Count('clients', filter=Q(clients__request_type='rent', clients__created_at__range=(start, end)), distinct=True),
    ).order_by('username')

    totals = {
        'buyers': sum(m.c_buy for m in report_data),
        'renters': sum(m.c_rent for m in report_data),
        'sale': sum(m.p_sale for m in report_data),
        'rent': sum(m.p_rent for m in report_data),
    }

    context = get_base_context('reports', None)
    context.update({
        'report_data': report_data,
        'report_label': report_label,
        'current_period': period,
        'period_totals': totals
    })
    return render(request, 'crm/reports.html', context)

@login_required
def info_view(request):
    if not request.user.is_staff:
        return redirect('home')
    
    import os
    project_structure = []
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for root, dirs, files in os.walk(base_dir):
        # Исключаем папки __pycache__, .git, migrations и другие служебные
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'migrations', 'staticfiles', 'venv', '.venv', 'node_modules']]
        
        level = root.replace(base_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        relative_root = os.path.relpath(root, base_dir)
        if relative_root == '.':
            project_structure.append({'name': os.path.basename(base_dir) + '/', 'level': 0, 'type': 'dir', 'path': ''})
        else:
            project_structure.append({'name': os.path.basename(root) + '/', 'level': level, 'type': 'dir', 'path': relative_root})
        
        sub_indent = ' ' * 2 * (level + 1)
        for file in sorted(files):
            if file.endswith('.pyc') or file.startswith('.'):
                continue
            file_path = os.path.join(relative_root, file) if relative_root != '.' else file
            project_structure.append({'name': file, 'level': level + 1, 'type': 'file', 'path': file_path})
    
    context = get_base_context('info', None)
    context['project_structure'] = project_structure
    return render(request, 'crm/info.html', context)

# --- API ---
def clean_float(value):
    try: return float(value.replace(',', '.')) if value else None
    except ValueError: return None
def clean_int(value, default=None):
    try: return int(value) if value else default
    except ValueError: return default
def clean_string(value):
    if value is None: return None
    val = str(value).strip()
    return val if val else None

@login_required
@require_POST
def add_record(request):
    record_type = request.POST.get('recordType'); deal_type = request.POST.get('dealType')
    assigned_manager_obj = request.user 
    if request.user.is_staff:
        manager_id = request.POST.get('manager_id')
        if manager_id: assigned_manager_obj = User.objects.filter(id=manager_id).first() or request.user
    try:
        if record_type == 'property':
            Property.objects.create(deal_type=deal_type, owner_name=request.POST.get('owner_name', ''), phone=request.POST.get('phone', ''), address=request.POST.get('address', ''), area=clean_float(request.POST.get('area')), price=clean_float(request.POST.get('price')), levels=clean_int(request.POST.get('levels'), 1), floor=clean_string(request.POST.get('floor')), total_floors=clean_string(request.POST.get('total_floors')), notes=request.POST.get('notes', ''), manager=assigned_manager_obj)
        elif record_type == 'client':
            Client.objects.create(request_type=deal_type, name=request.POST.get('name', ''), phone=request.POST.get('phone', ''), budget=clean_float(request.POST.get('budget')), area_required=request.POST.get('area_required', ''), property_type=request.POST.get('property_type', ''), location=request.POST.get('location', ''), activity_type=request.POST.get('activity_type', ''), company_name=request.POST.get('company_name', ''), floor_pref=request.POST.get('floor_pref', ''), notes=request.POST.get('notes', ''), manager=assigned_manager_obj)
        return JsonResponse({'status': 'ok'})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def toggle_status(request):
    record_id = request.POST.get('record_id'); record_type = request.POST.get('record_type')
    try:
        obj = Property.objects.get(id=record_id) if record_type == 'property' else Client.objects.get(id=record_id)
        if not request.user.is_staff and obj.manager != request.user: return JsonResponse({'status': 'error', 'message': 'Отказано в доступе.'})
        obj.status = 'not_actual' if obj.status == 'actual' else 'actual'; obj.save()
        return JsonResponse({'status': 'ok', 'new_status': obj.status})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
@require_POST
def update_date(request):
    record_id = request.POST.get('record_id'); record_type = request.POST.get('record_type')
    try:
        obj = Property.objects.get(id=record_id) if record_type == 'property' else Client.objects.get(id=record_id)
        if not request.user.is_staff and obj.manager != request.user: return JsonResponse({'status': 'error', 'message': 'Отказано в доступе.'})
        obj.date_added = timezone.now(); obj.save()
        return JsonResponse({'status': 'ok', 'new_date_str': obj.date_added.strftime('%d.%m.%Y'), 'new_date_order': obj.date_added.strftime('%Y%m%d')})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
@require_POST
def get_record(request):
    record_id = request.POST.get('record_id'); record_type = request.POST.get('record_type')
    try:
        obj = Property.objects.get(id=record_id) if record_type == 'property' else Client.objects.get(id=record_id)
        if not request.user.is_staff and obj.manager != request.user: return JsonResponse({'status': 'denied'})
        data = {'manager_id': obj.manager.id if obj.manager else ''}
        if record_type == 'property':
            data.update({'dealType': obj.deal_type, 'owner_name': obj.owner_name or '', 'phone': obj.phone or '', 'address': obj.address or '', 'area': obj.area or '', 'price': obj.price or '', 'levels': obj.levels or '', 'floor': obj.floor or '', 'total_floors': obj.total_floors or '', 'notes': obj.notes or ''})
        elif record_type == 'client':
            data.update({'dealType': obj.request_type, 'name': obj.name or '', 'phone': obj.phone or '', 'budget': obj.budget or '', 'area_required': obj.area_required or '', 'property_type': obj.property_type or '', 'location': obj.location or '', 'activity_type': obj.activity_type or '', 'company_name': obj.company_name or '', 'floor_pref': obj.floor_pref or '', 'notes': obj.notes or ''})
        return JsonResponse({'status': 'ok', 'data': data})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
@require_POST
def edit_record(request):
    record_id = request.POST.get('record_id'); record_type = request.POST.get('recordType') or request.POST.get('record_type')
    try:
        obj = Property.objects.get(id=record_id) if record_type == 'property' else Client.objects.get(id=record_id)
        if not request.user.is_staff and obj.manager != request.user: return JsonResponse({'status': 'error', 'message': 'Отказано в доступе.'})
        if request.user.is_staff:
            manager_id = request.POST.get('manager_id')
            if manager_id:
                new_manager = User.objects.filter(id=manager_id).first()
                if new_manager: obj.manager = new_manager
        if record_type == 'property':
            obj.owner_name = request.POST.get('owner_name', ''); obj.phone = request.POST.get('phone', ''); obj.address = request.POST.get('address', ''); obj.area = clean_float(request.POST.get('area')); obj.price = clean_float(request.POST.get('price')); obj.levels = clean_int(request.POST.get('levels'), 1); obj.floor = clean_string(request.POST.get('floor')); obj.total_floors = clean_string(request.POST.get('total_floors')); obj.notes = request.POST.get('notes', '')
        elif record_type == 'client':
            obj.name = request.POST.get('name', ''); obj.phone = request.POST.get('phone', ''); obj.budget = clean_float(request.POST.get('budget')); obj.area_required = request.POST.get('area_required', ''); obj.property_type = request.POST.get('property_type', ''); obj.location = request.POST.get('location', ''); obj.activity_type = request.POST.get('activity_type', ''); obj.company_name = request.POST.get('company_name', ''); obj.floor_pref = request.POST.get('floor_pref', ''); obj.notes = request.POST.get('notes', '')
        obj.save(); return JsonResponse({'status': 'ok'})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
@require_POST
def delete_record(request):
    record_id = request.POST.get('record_id'); record_type = request.POST.get('record_type')
    if not request.user.is_staff: return JsonResponse({'status': 'error', 'message': 'Отказано в доступе.'})
    try:
        obj = Property.objects.get(id=record_id) if record_type == 'property' else Client.objects.get(id=record_id)
        obj.delete(); return JsonResponse({'status': 'ok'})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})
  # Тестовый комментарий для проверки авто-деплоя  