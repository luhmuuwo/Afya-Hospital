import os
import json
import base64
import requests
import uuid
from datetime import datetime, date, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import Patient, Doctor, Appointment, Bill, PharmacyItem, PharmacyIssue, LabTest, MPesaTransaction
from .form import PatientForm, PatientSearchForm, DoctorForm, AppointmentForm, AppointmentUpdateForm, BillForm, PharmacyItemForm, PharmacyIssueForm, LabTestForm
from .credentials import MpesaC2bCredential, MpesaAccessToken, LipanaMpesaPpassword


def get_mpesa_access_token():
    """Get access token from safaricom oauth API."""
    # First check explicit environment override for easier deployment
    env_token = os.environ.get('MPESA_ACCESS_TOKEN')
    if env_token:
        return env_token

    if MpesaAccessToken:
        token = MpesaAccessToken.fetch()
        if token:
            return token

    url = MpesaC2bCredential.api_URL
    auth = (MpesaC2bCredential.consumer_key, MpesaC2bCredential.consumer_secret)
    response = requests.get(url, auth=auth)
    response.raise_for_status()
    data = response.json()
    return data.get('access_token')


def get_lipa_na_mpesa_password(timestamp=None):
    """Generate base64 password for STKPush request."""
    timestamp = timestamp or datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = LipanaMpesaPpassword.business_short_code + LipanaMpesaPpassword.passkey + timestamp
    encoded = base64.b64encode(data_to_encode.encode('utf-8')).decode('utf-8')
    return encoded, timestamp


def initiate_stk_push_request(phone, amount, bill_ref, checkout_callback_url):
    """Call Safaricom STKPush processrequest endpoint."""
    token = get_mpesa_access_token()
    password, timestamp = get_lipa_na_mpesa_password()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    payload = {
        'businessShortCode': MpesaC2bCredential.business_short_code,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': float(amount),
        'PartyA': phone,
        'PartyB': MpesaC2bCredential.business_short_code,
        'PhoneNumber': phone,
        'CallBackURL': checkout_callback_url,
        'AccountReference': bill_ref,
        'TransactionDesc': f'M-Pesa payment for bill {bill_ref}',
    }

    stk_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    response = requests.post(stk_url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def home(request):
    # Dashboard stats
    patient_count = Patient.objects.count()
    doctor_count = Doctor.objects.count()
    appointment_count = Appointment.objects.count()
    report_count = Appointment.objects.filter(
        Q(diagnosis__isnull=False) | Q(prescription__isnull=False)
    ).count()
    bill_count = Bill.objects.count()
    pharmacy_item_count = PharmacyItem.objects.count()
    low_stock_count = PharmacyItem.objects.filter(quantity__lte=10).count()
    expiring_soon_count = PharmacyItem.objects.filter(expiry_date__lte=date.today() + timedelta(days=30)).count()
    lab_test_count = LabTest.objects.count()
    pending_tests_count = LabTest.objects.filter(status='Pending').count()

    context = {
        'patient_count': patient_count,
        'doctor_count': doctor_count,
        'appointment_count': appointment_count,
        'report_count': report_count,
        'bill_count': bill_count,
        'pharmacy_item_count': pharmacy_item_count,
        'low_stock_count': low_stock_count,
        'expiring_soon_count': expiring_soon_count,
        'lab_test_count': lab_test_count,
        'pending_tests_count': pending_tests_count,
    }
    return render(request, 'homepage.html', context)

# Landing page / Patient list
def patient_list(request):
    patients = Patient.objects.all()
    search_form = PatientSearchForm(request.GET)
    
    if search_form.is_valid() and search_form.cleaned_data['search_query']:
        query = search_form.cleaned_data['search_query']
        patients = patients.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(patient_id__icontains=query) |
            Q(email__icontains=query)
        )
    
    context = {
        'patients': patients,
        'search_form': search_form,
    }
    return render(request, 'patient_list.html', context)

# Register new patient
def register_patient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient registered successfully!')
            return redirect('myapp:patient_list')
    else:
        form = PatientForm()
    
    context = {'form': form, 'title': 'Register New Patient'}
    return render(request, 'patient_form.html', context)

# View patient details
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    appointments = Appointment.objects.filter(patient=patient).order_by('-date', '-time')
    context = {
        'patient': patient,
        'appointments': appointments,
    }
    return render(request, 'patient_detail.html', context)

# Update patient details
def update_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient details updated successfully!')
            return redirect('myapp:patient_detail', pk=patient.pk)
    else:
        form = PatientForm(instance=patient)
    
    context = {'form': form, 'patient': patient, 'title': 'Update Patient Details'}
    return render(request, 'patient_form.html', context)

# Delete patient
def delete_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    
    if request.method == 'POST':
        patient.delete()
        messages.success(request, 'Patient deleted successfully!')
        return redirect('myapp:patient_list')
    
    context = {'patient': patient}
    return render(request, 'patient_confirm_delete.html', context)

# Search patients
def search_patient(request):
    search_form = PatientSearchForm(request.GET)
    patients = []
    
    if search_form.is_valid() and search_form.cleaned_data['search_query']:
        query = search_form.cleaned_data['search_query']
        patients = Patient.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(patient_id__icontains=query) |
            Q(email__icontains=query)
        )
    
    context = {
        'patients': patients,
        'search_form': search_form,
    }
    return render(request, 'patient_search.html', context)


# --- doctor views ---

def doctor_list(request):
    doctors = Doctor.objects.all()
    context = {'doctors': doctors}
    return render(request, 'doctor_list.html', context)


def register_doctor(request):
    if request.method == 'POST':
        form = DoctorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Doctor added successfully!')
            return redirect('myapp:doctor_list')
    else:
        form = DoctorForm()
    
    context = {'form': form, 'title': 'Add New Doctor'}
    return render(request, 'doctor_form.html', context)


def doctor_detail(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    appointments = Appointment.objects.filter(doctor=doctor).order_by('date', 'time')
    context = {
        'doctor': doctor,
        'appointments': appointments,
    }
    return render(request, 'doctor_detail.html', context)


def update_doctor(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == 'POST':
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Doctor details updated successfully!')
            return redirect('myapp:doctor_detail', pk=doctor.pk)
    else:
        form = DoctorForm(instance=doctor)
    
    context = {'form': form, 'doctor': doctor, 'title': 'Update Doctor Details'}
    return render(request, 'doctor_form.html', context)


def delete_doctor(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == 'POST':
        doctor.delete()
        messages.success(request, 'Doctor deleted successfully!')
        return redirect('myapp:doctor_list')
    context = {'doctor': doctor}
    return render(request, 'doctor_confirm_delete.html', context)


# --- appointment views ---


def _generate_timeslots(start_hour=9, end_hour=17, step_minutes=30):
    slots = []
    current = datetime.combine(date.today(), datetime.min.time()).replace(hour=start_hour, minute=0)
    end = current.replace(hour=end_hour, minute=0)
    while current < end:
        slots.append(current.time())
        current += timedelta(minutes=step_minutes)
    return slots


def _format_timeslot(t):
    return t.strftime('%H:%M')


def _get_available_timeslots(doctor, date_obj):
    # Exclude Cancelled appointments
    booked_times = Appointment.objects.filter(
        doctor=doctor,
        date=date_obj,
    ).exclude(status='Cancelled').values_list('time', flat=True)

    all_slots = _generate_timeslots()
    available = [t for t in all_slots if t not in booked_times]

    return [(t.strftime('%H:%M'), t.strftime('%H:%M')) for t in available]


def appointment_list(request):
    appointments = Appointment.objects.select_related('patient', 'doctor').order_by('-date', '-time')
    context = {'appointments': appointments}
    return render(request, 'appointment_list.html', context)


def book_appointment(request):
    doctor_id = request.GET.get('doctor') or request.POST.get('doctor')
    patient_id = request.GET.get('patient') or request.POST.get('patient')
    date_str = request.GET.get('date') or request.POST.get('date')

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.status = 'Pending'
            appointment.save()

            messages.success(request, 'Appointment booked successfully!')
            return redirect('myapp:appointment_list')
    else:
        initial = {}
        if doctor_id:
            initial['doctor'] = doctor_id
        if patient_id:
            initial['patient'] = patient_id
        if date_str:
            initial['date'] = date_str
        form = AppointmentForm(initial=initial)

    context = {
        'form': form,
    }
    return render(request, 'appointment_form.html', context)


def doctor_appointments(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    appointments = Appointment.objects.filter(doctor=doctor).order_by('-date', '-time')
    context = {
        'doctor': doctor,
        'appointments': appointments,
    }
    return render(request, 'doctor_appointments.html', context)


def cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        appointment.status = 'Cancelled'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
        return redirect('myapp:appointment_list')
    return render(request, 'appointment_confirm_cancel.html', {'appointment': appointment})


def edit_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    if request.method == 'POST':
        form = AppointmentUpdateForm(request.POST, request.FILES, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appointment updated successfully.')
            return redirect('myapp:appointment_list')
    else:
        form = AppointmentUpdateForm(instance=appointment)

    context = {'form': form, 'appointment': appointment}
    return render(request, 'appointment_edit.html', context)


def medical_reports(request):
    # Show appointments with any medical information (diagnosis or prescription)
    reports = Appointment.objects.select_related('patient', 'doctor').filter(
        Q(diagnosis__isnull=False) | Q(prescription__isnull=False)
    ).order_by('-date', '-time')

    context = {
        'reports': reports,
    }
    return render(request, 'medical_reports.html', context)


# --- billing views ---

def bill_list(request):
    bills = Bill.objects.select_related('patient', 'appointment').order_by('-created_at')
    context = {'bills': bills}
    return render(request, 'bill_list.html', context)


def create_bill(request):
    if request.method == 'POST':
        form = BillForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bill created successfully!')
            return redirect('myapp:bill_list')
    else:
        form = BillForm()
    context = {'form': form, 'title': 'Create New Bill'}
    return render(request, 'bill_form.html', context)


def bill_detail(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    active_mpesa_transaction = bill.mpesa_transactions.filter(status__in=['Pending', 'Success']).order_by('-created_at').first()
    context = {
        'bill': bill,
        'active_mpesa_transaction': active_mpesa_transaction,
        'has_active_mpesa_transaction': active_mpesa_transaction is not None,
    }
    return render(request, 'bill_detail.html', context)


def update_bill(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if request.method == 'POST':
        form = BillForm(request.POST, instance=bill)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bill updated successfully!')
            return redirect('myapp:bill_detail', pk=bill.pk)
    else:
        form = BillForm(instance=bill)
    context = {'form': form, 'bill': bill, 'title': 'Update Bill'}
    return render(request, 'bill_form.html', context)


def delete_bill(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if request.method == 'POST':
        bill.delete()
        messages.success(request, 'Bill deleted successfully!')
        return redirect('myapp:bill_list')
    context = {'bill': bill}
    return render(request, 'bill_confirm_delete.html', context)


# --- pharmacy views ---

def pharmacy_item_list(request):
    pharmacy_items = PharmacyItem.objects.all()
    context = {'pharmacy_items': pharmacy_items}
    return render(request, 'pharmacy_item_list.html', context)


def add_pharmacy_item(request):
    if request.method == 'POST':
        form = PharmacyItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pharmacy item added successfully!')
            return redirect('myapp:pharmacy_item_list')
    else:
        form = PharmacyItemForm()
    context = {'form': form, 'title': 'Add New Pharmacy Item'}
    return render(request, 'pharmacy_item_form.html', context)


def pharmacy_item_detail(request, pk):
    pharmacy_item = get_object_or_404(PharmacyItem, pk=pk)
    issues = PharmacyIssue.objects.filter(pharmacy_item=pharmacy_item).order_by('-issued_date')
    context = {
        'pharmacy_item': pharmacy_item,
        'issues': issues,
    }
    return render(request, 'pharmacy_item_detail.html', context)


def update_pharmacy_item(request, pk):
    pharmacy_item = get_object_or_404(PharmacyItem, pk=pk)
    if request.method == 'POST':
        form = PharmacyItemForm(request.POST, instance=pharmacy_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pharmacy item updated successfully!')
            return redirect('myapp:pharmacy_item_detail', pk=pharmacy_item.pk)
    else:
        form = PharmacyItemForm(instance=pharmacy_item)
    context = {'form': form, 'pharmacy_item': pharmacy_item, 'title': 'Update Pharmacy Item'}
    return render(request, 'pharmacy_item_form.html', context)


def delete_pharmacy_item(request, pk):
    pharmacy_item = get_object_or_404(PharmacyItem, pk=pk)
    if request.method == 'POST':
        pharmacy_item.delete()
        messages.success(request, 'Pharmacy item deleted successfully!')
        return redirect('myapp:pharmacy_item_list')
    context = {'pharmacy_item': pharmacy_item}
    return render(request, 'pharmacy_item_confirm_delete.html', context)


def issue_pharmacy_item(request):
    if request.method == 'POST':
        form = PharmacyIssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            # Reduce stock
            pharmacy_item = issue.pharmacy_item
            pharmacy_item.quantity -= issue.quantity_issued
            pharmacy_item.save()
            issue.save()
            messages.success(request, 'Pharmacy item issued successfully!')
            return redirect('myapp:pharmacy_item_list')
    else:
        form = PharmacyIssueForm()
    context = {'form': form, 'title': 'Issue Pharmacy Item to Patient'}
    return render(request, 'pharmacy_issue_form.html', context)


def pharmacy_alerts(request):
    today = date.today()
    expiring_soon = PharmacyItem.objects.filter(expiry_date__lte=today + timedelta(days=30), expiry_date__gte=today)
    expired = PharmacyItem.objects.filter(expiry_date__lt=today)
    low_stock = PharmacyItem.objects.filter(quantity__lte=10)
    
    context = {
        'expiring_soon': expiring_soon,
        'expired': expired,
        'low_stock': low_stock,
    }
    return render(request, 'pharmacy_alerts.html', context)

# --- lab test views ---

def lab_test_list(request):
    lab_tests = LabTest.objects.select_related('patient', 'requested_by').order_by('-test_date')
    context = {'lab_tests': lab_tests}
    return render(request, 'lab_test_list.html', context)


def add_lab_test(request):
    if request.method == 'POST':
        form = LabTestForm(request.POST, request.FILES)
        if form.is_valid():
            lab_test = form.save(commit=False)
            if lab_test.status == 'Completed' and not lab_test.completed_date:
                lab_test.completed_date = timezone.now()
            lab_test.save()
            messages.success(request, 'Lab test added successfully!')
            return redirect('myapp:lab_test_list')
    else:
        form = LabTestForm()
    context = {'form': form, 'title': 'Add New Lab Test'}
    return render(request, 'lab_test_form.html', context)


def lab_test_detail(request, pk):
    lab_test = get_object_or_404(LabTest, pk=pk)
    context = {'lab_test': lab_test}
    return render(request, 'lab_test_detail.html', context)


def update_lab_test(request, pk):
    lab_test = get_object_or_404(LabTest, pk=pk)
    if request.method == 'POST':
        form = LabTestForm(request.POST, request.FILES, instance=lab_test)
        if form.is_valid():
            updated_test = form.save(commit=False)
            if updated_test.status == 'Completed' and not updated_test.completed_date:
                updated_test.completed_date = timezone.now()
            elif updated_test.status != 'Completed':
                updated_test.completed_date = None
            updated_test.save()
            messages.success(request, 'Lab test updated successfully!')
            return redirect('myapp:lab_test_detail', pk=lab_test.pk)
    else:
        form = LabTestForm(instance=lab_test)
    context = {'form': form, 'lab_test': lab_test, 'title': 'Update Lab Test'}
    return render(request, 'lab_test_form.html', context)


def delete_lab_test(request, pk):
    lab_test = get_object_or_404(LabTest, pk=pk)
    if request.method == 'POST':
        lab_test.delete()
        messages.success(request, 'Lab test deleted successfully!')
        return redirect('myapp:lab_test_list')
    context = {'lab_test': lab_test}
    return render(request, 'lab_test_confirm_delete.html', context)


# --- Management Section Views ---

def patients_management(request):
    """Patient Management Dashboard - shows patient list and quick actions"""
    patients = Patient.objects.all().order_by('-date_registered')
    patient_count = patients.count()
    context = {
        'patients': patients,
        'patient_count': patient_count,
        'title': 'Patient Management',
    }
    return render(request, 'patients_management.html', context)


def doctors_management(request):
    """Doctor Management Dashboard - shows doctor list and quick actions"""
    doctors = Doctor.objects.all()
    doctor_count = doctors.count()
    context = {
        'doctors': doctors,
        'doctor_count': doctor_count,
        'title': 'Doctor Management',
    }
    return render(request, 'doctors_management.html', context)


def bills_management(request):
    """Bills Management Dashboard - shows bills and payment options including M-Pesa"""
    bills = Bill.objects.select_related('patient').order_by('-created_at')
    bill_count = bills.count()
    pending_bills = bills.filter(payment_status='Pending').count()
    paid_bills = bills.filter(payment_status='Paid').count()
    context = {
        'bills': bills,
        'bill_count': bill_count,
        'pending_bills': pending_bills,
        'paid_bills': paid_bills,
        'title': 'Bills Management',
    }
    return render(request, 'bills_management.html', context)


def pharmacy_management(request):
    """Pharmacy Management Dashboard - shows pharmacy inventory"""
    pharmacy_items = PharmacyItem.objects.all()
    item_count = pharmacy_items.count()
    low_stock_count = pharmacy_items.filter(quantity__lte=10).count()
    expiring_soon_count = pharmacy_items.filter(expiry_date__lte=date.today() + timedelta(days=30)).count()
    context = {
        'pharmacy_items': pharmacy_items,
        'item_count': item_count,
        'low_stock_count': low_stock_count,
        'expiring_soon_count': expiring_soon_count,
        'title': 'Pharmacy Management',
    }
    return render(request, 'pharmacy_management.html', context)


def lab_tests_management(request):
    """Lab Tests Management Dashboard - shows lab tests"""
    lab_tests = LabTest.objects.select_related('patient', 'requested_by').order_by('-test_date')
    test_count = lab_tests.count()
    pending_count = lab_tests.filter(status='Pending').count()
    completed_count = lab_tests.filter(status='Completed').count()
    context = {
        'lab_tests': lab_tests,
        'test_count': test_count,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'title': 'Lab Tests Management',
    }
    return render(request, 'lab_tests_management.html', context)


# --- M-Pesa Payment Views ---

def initiate_mpesa_payment(request, bill_id):
    """Initiate M-Pesa payment for a bill using Daraja STK Push."""
    bill = get_object_or_404(Bill, pk=bill_id)

    if request.method == 'POST':
        phone = request.POST.get('phone') or bill.mpesa_payment
        phone = phone.strip() if phone else ''

        if not phone or len(phone) not in (10, 12, 13):
            messages.error(request, 'Valid phone number is required for M-Pesa payment. Format: 254XXXXXXXXX or 07XXXXXXXX')
            return redirect('myapp:bill_detail', pk=bill_id)

        if phone.startswith('0'):
            phone = '254' + phone[1:]

        bill.mpesa_payment = phone
        bill.payment_method = 'M-Pesa'
        bill.mpesa_status = 'Pending'
        bill.mpesa_transaction_id = None
        bill.save()

        try:
            amount = request.POST.get('amount') or bill.total_amount
            try:
                amount = float(amount)
            except (TypeError, ValueError):
                amount = float(bill.total_amount)

            callback_url = request.build_absolute_uri('/mpesa/callback/')
            response_data = initiate_stk_push_request(phone, amount, f'Bill-{bill.pk}', callback_url)

            checkout_id = response_data.get('CheckoutRequestID') or response_data.get('MerchantRequestID')
            if not checkout_id:
                raise ValueError('No CheckoutRequestID returned')

            transaction = MPesaTransaction.objects.create(
                bill=bill,
                patient_phone=phone,
                amount=bill.total_amount,
                transaction_id=checkout_id,
                status='Pending',
                response_data=json.dumps(response_data),
            )

            messages.success(request, 'M-Pesa STK Push initiated. Complete the payment on your phone.')
            return redirect('myapp:mpesa_payment_status', transaction_id=transaction.id)

        except Exception as exc:
            bill.mpesa_status = 'Failed'
            bill.save()
            messages.error(request, f'Failed to initiate M-Pesa payment: {str(exc)}')
            return redirect('myapp:bill_detail', pk=bill_id)

    context = {
        'bill': bill,
        'title': 'Pay with M-Pesa',
    }
    return render(request, 'mpesa_payment_form.html', context)


def mpesa_payment_status(request, transaction_id):
    """Show M-Pesa payment status"""
    from .models import MPesaTransaction
    
    transaction = get_object_or_404(MPesaTransaction, pk=transaction_id)
    
    context = {
        'transaction': transaction,
        'bill': transaction.bill,
        'title': 'M-Pesa Payment Status',
    }
    return render(request, 'mpesa_payment_status.html', context)


def process_mpesa_callback(request):
    """Process M-Pesa callback from Daraja API."""
    if request.method != 'POST':
        return render(request, 'mpesa_callback_response.html')

    try:
        body = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, AttributeError):
        return render(request, 'mpesa_callback_response.html')

    # Daraja callback has nested structure in Body -> stkCallback
    stk_callback = body.get('Body', {}).get('stkCallback', {})
    checkout_id = stk_callback.get('CheckoutRequestID')
    result_code = stk_callback.get('ResultCode')
    result_desc = stk_callback.get('ResultDesc')

    mpesa_receipt = ''
    mpesa_amount = None
    mpesa_phone = ''
    callback_data = stk_callback.get('CallbackMetadata', {}).get('Item', [])

    for item in callback_data:
        name = item.get('Name')
        value = item.get('Value')
        if name == 'MpesaReceiptNumber':
            mpesa_receipt = value
        elif name == 'Amount':
            mpesa_amount = value
        elif name == 'PhoneNumber':
            mpesa_phone = value

    try:
        transaction = MPesaTransaction.objects.get(transaction_id=checkout_id)
    except MPesaTransaction.DoesNotExist:
        return render(request, 'mpesa_callback_response.html')

    transaction.response_data = json.dumps(stk_callback)

    if str(result_code) == '0':
        transaction.status = 'Success'
        transaction.mpesa_receipt = mpesa_receipt
        transaction.completed_at = timezone.now()
        transaction.save()

        bill = transaction.bill
        bill.payment_status = 'Paid'
        bill.payment_method = 'M-Pesa'
        bill.mpesa_transaction_id = transaction.transaction_id
        bill.mpesa_receipt_number = mpesa_receipt
        bill.mpesa_status = 'Success'
        bill.mpesa_timestamp = transaction.completed_at
        bill.save()

    else:
        transaction.status = 'Failed'
        transaction.completed_at = timezone.now()
        transaction.save()

        bill = transaction.bill
        bill.mpesa_status = 'Failed'
        bill.payment_status = 'Pending'
        bill.mpesa_timestamp = timezone.now()
        bill.save()

    return render(request, 'mpesa_callback_response.html')


def simulate_mpesa_payment(request, bill_id):
    """Simulate successful M-Pesa payment for testing purposes"""
    from .models import MPesaTransaction
    from django.utils import timezone
    import uuid
    
    bill = get_object_or_404(Bill, pk=bill_id)
    
    if request.method == 'POST':
        # Create a simulated successful transaction
        transaction = MPesaTransaction.objects.create(
            bill=bill,
            patient_phone='254712345678',  # Test phone number
            amount=bill.total_amount,
            transaction_id=str(uuid.uuid4()),
            status='Success',
            mpesa_receipt=f'SIM{uuid.uuid4().hex[:8].upper()}',
            completed_at=timezone.now(),
            response_data='{"ResultCode": "0", "MpesaReceiptNumber": "SIM' + uuid.uuid4().hex[:8].upper() + '"}'
        )
        
        # Update bill payment status
        bill.payment_status = 'Paid'
        bill.payment_method = 'M-Pesa'
        bill.save()
        
        messages.success(request, f'Payment of KES {bill.total_amount} completed successfully via M-Pesa!')
        return redirect('myapp:bill_detail', pk=bill_id)
    
    # If not POST, redirect to bill detail
    return redirect('myapp:bill_detail', pk=bill_id)