from django.urls import path
from . import views

urlpatterns = [
    # Core URLs
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Admin URLs
    path('base_admin/', views.base_admin, name='base_admin'),
    
    # Staff Management URLs
    path('staffmanagement/', views.staff_list, name='staffmanagement'),
    path('register-staff/', views.register_staff, name='register_staff'),

    path('edit-staff/<int:staff_id>/', views.edit_staff, name='edit_staff'),
]