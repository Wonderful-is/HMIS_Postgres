from django.urls import path
from . import views

from .views import download_patient_pdf

urlpatterns = [
    # Core URLs
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    #--------------------------------------------------------------------------------------------
    #--------------------------------------------------------------------------------------------


    # Admin URLs
    path('base_admin/', views.base_admin, name='base_admin'),



    #---------------------------------------------------------------------------------------------
    #---------------------------------------------------------------------------------------------
    
    # Staff Management URLs
    path('staffmanagement/', views.staff_list, name='staffmanagement'),
    path('register_staff/', views.register_staff, name='register_staff'),
    path('delete_staff/<int:staff_id>/', views.delete_staff, name='delete_staff'),
    path('edit-staff/<int:staff_id>/', views.edit_staff, name='edit_staff'),
    
    #Role managment

    path('rolemanagement/', views.role_list, name='rolemanagement'),
    path('delete_role/<int:role_id>/', views.delete_role, name='delete_role'),
    path('register_role/', views.register_role, name='register_role'),
    path('edit-role/<int:role_id>/', views.edit_role, name='edit_role'),

   #Department Managment

 
    path('departmentmanagement/', views.department_list, name='departmentmanagement'),
    path('register_department/', views.register_department, name='register_department'),
    path('edit-department/<int:department_id>/', views.edit_department, name='edit_department'),
    path('delete-department/<int:department_id>/', views.delete_department, name='delete_department'),


    #---------------------------------------------------------------------------------------------------------
    #---------------------------------------------------------------------------------------------------------

     # Admin URLs

    path('download_patient_excel/', views.download_patient_excel, name='download_patient_excel'),
    path('download_patient_pdf/<int:patient_id>/', views.download_patient_pdf, name='download_patient_pdf'),
  
   
    path('base_almoner/', views.base_almoner, name='base_almoner'),

    path('patientmanagement/', views.patient_list, name='patientmanagement'),
    path('register_new_patient/', views.new_patient_list, name='register_new_patient'),

    path('view-patient/<int:patient_id>/', views.view_patient, name='view_patient'),
    path('edit-patient/<int:patient_id>/', views.edit_patient, name='edit_patient'),

     # Other URL patterns...
    path('download-patient/<int:patient_id>/', views.download_patient_pdf, name='download_patient_pdf'),


#download view
    path('download-pdf/<int:patient_id>/', download_patient_pdf, name='download_patient_pdf'),

    path('download-patient-excel/', views.download_patient_excel, name='download_patient_excel'),
 

    #___________________________________________________________________________________________________________
    path('visitmanagement/', views.visit_list, name='visitmanagement'),
    path('visit/<int:visit_id>/', views.view_visit, name='view_visit'),
    path('register_patient_visit/', views.patient_visit_list, name='register_patient_visit'),

    path('search_patient/', views.search_patient, name='search_patient'),
    path('register_patient_visit/<int:patient_id>/', views.register_patient_visit, name='register_patient_visit'),

    path('edit-visit/<int:visit_id>/', views.edit_visit, name='edit_visit'),




#__________{% url 'register_patient_visit' %}______________________________________________________________________________________
    path('appointmentmanagement/', views.appointment_list, name = 'appointmentmanagement'),

    path('register_patient_appointment/', views.register_patient_appointment, name='register_patient_appointment'),

    path('appointment/<int:appointment_id>/', views.view_appointment, name='view_appointment'),

    #path('search_patient_appointment/', views.search_patient_appointment, name='search_patient_appointment'),

    path('search_patient_appointment/', views.search_patient_appointment, name='search_patient_appointment'),
    path('register_patient_appointment/<int:patient_id>/', views.register_patient_appointment, name='register_patient_appointment'),

    path('edit-appointment/<int:appointment_id>/', views.edit_appointment, name='edit_appointment'),



  
  

   #_____________________________________________________________________________________________________________
   
    # Nurse URLs
    path('base_nurse/', views.base_nurse, name='base_nurse'),

    path('patientscreeningmanagement/', views.patient_screening_list, name='patientscreeningmanagement'),

    path('search_patient_screened/', views.search_patient_screened, name='search_patient_screened'),
    path('register_patient_screened/', views.register_patient_screened, name='register_patient_screened'),

    path('register_patient_screened/<int:patient_id>/', views.register_patient_screened, name='register_patient_screened'),
    path('patientscrenningmanagement/', views.patient_screening_list, name='patientscrenningmanagement'),
    path('edit_patient_screened/<int:screening_id>/', views.edit_patient_screened, name='edit_patient_screened'),

    path('view_patient_screened/<int:patient_id>/', views.view_patient_screened, name='view_patient_screened'),

   

#________________________________________________________________________________________________________________________

    path('base_doctor/', views.base_doctor, name='base_doctor'),

    path('patient_consultation_management/', views.Consultation, name='patient_consultation_management'),
    path('register_patient_consulted/<int:patient_id>/', views.register_patient_consulted, name='register_patient_consulted'),
    
    path('register_patient_consulted/', views.register_patient_consulted, name='register_patient_consulted'),
    path('search_patient_consulted/', views.search_patient_consulted, name='search_patient_consulted'),
    path('edit_patient_consulted/<int:id>/', views.edit_patient_consulted, name='edit_patient_consulted'),

     path('view_patient_consultation/<int:id>/', views.view_patient_consultation, name='view_patient_consultation'),



    
# =========================

    
   
]

