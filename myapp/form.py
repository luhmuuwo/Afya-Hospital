from django import forms

from .models import Appointment, Doctor, Patient, Bill, PharmacyItem, PharmacyIssue, LabTest


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = (
            'patient_id',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'gender',
            'date_of_birth',
            'address',
            'medical_history',
        )
        widgets = {
            'patient_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter patient ID'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter address', 'rows': 3}),
            'medical_history': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter medical history (optional)', 'rows': 3}),
        }


class PatientSearchForm(forms.Form):
    search_query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Search by name, patient ID, or email',
            }
        ),
    )


class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = (
            'doctor_id',
            'first_name',
            'last_name',
            'email',
            'specialization',
            'phone_number',
            'department',
            'schedule',
        )
        widgets = {
            'doctor_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter doctor ID'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter specialization'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'schedule': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter schedule (optional)', 'rows': 3}),
        }


def _default_time_choices():
    # Standard 30 minute slots from 09:00 to 17:00
    slots = []
    hour = 9
    minute = 0
    while hour < 17:
        slots.append((f"{hour:02d}:{minute:02d}", f"{hour:02d}:{minute:02d}"))
        minute += 30
        if minute == 60:
            minute = 0
            hour += 1
    return slots


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ('patient', 'doctor', 'date', 'time')
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the choices for time since it's now free input

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')

        if doctor and date and time:
            # Check if this time slot is already booked for this doctor on this date
            existing_appointment = Appointment.objects.filter(
                doctor=doctor,
                date=date,
                time=time,
                status__in=['Pending', 'Completed']  # Exclude Cancelled
            ).exclude(pk=self.instance.pk if self.instance else None)

            if existing_appointment.exists():
                raise forms.ValidationError("This time slot is already booked for the selected doctor and date.")

        return cleaned_data


class LabTestForm(forms.ModelForm):
    class Meta:
        model = LabTest
        fields = ('patient', 'test_name', 'description', 'status', 'results', 'requested_by')
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'test_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter test name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional test description'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'results': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'requested_by': forms.Select(attrs={'class': 'form-control'}),
        }

class AppointmentUpdateForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ('status', 'diagnosis', 'prescribed_drugs', 'prescription')
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter diagnosis notes'}),
            'prescribed_drugs': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter prescribed drugs with dosages (e.g., Drug A: 500mg twice daily)'}),
            'prescription': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ('patient', 'appointment', 'services', 'total_amount', 'payment_method', 'payment_status', 'mpesa_payment')
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'appointment': forms.Select(attrs={'class': 'form-control'}),
            'services': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'List services provided'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'payment_status': forms.Select(attrs={'class': 'form-control'}),
            'mpesa_payment': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter M-Pesa phone number (254XXXXXXXXX)'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        mpesa_payment = cleaned_data.get('mpesa_payment')
        
        if payment_method == 'M-Pesa' and not mpesa_payment:
            raise forms.ValidationError("M-Pesa phone number is required when payment method is M-Pesa.")
        
        return cleaned_data


class PharmacyItemForm(forms.ModelForm):
    class Meta:
        model = PharmacyItem
        fields = ('name', 'quantity', 'price', 'expiry_date', 'batch_number')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter pharmacy item name'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter price per unit'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter batch number (optional)'}),
        }


class PharmacyIssueForm(forms.ModelForm):
    class Meta:
        model = PharmacyIssue
        fields = ('patient', 'pharmacy_item', 'quantity_issued', 'issued_by', 'notes')
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'pharmacy_item': forms.Select(attrs={'class': 'form-control'}),
            'quantity_issued': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity to issue'}),
            'issued_by': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes (optional)'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        pharmacy_item = cleaned_data.get('pharmacy_item')
        quantity_issued = cleaned_data.get('quantity_issued')

        if pharmacy_item and quantity_issued:
            if quantity_issued > pharmacy_item.quantity:
                raise forms.ValidationError("Cannot issue more than available stock.")

        return cleaned_data
