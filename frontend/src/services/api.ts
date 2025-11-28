import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // For session-based authentication
});

// Types
export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'admin' | 'receptionist' | 'doctor' | 'cashier' | 'finance';
  phone: string;
  address: string;
  is_active: boolean;
}

export interface Patient {
  id: number;
  first_name: string;
  last_name: string;
  full_name: string;
  date_of_birth: string;
  gender: 'M' | 'F' | 'O';
  national_id: string;
  phone: string;
  email: string;
  address: string;
  insurance_company: number | null;
  insurance_company_name: string;
  insurance_number: string;
  insurance_percentage: string;
  patient_pays_percentage: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
}

export interface Tariff {
  id: number;
  code: string;
  name: string;
  description: string;
  category: number;
  category_name: string;
  unit_price: string;
  is_active: boolean;
}

export interface MedicalRecord {
  id: number;
  patient: number;
  patient_name: string;
  doctor: number;
  doctor_name: string;
  visit_date: string;
  chief_complaint: string;
  diagnosis: string;
  treatment_plan: string;
  notes: string;
}

export interface InvoiceItem {
  id: number;
  invoice: number;
  tariff: number;
  tariff_code: string;
  tariff_name: string;
  description: string;
  quantity: number;
  unit_price: string;
  total_price: string;
}

export interface Invoice {
  id: number;
  invoice_number: string;
  patient: number;
  patient_name: string;
  medical_record: number | null;
  subtotal: string;
  insurance_coverage: string;
  patient_responsibility: string;
  amount_paid: string;
  balance_due: string;
  status: 'pending' | 'partial' | 'paid' | 'cancelled';
  items: InvoiceItem[];
  invoice_date: string;
}

// API Services
export const userService = {
  getAll: () => apiClient.get<User[]>('/users/'),
  getById: (id: number) => apiClient.get<User>(`/users/${id}/`),
  getCurrentUser: () => apiClient.get<User>('/users/me/'),
  getDoctors: () => apiClient.get<User[]>('/users/doctors/'),
  create: (data: Partial<User> & { password: string; password_confirm: string }) => 
    apiClient.post<User>('/users/', data),
  update: (id: number, data: Partial<User>) => 
    apiClient.patch<User>(`/users/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/users/${id}/`),
};

export const patientService = {
  getAll: (params?: { search?: string; insurance_company?: number }) => 
    apiClient.get<{ results: Patient[] }>('/patients/', { params }),
  getById: (id: number) => apiClient.get<Patient>(`/patients/${id}/`),
  create: (data: Partial<Patient>) => apiClient.post<Patient>('/patients/', data),
  update: (id: number, data: Partial<Patient>) => 
    apiClient.patch<Patient>(`/patients/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/patients/${id}/`),
};

export const tariffService = {
  getAll: (params?: { category?: number; search?: string; is_active?: boolean }) => 
    apiClient.get<{ results: Tariff[] }>('/tariffs/', { params }),
  getById: (id: number) => apiClient.get<Tariff>(`/tariffs/${id}/`),
  create: (data: Partial<Tariff>) => apiClient.post<Tariff>('/tariffs/', data),
  update: (id: number, data: Partial<Tariff>) => 
    apiClient.patch<Tariff>(`/tariffs/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/tariffs/${id}/`),
};

export const medicalRecordService = {
  getAll: (params?: { patient?: number; doctor?: number }) => 
    apiClient.get<{ results: MedicalRecord[] }>('/medical-records/', { params }),
  getById: (id: number) => apiClient.get<MedicalRecord>(`/medical-records/${id}/`),
  create: (data: Partial<MedicalRecord>) => 
    apiClient.post<MedicalRecord>('/medical-records/', data),
  update: (id: number, data: Partial<MedicalRecord>) => 
    apiClient.patch<MedicalRecord>(`/medical-records/${id}/`, data),
  createInvoice: (id: number, tariffs: number[]) => 
    apiClient.post<Invoice>(`/medical-records/${id}/create_invoice/`, { tariffs }),
};

export const invoiceService = {
  getAll: (params?: { patient?: number; status?: string }) => 
    apiClient.get<{ results: Invoice[] }>('/invoices/', { params }),
  getById: (id: number) => apiClient.get<Invoice>(`/invoices/${id}/`),
  addPayment: (id: number, data: { amount: number; payment_method: string; notes?: string }) => 
    apiClient.post(`/invoices/${id}/add_payment/`, data),
  cancel: (id: number) => apiClient.post(`/invoices/${id}/cancel/`),
};

export const reportService = {
  getDaily: (date?: string) => 
    apiClient.get('/reports/daily/', { params: { date } }),
  getMonthly: (year?: number, month?: number) => 
    apiClient.get('/reports/monthly/', { params: { year, month } }),
  getDoctorIncome: (params?: { doctor_id?: number; start_date?: string; end_date?: string }) => 
    apiClient.get('/reports/doctor-income/', { params }),
  getInsurance: (params?: { insurance_id?: number; start_date?: string; end_date?: string }) => 
    apiClient.get('/reports/insurance/', { params }),
  getHMIS: (params?: { start_date?: string; end_date?: string }) => 
    apiClient.get('/reports/hmis/', { params }),
  getIDSR: (params?: { start_date?: string; end_date?: string }) => 
    apiClient.get('/reports/idsr/', { params }),
  getDashboard: () => apiClient.get('/dashboard/'),
};

export default apiClient;
