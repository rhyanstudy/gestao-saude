from django.contrib import admin
from django.urls import path
from gestao import views

urlpatterns = [
    path('django-admin/', admin.site.urls),

    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/redirect/', views.dashboard_redirect, name='dashboard_redirect'),

    path('dashboard/user/', views.user_dashboard, name='user_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),

    path('submit/medication/', views.submit_medication, name='submit_medication'),
    path('submit/cmm/', views.submit_cmm_request, name='submit_cmm_request'),
    path('edit/cmm/<int:pk>/', views.edit_cmm_request, name='edit_cmm_request'),

    path('request/<str:request_type>/<int:pk>/', views.request_detail, name='request_detail'),
]
