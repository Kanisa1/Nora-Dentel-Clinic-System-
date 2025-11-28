from rest_framework import serializers
from .models import Tariff


class TariffSerializer(serializers.ModelSerializer):
    """Serializer for Tariff model."""

    class Meta:
        model = Tariff
        fields = '__all__'
