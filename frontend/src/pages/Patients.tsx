import React, { useState, useEffect } from 'react';
import { patientService, Patient } from '../services/api';
import './Patients.css';

const Patients: React.FC = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<Partial<Patient>>({
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: 'M',
    phone: '',
    email: '',
    insurance_percentage: '0',
  });

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async (searchQuery?: string) => {
    try {
      setLoading(true);
      const response = await patientService.getAll({ search: searchQuery });
      setPatients(response.data.results || []);
    } catch (err) {
      console.error('Failed to fetch patients:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchPatients(search);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await patientService.create(formData);
      setShowForm(false);
      setFormData({
        first_name: '',
        last_name: '',
        date_of_birth: '',
        gender: 'M',
        phone: '',
        email: '',
        insurance_percentage: '0',
      });
      fetchPatients();
    } catch (err) {
      console.error('Failed to create patient:', err);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  return (
    <div className="patients-page">
      <div className="page-header">
        <h2>Patients</h2>
        <button className="btn-primary" onClick={() => setShowForm(true)}>
          + Add Patient
        </button>
      </div>

      <form className="search-form" onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Search patients..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button type="submit">Search</button>
      </form>

      {showForm && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Add New Patient</h3>
            <form onSubmit={handleSubmit}>
              <div className="form-row">
                <div className="form-group">
                  <label>First Name</label>
                  <input
                    type="text"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Last Name</label>
                  <input
                    type="text"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleInputChange}
                    required
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Date of Birth</label>
                  <input
                    type="date"
                    name="date_of_birth"
                    value={formData.date_of_birth}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Gender</label>
                  <select name="gender" value={formData.gender} onChange={handleInputChange}>
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                    <option value="O">Other</option>
                  </select>
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Phone</label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Email</label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Insurance Coverage (%)</label>
                <input
                  type="number"
                  name="insurance_percentage"
                  value={formData.insurance_percentage}
                  onChange={handleInputChange}
                  min="0"
                  max="100"
                />
              </div>
              <div className="form-actions">
                <button type="button" onClick={() => setShowForm(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading patients...</div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Phone</th>
              <th>Gender</th>
              <th>Insurance %</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {patients.map(patient => (
              <tr key={patient.id}>
                <td>{patient.full_name}</td>
                <td>{patient.phone}</td>
                <td>{patient.gender === 'M' ? 'Male' : patient.gender === 'F' ? 'Female' : 'Other'}</td>
                <td>{patient.insurance_percentage}%</td>
                <td>
                  <button className="btn-small">View</button>
                </td>
              </tr>
            ))}
            {patients.length === 0 && (
              <tr>
                <td colSpan={5} className="no-data">No patients found</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default Patients;
