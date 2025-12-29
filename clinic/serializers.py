from rest_framework import serializers
from .models import *

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'

class PatientCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientCard
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'

class TriageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Triage
        fields = '__all__'

class QueueEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = WaitingQueueEntry
        fields = '__all__'

class TariffActSerializer(serializers.ModelSerializer):
    class Meta:
        model = TariffAct
        fields = '__all__'

class BillingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingItem
        fields = '__all__'

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'
