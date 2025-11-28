from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    User, Patient, Invoice, InvoiceItem, Payment,
    MedicalRecord, Drug, Prescription, InsuranceCompany
)


class DailyReportView(APIView):
    """Daily report with summary of activities."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        date_str = request.query_params.get('date')
        if date_str:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            report_date = timezone.now().date()
        
        # Get start and end of day
        start_of_day = timezone.make_aware(
            datetime.combine(report_date, datetime.min.time())
        )
        end_of_day = timezone.make_aware(
            datetime.combine(report_date, datetime.max.time())
        )
        
        # Patient statistics
        patients_registered = Patient.objects.filter(
            created_at__range=(start_of_day, end_of_day)
        ).count()
        
        # Visit statistics
        visits = MedicalRecord.objects.filter(
            visit_date__range=(start_of_day, end_of_day)
        ).count()
        
        # Invoice statistics
        invoices = Invoice.objects.filter(
            created_at__range=(start_of_day, end_of_day)
        )
        invoices_count = invoices.count()
        invoices_total = invoices.aggregate(
            total=Sum('subtotal')
        )['total'] or Decimal('0')
        
        # Payment statistics
        payments = Payment.objects.filter(
            payment_date__range=(start_of_day, end_of_day)
        )
        payments_count = payments.count()
        payments_total = payments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        # Payment breakdown by method
        payment_methods = payments.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        # Prescriptions dispensed
        prescriptions_dispensed = Prescription.objects.filter(
            dispensed_at__range=(start_of_day, end_of_day)
        ).count()
        
        return Response({
            'date': report_date.isoformat(),
            'patients': {
                'registered': patients_registered,
                'visits': visits,
            },
            'invoices': {
                'count': invoices_count,
                'total': str(invoices_total),
            },
            'payments': {
                'count': payments_count,
                'total': str(payments_total),
                'by_method': list(payment_methods),
            },
            'prescriptions_dispensed': prescriptions_dispensed,
        })


class MonthlyReportView(APIView):
    """Monthly report with summary of activities."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))
        
        # Get first and last day of month
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        start_of_month = timezone.make_aware(
            datetime.combine(first_day, datetime.min.time())
        )
        end_of_month = timezone.make_aware(
            datetime.combine(last_day, datetime.max.time())
        )
        
        # Patient statistics
        patients_registered = Patient.objects.filter(
            created_at__range=(start_of_month, end_of_month)
        ).count()
        total_patients = Patient.objects.count()
        
        # Visit statistics
        visits = MedicalRecord.objects.filter(
            visit_date__range=(start_of_month, end_of_month)
        )
        visits_count = visits.count()
        visits_by_doctor = visits.values(
            'doctor__username', 'doctor__first_name', 'doctor__last_name'
        ).annotate(count=Count('id')).order_by('-count')
        
        # Invoice statistics
        invoices = Invoice.objects.filter(
            created_at__range=(start_of_month, end_of_month)
        )
        invoices_count = invoices.count()
        invoices_total = invoices.aggregate(
            subtotal=Sum('subtotal'),
            insurance_coverage=Sum('insurance_coverage'),
            patient_responsibility=Sum('patient_responsibility'),
            amount_paid=Sum('amount_paid')
        )
        
        # Payment statistics
        payments = Payment.objects.filter(
            payment_date__range=(start_of_month, end_of_month)
        )
        payments_total = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Daily breakdown
        daily_payments = payments.extra(
            select={'day': 'DATE(payment_date)'}
        ).values('day').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('day')
        
        return Response({
            'year': year,
            'month': month,
            'patients': {
                'registered_this_month': patients_registered,
                'total': total_patients,
            },
            'visits': {
                'count': visits_count,
                'by_doctor': list(visits_by_doctor),
            },
            'invoices': {
                'count': invoices_count,
                'subtotal': str(invoices_total['subtotal'] or 0),
                'insurance_coverage': str(invoices_total['insurance_coverage'] or 0),
                'patient_responsibility': str(invoices_total['patient_responsibility'] or 0),
                'amount_paid': str(invoices_total['amount_paid'] or 0),
            },
            'payments': {
                'total': str(payments_total),
                'daily_breakdown': list(daily_payments),
            },
        })


class DoctorIncomeReportView(APIView):
    """Report on doctor's income from invoices."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        doctor_id = request.query_params.get('doctor_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Default to current month
        if not start_date or not end_date:
            now = timezone.now()
            first_day = datetime(now.year, now.month, 1)
            if now.month == 12:
                last_day = datetime(now.year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = datetime(now.year, now.month + 1, 1) - timedelta(days=1)
            
            start_date = first_day.strftime('%Y-%m-%d')
            end_date = last_day.strftime('%Y-%m-%d')
        
        start_dt = timezone.make_aware(
            datetime.strptime(start_date, '%Y-%m-%d')
        )
        end_dt = timezone.make_aware(
            datetime.combine(
                datetime.strptime(end_date, '%Y-%m-%d'),
                datetime.max.time()
            )
        )
        
        # Base queryset for medical records
        records = MedicalRecord.objects.filter(
            visit_date__range=(start_dt, end_dt)
        )
        
        if doctor_id:
            records = records.filter(doctor_id=doctor_id)
        
        # Get invoices linked to these records
        record_ids = records.values_list('id', flat=True)
        invoices = Invoice.objects.filter(
            medical_record_id__in=record_ids
        )
        
        # Aggregate by doctor
        doctor_income = records.values(
            'doctor__id', 'doctor__username',
            'doctor__first_name', 'doctor__last_name'
        ).annotate(
            visits=Count('id'),
            total_billed=Sum(
                'invoices__subtotal',
                default=Decimal('0')
            ),
            total_paid=Sum(
                'invoices__amount_paid',
                default=Decimal('0')
            )
        ).order_by('-total_billed')
        
        return Response({
            'start_date': start_date,
            'end_date': end_date,
            'doctors': list(doctor_income),
            'summary': {
                'total_visits': records.count(),
                'total_billed': str(
                    invoices.aggregate(total=Sum('subtotal'))['total'] or 0
                ),
                'total_paid': str(
                    invoices.aggregate(total=Sum('amount_paid'))['total'] or 0
                ),
            }
        })


class InsuranceReportView(APIView):
    """Report on insurance claims and payments."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        insurance_id = request.query_params.get('insurance_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Default to current month
        if not start_date or not end_date:
            now = timezone.now()
            first_day = datetime(now.year, now.month, 1)
            if now.month == 12:
                last_day = datetime(now.year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = datetime(now.year, now.month + 1, 1) - timedelta(days=1)
            
            start_date = first_day.strftime('%Y-%m-%d')
            end_date = last_day.strftime('%Y-%m-%d')
        
        start_dt = timezone.make_aware(
            datetime.strptime(start_date, '%Y-%m-%d')
        )
        end_dt = timezone.make_aware(
            datetime.combine(
                datetime.strptime(end_date, '%Y-%m-%d'),
                datetime.max.time()
            )
        )
        
        # Base queryset
        invoices = Invoice.objects.filter(
            created_at__range=(start_dt, end_dt),
            patient__insurance_company__isnull=False
        ).select_related('patient__insurance_company')
        
        if insurance_id:
            invoices = invoices.filter(patient__insurance_company_id=insurance_id)
        
        # Aggregate by insurance company
        insurance_summary = invoices.values(
            'patient__insurance_company__id',
            'patient__insurance_company__name',
            'patient__insurance_company__code'
        ).annotate(
            invoices_count=Count('id'),
            total_billed=Sum('subtotal'),
            insurance_coverage=Sum('insurance_coverage'),
            patient_paid=Sum('amount_paid')
        ).order_by('-insurance_coverage')
        
        # Get detailed breakdown if specific insurance requested
        details = []
        if insurance_id:
            details = invoices.values(
                'invoice_number',
                'patient__first_name',
                'patient__last_name',
                'subtotal',
                'insurance_coverage',
                'patient_responsibility',
                'amount_paid',
                'status',
                'invoice_date'
            ).order_by('-invoice_date')
        
        return Response({
            'start_date': start_date,
            'end_date': end_date,
            'insurance_companies': list(insurance_summary),
            'details': list(details) if insurance_id else [],
            'summary': {
                'total_invoices': invoices.count(),
                'total_billed': str(
                    invoices.aggregate(total=Sum('subtotal'))['total'] or 0
                ),
                'total_insurance_coverage': str(
                    invoices.aggregate(total=Sum('insurance_coverage'))['total'] or 0
                ),
            }
        })


class HMISReportView(APIView):
    """Health Management Information System (HMIS) report."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Default to current month
        if not start_date or not end_date:
            now = timezone.now()
            first_day = datetime(now.year, now.month, 1)
            if now.month == 12:
                last_day = datetime(now.year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = datetime(now.year, now.month + 1, 1) - timedelta(days=1)
            
            start_date = first_day.strftime('%Y-%m-%d')
            end_date = last_day.strftime('%Y-%m-%d')
        
        start_dt = timezone.make_aware(
            datetime.strptime(start_date, '%Y-%m-%d')
        )
        end_dt = timezone.make_aware(
            datetime.combine(
                datetime.strptime(end_date, '%Y-%m-%d'),
                datetime.max.time()
            )
        )
        
        # Patient demographics
        patients = Patient.objects.filter(
            created_at__range=(start_dt, end_dt)
        )
        
        gender_breakdown = patients.values('gender').annotate(
            count=Count('id')
        )
        
        # Age groups
        today = timezone.now().date()
        age_groups = {
            '0-5': 0,
            '6-12': 0,
            '13-17': 0,
            '18-35': 0,
            '36-50': 0,
            '51-65': 0,
            '65+': 0
        }
        
        for patient in patients:
            age = (today - patient.date_of_birth).days // 365
            if age <= 5:
                age_groups['0-5'] += 1
            elif age <= 12:
                age_groups['6-12'] += 1
            elif age <= 17:
                age_groups['13-17'] += 1
            elif age <= 35:
                age_groups['18-35'] += 1
            elif age <= 50:
                age_groups['36-50'] += 1
            elif age <= 65:
                age_groups['51-65'] += 1
            else:
                age_groups['65+'] += 1
        
        # Visits/consultations
        visits = MedicalRecord.objects.filter(
            visit_date__range=(start_dt, end_dt)
        )
        
        # Common diagnoses
        # Note: In a real system, you'd have ICD codes
        diagnoses = visits.exclude(diagnosis='').values('diagnosis').annotate(
            count=Count('id')
        ).order_by('-count')[:20]
        
        # Services rendered (tariffs used)
        services = InvoiceItem.objects.filter(
            invoice__created_at__range=(start_dt, end_dt)
        ).values(
            'tariff__code', 'tariff__name'
        ).annotate(
            count=Sum('quantity'),
            total_value=Sum('total_price')
        ).order_by('-count')[:20]
        
        return Response({
            'period': {
                'start_date': start_date,
                'end_date': end_date,
            },
            'patients': {
                'new_registrations': patients.count(),
                'total_consultations': visits.count(),
                'gender_breakdown': list(gender_breakdown),
                'age_groups': age_groups,
            },
            'diagnoses': list(diagnoses),
            'services': list(services),
        })


class IDSRReportView(APIView):
    """Integrated Disease Surveillance and Response (IDSR) report."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Default to current week
        if not start_date or not end_date:
            now = timezone.now()
            start_of_week = now - timedelta(days=now.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            start_date = start_of_week.strftime('%Y-%m-%d')
            end_date = end_of_week.strftime('%Y-%m-%d')
        
        start_dt = timezone.make_aware(
            datetime.strptime(start_date, '%Y-%m-%d')
        )
        end_dt = timezone.make_aware(
            datetime.combine(
                datetime.strptime(end_date, '%Y-%m-%d'),
                datetime.max.time()
            )
        )
        
        # Medical records in period
        records = MedicalRecord.objects.filter(
            visit_date__range=(start_dt, end_dt)
        ).select_related('patient')
        
        # Conditions to track (would be ICD codes in real system)
        # This is a simplified version for common dental conditions
        tracked_conditions = [
            'dental caries',
            'gingivitis',
            'periodontitis',
            'tooth abscess',
            'oral infection',
            'tooth extraction',
            'root canal',
        ]
        
        condition_counts = {}
        for condition in tracked_conditions:
            count = records.filter(
                Q(diagnosis__icontains=condition) |
                Q(chief_complaint__icontains=condition)
            ).count()
            if count > 0:
                condition_counts[condition] = count
        
        # Age-sex breakdown for cases
        case_breakdown = []
        for record in records:
            patient = record.patient
            age = (timezone.now().date() - patient.date_of_birth).days // 365
            case_breakdown.append({
                'age': age,
                'gender': patient.gender,
                'diagnosis': record.diagnosis[:100],
            })
        
        return Response({
            'reporting_period': {
                'start_date': start_date,
                'end_date': end_date,
                'week_number': datetime.strptime(start_date, '%Y-%m-%d').isocalendar()[1],
            },
            'total_cases': records.count(),
            'tracked_conditions': condition_counts,
            'case_breakdown': case_breakdown[:100],  # Limit for performance
        })


class DashboardView(APIView):
    """Dashboard summary view."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        now = timezone.now()
        today = now.date()
        start_of_day = timezone.make_aware(
            datetime.combine(today, datetime.min.time())
        )
        end_of_day = timezone.make_aware(
            datetime.combine(today, datetime.max.time())
        )
        
        # Today's statistics
        todays_visits = MedicalRecord.objects.filter(
            visit_date__range=(start_of_day, end_of_day)
        ).count()
        
        todays_payments = Payment.objects.filter(
            payment_date__range=(start_of_day, end_of_day)
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        pending_invoices = Invoice.objects.filter(
            status=Invoice.Status.PENDING
        ).count()
        
        # Low stock alerts
        low_stock_drugs = Drug.objects.filter(
            stock_quantity__lte=F('reorder_level')
        ).count()
        
        # Overall statistics
        total_patients = Patient.objects.count()
        total_doctors = User.objects.filter(
            role=User.Role.DOCTOR, is_active=True
        ).count()
        
        # Pending prescriptions
        pending_prescriptions = Prescription.objects.filter(
            is_dispensed=False
        ).count()
        
        return Response({
            'today': {
                'visits': todays_visits,
                'payments': str(todays_payments),
            },
            'pending': {
                'invoices': pending_invoices,
                'prescriptions': pending_prescriptions,
            },
            'alerts': {
                'low_stock_drugs': low_stock_drugs,
            },
            'totals': {
                'patients': total_patients,
                'doctors': total_doctors,
            }
        })
