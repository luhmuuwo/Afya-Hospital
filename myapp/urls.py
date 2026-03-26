from django.urls import path
from . import views

app_name = 'myapp'

urlpatterns = [
    # homepage
    path('', views.home, name='homepage'),

    # Management Sections
    path('patients-management/', views.patients_management, name='patients_management'),
    path('doctors-management/', views.doctors_management, name='doctors_management'),
    path('bills-management/', views.bills_management, name='bills_management'),
    path('pharmacy-management/', views.pharmacy_management, name='pharmacy_management'),
    path('lab-tests-management/', views.lab_tests_management, name='lab_tests_management'),

    # patient routes
    path('patients/',views.patient_list, name='patient_list'),
    path('patients/register/',views.register_patient, name='register_patient'),
    path('patients/<int:pk>/',views.patient_detail, name='patient_detail'),
    path('patients/<int:pk>/update/',views.update_patient, name='update_patient'),
    path('patients/<int:pk>/delete/',views.delete_patient, name='delete_patient'),
    path('patients/search/',views.search_patient, name='search_patient'),
    
    # doctor routes
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('doctors/add/', views.register_doctor, name='register_doctor'),
    path('doctor/<int:pk>/', views.doctor_detail, name='doctor_detail'),
    path('doctor/<int:pk>/update/', views.update_doctor, name='update_doctor'),
    path('doctor/<int:pk>/delete/', views.delete_doctor, name='delete_doctor'),

    # appointment routes
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/book/', views.book_appointment, name='book_appointment'),
    path('appointments/<int:pk>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('appointments/<int:pk>/edit/', views.edit_appointment, name='edit_appointment'),
    path('doctor/<int:pk>/appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('reports/', views.medical_reports, name='medical_reports'),

    # billing routes
    path('bills/', views.bill_list, name='bill_list'),
    path('bills/create/', views.create_bill, name='create_bill'),
    path('bills/<int:pk>/', views.bill_detail, name='bill_detail'),
    path('bills/<int:pk>/update/', views.update_bill, name='update_bill'),
    path('bills/<int:pk>/delete/', views.delete_bill, name='delete_bill'),

    # M-Pesa payment routes
    path('bills/<int:bill_id>/pay-mpesa/',views.initiate_mpesa_payment, name='initiate_mpesa_payment'),
    path('mpesa/payment-status/<int:transaction_id>/',views.mpesa_payment_status, name='mpesa_payment_status'),
    path('mpesa/callback/',views.process_mpesa_callback, name='mpesa_callback'),
    path('bills/<int:bill_id>/simulate-payment/',views.simulate_mpesa_payment, name='simulate_mpesa_payment'),

    # pharmacy routes
    path('pharmacy/', views.pharmacy_item_list, name='pharmacy_item_list'),
    path('pharmacy/add/', views.add_pharmacy_item, name='add_pharmacy_item'),
    path('pharmacy/<int:pk>/', views.pharmacy_item_detail, name='pharmacy_item_detail'),
    path('pharmacy/<int:pk>/update/', views.update_pharmacy_item, name='update_pharmacy_item'),
    path('pharmacy/<int:pk>/delete/', views.delete_pharmacy_item, name='delete_pharmacy_item'),
    path('pharmacy/issue/', views.issue_pharmacy_item, name='issue_pharmacy_item'),
    path('pharmacy/alerts/', views.pharmacy_alerts, name='pharmacy_alerts'),

    # lab test routes
    path('lab-tests/', views.lab_test_list, name='lab_test_list'),
    path('lab-tests/add/', views.add_lab_test, name='add_lab_test'),
    path('lab-tests/<int:pk>/', views.lab_test_detail, name='lab_test_detail'),
    path('lab-tests/<int:pk>/update/', views.update_lab_test, name='update_lab_test'),
    path('lab-tests/<int:pk>/delete/', views.delete_lab_test, name='delete_lab_test'),

    # STKPush payment routes (for M-Pesa integration)
    path('token/', views.home, name='token'),
    path('stk/', views.bill_list, name='stk'),
    path('pay/', views.bill_list, name='pay'),
    
]
