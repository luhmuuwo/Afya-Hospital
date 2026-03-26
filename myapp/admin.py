from django.contrib import admin
from .models import Patient, Doctor, Appointment, Bill, PharmacyItem, PharmacyIssue, LabTest, MPesaTransaction

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'first_name', 'last_name', 'email', 'phone_number', 'date_registered')
    list_filter = ('gender', 'date_registered')
    search_fields = ('patient_id', 'first_name', 'last_name', 'email')
    readonly_fields = ('date_registered',)
    fieldsets = (
        ('Personal Information', {
            'fields': ('patient_id', 'first_name', 'last_name', 'gender', 'date_of_birth')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone_number', 'address')
        }),
        ('Medical Information', {
            'fields': ('medical_history',)
        }),
        ('Timestamps', {
            'fields': ('date_registered',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('doctor_id', 'first_name', 'last_name', 'email', 'specialization', 'department')
    list_filter = ('department',)
    search_fields = ('doctor_id', 'first_name', 'last_name', 'email', 'specialization')
    readonly_fields = ('date_added',)
    fieldsets = (
        ('Personal Information', {
            'fields': ('doctor_id', 'first_name', 'last_name', 'email', 'phone_number')
        }),
        ('Professional Info', {
            'fields': ('specialization', 'department', 'schedule')
        }),
        ('Timestamps', {
            'fields': ('date_added',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'date', 'time', 'status', 'diagnosis', 'created_at')
    list_filter = ('status', 'date', 'doctor')
    search_fields = ('patient__first_name', 'patient__last_name', 'doctor__first_name', 'doctor__last_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('patient', 'appointment', 'total_amount', 'payment_status', 'payment_method', 'mpesa_status', 'created_at')
    list_filter = ('payment_status', 'payment_method', 'mpesa_status', 'created_at')
    search_fields = ('patient__first_name', 'patient__last_name', 'mpesa_payment', 'mpesa_receipt_number')
    readonly_fields = ('created_at', 'updated_at', 'mpesa_timestamp')
    fieldsets = (
        ('Bill Information', {
            'fields': ('patient', 'appointment', 'services', 'total_amount')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status')
        }),
        ('M-Pesa Payment Details', {
            'fields': ('mpesa_payment', 'mpesa_transaction_id', 'mpesa_receipt_number', 'mpesa_status', 'mpesa_timestamp'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PharmacyItem)
class PharmacyItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'price', 'expiry_date', 'is_expired', 'is_expiring_soon')
    list_filter = ('expiry_date',)
    search_fields = ('name', 'batch_number')
    readonly_fields = ('date_added', 'updated_at')
    fieldsets = (
        ('Pharmacy Item Details', {
            'fields': ('name', 'quantity', 'price', 'expiry_date', 'batch_number')
        }),
        ('Timestamps', {
            'fields': ('date_added', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PharmacyIssue)
class PharmacyIssueAdmin(admin.ModelAdmin):
    list_display = ('patient', 'pharmacy_item', 'quantity_issued', 'issued_by', 'issued_date')
    list_filter = ('issued_date', 'issued_by')
    search_fields = ('patient__first_name', 'patient__last_name', 'pharmacy_item__name')
    readonly_fields = ('issued_date',)

@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ('patient', 'test_name', 'status', 'test_date', 'requested_by')
    list_filter = ('status', 'test_date', 'requested_by')
    search_fields = ('patient__first_name', 'patient__last_name', 'test_name')
    readonly_fields = ('test_date', 'completed_date')


@admin.register(MPesaTransaction)
class MPesaTransactionAdmin(admin.ModelAdmin):
    list_display = ('bill', 'patient_phone', 'amount', 'status', 'mpesa_receipt', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('patient_phone', 'transaction_id', 'mpesa_receipt', 'bill__patient__first_name', 'bill__patient__last_name')
    readonly_fields = ('transaction_id', 'created_at', 'completed_at', 'response_data')
    fieldsets = (
        ('Transaction Information', {
            'fields': ('bill', 'transaction_id', 'patient_phone', 'amount', 'status')
        }),
        ('M-Pesa Details', {
            'fields': ('mpesa_receipt', 'response_data')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )