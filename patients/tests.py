from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Patient


class PatientModelTests(TestCase):
    """Tests for Patient model."""

    def test_create_patient(self):
        """Test creating a patient."""
        patient = Patient.objects.create(
            first_name="Jane",
            last_name="Doe",
            date_of_birth="1995-03-20",
            gender="F",
            phone_number="+0987654321",
            insurance_percentage=50.00,
            department="general"
        )
        self.assertEqual(str(patient), "Jane Doe")
        self.assertEqual(patient.department, "general")


class PatientAPITests(APITestCase):
    """Tests for Patient API endpoints."""

    def test_list_patients(self):
        """Test GET /api/patients/ returns a list."""
        response = self.client.get('/api/patients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_patient(self):
        """Test POST /api/patients/ creates a patient."""
        data = {
            "first_name": "Test",
            "last_name": "Patient",
            "date_of_birth": "2000-01-01",
            "gender": "M",
            "phone_number": "+1111111111",
            "insurance_percentage": 100.00,
            "department": "orthodontics"
        }
        response = self.client.post('/api/patients/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Patient.objects.count(), 1)
        self.assertEqual(Patient.objects.get().first_name, "Test")
