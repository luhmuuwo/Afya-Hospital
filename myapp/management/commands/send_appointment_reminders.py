from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from myapp.models import Appointment
from myapp.notifications import send_appointment_reminder
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send appointment reminders via email and SMS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Send reminders for appointments within this many hours (default: 24)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending',
        )

    def handle(self, *args, **options):
        hours_ahead = options['hours']
        dry_run = options['dry_run']

        # Calculate the target time range
        now = timezone.now()
        target_time_start = now + timedelta(hours=hours_ahead - 1)  # Start of the hour window
        target_time_end = now + timedelta(hours=hours_ahead)  # End of the hour window

        # Find appointments in the target time range
        appointments = Appointment.objects.filter(
            date=now.date(),  # Same day
            time__gte=target_time_start.time(),
            time__lt=target_time_end.time(),
            status='Pending'  # Only pending appointments
        ).select_related('patient', 'doctor')

        self.stdout.write(
            self.style.SUCCESS(f'Found {appointments.count()} appointments for reminder in the next {hours_ahead} hours')
        )

        sent_count = 0
        failed_count = 0

        for appointment in appointments:
            patient_name = f"{appointment.patient.first_name} {appointment.patient.last_name}"

            if dry_run:
                self.stdout.write(
                    f"DRY RUN: Would send reminder to {patient_name} for appointment at {appointment.time.strftime('%H:%M')}"
                )
                sent_count += 1
            else:
                try:
                    if send_appointment_reminder(appointment, hours_ahead):
                        self.stdout.write(
                            self.style.SUCCESS(f"Reminder sent to {patient_name} for {appointment.time.strftime('%H:%M')}")
                        )
                        sent_count += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"Failed to send reminder to {patient_name}")
                        )
                        failed_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error sending reminder to {patient_name}: {str(e)}")
                    )
                    failed_count += 1
                    logger.error(f"Error sending reminder for appointment {appointment.id}: {str(e)}")

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"DRY RUN COMPLETE: Would have sent {sent_count} reminders")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"COMPLETED: Sent {sent_count} reminders, {failed_count} failed")
            )