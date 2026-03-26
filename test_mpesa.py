#!/usr/bin/env python
"""
Test script for M-Pesa payment functionality
"""
import os
import sys
import django

# Setup Django environment
sys.path.append('/home/emobilis/Desktop/hospman/groupproject')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_management.settings')
django.setup()

from myapp.models import Patient, Bill, MPesaTransaction
from django.utils import timezone
import uuid

def test_mpesa_payment():
    """Test M-Pesa payment simulation"""
    print("Testing M-Pesa Payment Functionality")
    print("=" * 50)

    # Create a test patient if none exists
    patient, created = Patient.objects.get_or_create(
        first_name='Test',
        last_name='Patient',
        defaults={
            'patient_id': 'TEST001',
            'date_of_birth': '1990-01-01',
            'gender': 'M',
            'phone_number': '0712345678',
            'email': 'test@example.com',
            'address': 'Test Address'
        }
    )
    print(f"Patient: {'Created' if created else 'Found'} - {patient.first_name} {patient.last_name}")

    # Create a test bill if none exists
    bill, created = Bill.objects.get_or_create(
        patient=patient,
        defaults={
            'total_amount': 1500.00,
            'payment_status': 'Pending',
            'payment_method': 'Cash',
            'services': 'Test bill for M-Pesa payment'
        }
    )
    print(f"Bill: {'Created' if created else 'Found'} - ID: {bill.id}, Amount: KES {bill.total_amount}")

    # Simulate M-Pesa payment
    print("\nSimulating M-Pesa Payment...")
    transaction = MPesaTransaction.objects.create(
        bill=bill,
        patient_phone='254712345678',
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

    print(f"Transaction created: {transaction.transaction_id}")
    print(f"Receipt: {transaction.mpesa_receipt}")
    print(f"Bill status updated to: {bill.payment_status}")
    print(f"Payment method: {bill.payment_method}")

    # Verify the transaction
    transactions = MPesaTransaction.objects.filter(bill=bill)
    print(f"\nTotal transactions for bill {bill.id}: {transactions.count()}")

    for tx in transactions:
        print(f"- Transaction {tx.id}: {tx.status} - {tx.amount} KES")

    print("\n✅ M-Pesa Payment Test Completed Successfully!")

if __name__ == '__main__':
    test_mpesa_payment()