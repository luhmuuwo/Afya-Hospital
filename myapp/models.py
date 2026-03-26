from django.db import models
from django.utils import timezone

class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    patient_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    address = models.TextField()
    date_registered = models.DateTimeField(auto_now_add=True)
    medical_history = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.patient_id})"
    
    class Meta:
        ordering = ['-date_registered']


class Doctor(models.Model):
    DEPARTMENT_CHOICES = [
        ('cardiology', 'Cardiology'),
        ('neurology', 'Neurology'),
        ('pediatrics', 'Pediatrics'),
        ('orthopedics', 'Orthopedics'),
        ('general', 'General Medicine'),
        # add other departments as needed
    ]

    doctor_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    specialization = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    schedule = models.TextField(blank=True, null=True, help_text="Optional scheduling notes or timeslots")
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name} ({self.doctor_id})"

    class Meta:
        ordering = ['last_name', 'first_name']


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    diagnosis = models.TextField(blank=True, null=True)
    prescribed_drugs = models.TextField(blank=True, null=True, help_text="List of prescribed drugs with dosages")
    prescription = models.FileField(upload_to='prescriptions/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.date} {self.time.strftime('%H:%M')} - {self.patient} with {self.doctor}"

    class Meta:
        ordering = ['-date', '-time']


class Bill(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Overdue', 'Overdue'),
        ('Cancelled', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('Insurance', 'Insurance'),
        ('Bank Transfer', 'Bank Transfer'),
        ('M-Pesa', 'M-Pesa'),
        ('Other', 'Other'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, null=True, blank=True)
    services = models.TextField(help_text="List of services provided")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    
    # M-Pesa Payment Fields
    mpesa_payment = models.CharField(max_length=15, blank=True, null=True, help_text="M-Pesa phone number for payment (format: 254XXXXXXXXX)")
    mpesa_transaction_id = models.CharField(max_length=100, blank=True, null=True, help_text="M-Pesa transaction ID")
    mpesa_receipt_number = models.CharField(max_length=100, blank=True, null=True, help_text="M-Pesa receipt number")
    mpesa_status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Success', 'Success'), ('Failed', 'Failed')], blank=True, null=True, help_text="M-Pesa payment status")
    mpesa_timestamp = models.DateTimeField(blank=True, null=True, help_text="M-Pesa payment completion time")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bill for {self.patient} - ${self.total_amount}"

    class Meta:
        ordering = ['-created_at']


class PharmacyItem(models.Model):
    name = models.CharField(max_length=100, unique=True)
    quantity = models.PositiveIntegerField(help_text="Current stock quantity")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per unit")
    expiry_date = models.DateField()
    batch_number = models.CharField(max_length=50, blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (Qty: {self.quantity})"

    def is_expired(self):
        return self.expiry_date < timezone.now().date()

    def is_expiring_soon(self):
        # Expiring within 30 days
        return (self.expiry_date - timezone.now().date()).days <= 30 and not self.is_expired()

    class Meta:
        ordering = ['name']


class PharmacyIssue(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    pharmacy_item = models.ForeignKey(PharmacyItem, on_delete=models.CASCADE)
    quantity_issued = models.PositiveIntegerField()
    issued_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    issued_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.pharmacy_item.name} issued to {self.patient} on {self.issued_date.date()}"

    class Meta:
        ordering = ['-issued_date']

class LabTest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    test_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True, help_text="Optional test description or notes")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    results = models.FileField(upload_to='lab_results/', blank=True, null=True)
    test_date = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    requested_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.test_name} for {self.patient}"

    class Meta:
        ordering = ['-test_date']


class MPesaTransaction(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    ]

    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='mpesa_transactions')
    patient_phone = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    mpesa_receipt = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    response_data = models.TextField(blank=True, null=True, help_text="Raw M-Pesa response data")

    def __str__(self):
        return f"M-Pesa Transaction {self.transaction_id} - {self.bill.patient}"

    class Meta:
        ordering = ['-created_at']