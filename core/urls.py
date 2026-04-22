from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from crm import views

urlpatterns =[
    path('secret-boss-panel/', admin.site.urls),
    
    path('login/', auth_views.LoginView.as_view(template_name='crm/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    path('', views.properties_sale, name='home'),             
    path('sales/', views.properties_sale, name='sale_list'),        
    path('rent/', views.properties_rent, name='rent'),        
    path('rent-list/', views.properties_rent, name='rent_list'),        
    path('buyers/', views.buyers_list, name='buyers'),          
    path('renters/', views.renters_list, name='renters'),   
    
    # ИЗМЕНЕНИЕ: Путь для страницы отчетов
    path('reports/', views.reports_view, name='reports'),
    path('info/', views.info_view, name='info'),
    
    path('add-record/', views.add_record, name='add_record'),
    path('toggle-status/', views.toggle_status, name='toggle_status'),
    path('update-date/', views.update_date, name='update_date'),
    
    path('get-record/', views.get_record, name='get_record'),
    path('edit-record/', views.edit_record, name='edit_record'),
    path('delete-record/', views.delete_record, name='delete_record'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
