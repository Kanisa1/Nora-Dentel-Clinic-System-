from django.urls import path
from . import views_doctor
from .views_doctor_enhanced import (
    doctor_dashboard_enhanced,
    medical_record_form,
    billing_sheet,
    delete_billing_item,
    generate_medical_certificate,
    transfer_patient,
    create_followup_appointment,
    send_to_cashier,
    my_patients_today,
    waiting_queue,
    in_consultation_list,
    medical_records_list,
    my_statistics,
    prescriptions_list,
    print_prescription,
    medical_certificates_list,
    patient_transfers_list,
    doctor_profile,
    doctor_update_profile,
    doctor_update_profile_picture,
)

urlpatterns = [
    # Original login
    path('login/', views_doctor.doctor_login, name='doctor-login'),
    
    # Enhanced Doctor Dashboard (default)
    path('enhanced/', doctor_dashboard_enhanced, name='doctor_dashboard_enhanced'),
    path('dashboard/', doctor_dashboard_enhanced, name='doctor-dashboard'),  # Redirect old URL
    path('', doctor_dashboard_enhanced, name='doctor_home'),  # Default route
    
    # Medical Records
    path('medical-record/<int:visit_id>/', medical_record_form, name='medical_record_form'),
    
    # Billing
    path('billing/<int:visit_id>/', billing_sheet, name='billing_sheet'),
    path('billing/delete/<int:item_id>/', delete_billing_item, name='delete_billing_item'),
    path('visit/<int:visit_id>/followup/', create_followup_appointment, name='doctor-create-appointment'),
    
    # Certificates
    path('certificate/<int:visit_id>/', generate_medical_certificate, name='generate_medical_certificate'),
    
    # Patient Transfer
    path('transfer/<int:visit_id>/', transfer_patient, name='transfer_patient'),
    
    # Send to Cashier
    path('send-to-cashier/<int:visit_id>/', send_to_cashier, name='send_to_cashier'),
    
    # New functional navbar items
    path('my-patients-today/', my_patients_today, name='my_patients_today'),
    path('waiting-queue/', waiting_queue, name='waiting_queue'),
    path('in-consultation/', in_consultation_list, name='in_consultation_list'),
    path('medical-records/', medical_records_list, name='medical_records_list'),
    path('my-statistics/', my_statistics, name='my_statistics'),
    path('prescriptions/', prescriptions_list, name='prescriptions_list'),    path('prescriptions/<int:prescription_id>/print/', print_prescription, name='print_prescription'),    path('certificates/', medical_certificates_list, name='medical_certificates_list'),
    path('transfers/', patient_transfers_list, name='patient_transfers_list'),

    # Profile management
    path('profile/', doctor_profile, name='doctor_profile'),
    path('profile/update/', doctor_update_profile, name='doctor_update_profile'),
    path('profile/picture/', doctor_update_profile_picture, name='doctor_update_profile_picture'),
    
    # Original URLs (kept for compatibility)
    path('visit/<int:visit_id>/', views_doctor.visit_detail, name='doctor-visit-detail'),
    path('visit/<int:visit_id>/save-triage/', views_doctor.save_triage, name='doctor-save-triage'),
    path('visit/<int:visit_id>/add-act/', views_doctor.add_act, name='doctor-add-act'),
    path('visit/<int:visit_id>/prescription/', views_doctor.save_prescription, name='doctor-save-prescription'),
    path('prescription/<int:prescription_id>/delete/', views_doctor.delete_prescription, name='doctor-delete-prescription'),
    path('billing-item/<int:item_id>/delete/', views_doctor.delete_billing_item, name='doctor-delete-billing-item'),
    path('visit/<int:visit_id>/close/', views_doctor.close_visit, name='doctor-close-visit'),
]
