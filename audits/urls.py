from django.urls import path

from . import views

urlpatterns = [
    path('', views.manager_dashboard, name='manager_dashboard'),
    path('audits/<int:auditor_id>/', views.auditor_workspace, name='auditor_workspace'),
    path('audit/<str:audit_code>/', views.audit_detail, name='audit_detail'),
    path('form/<str:audit_code>/', views.audit_form, name='audit_form'),
    path('assign/', views.assign_task, name='assign_task'),  
]
