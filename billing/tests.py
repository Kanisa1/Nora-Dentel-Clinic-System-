from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Tariff


class TariffModelTests(TestCase):
    """Tests for Tariff model."""

    def test_create_tariff(self):
        """Test creating a tariff."""
        tariff = Tariff.objects.create(
            act_name="Root Canal",
            description="Root canal treatment",
            department="endodontics",
            price=500.00
        )
        self.assertIn("Root Canal", str(tariff))
        self.assertEqual(tariff.department, "endodontics")


class TariffAPITests(APITestCase):
    """Tests for Tariff API endpoints."""

    def test_list_tariffs(self):
        """Test GET /api/tariffs/ returns a list."""
        response = self.client.get('/api/tariffs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_tariff(self):
        """Test POST /api/tariffs/ creates a tariff."""
        data = {
            "act_name": "Tooth Extraction",
            "description": "Simple tooth extraction",
            "department": "oral_surgery",
            "price": 150.00,
            "is_active": True
        }
        response = self.client.post('/api/tariffs/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tariff.objects.count(), 1)
        self.assertEqual(Tariff.objects.get().act_name, "Tooth Extraction")
