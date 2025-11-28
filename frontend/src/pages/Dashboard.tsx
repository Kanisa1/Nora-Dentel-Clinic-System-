import React, { useState, useEffect } from 'react';
import { reportService } from '../services/api';
import './Dashboard.css';

interface DashboardData {
  today: {
    visits: number;
    payments: string;
  };
  pending: {
    invoices: number;
    prescriptions: number;
  };
  alerts: {
    low_stock_drugs: number;
  };
  totals: {
    patients: number;
    doctors: number;
  };
}

const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await reportService.getDashboard();
        setData(response.data);
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="dashboard">
      <h2>Dashboard</h2>
      
      <div className="dashboard-grid">
        <div className="dashboard-card today">
          <h3>Today's Activity</h3>
          <div className="stat">
            <span className="stat-value">{data?.today.visits || 0}</span>
            <span className="stat-label">Visits</span>
          </div>
          <div className="stat">
            <span className="stat-value">${data?.today.payments || '0.00'}</span>
            <span className="stat-label">Payments Received</span>
          </div>
        </div>

        <div className="dashboard-card pending">
          <h3>Pending</h3>
          <div className="stat">
            <span className="stat-value">{data?.pending.invoices || 0}</span>
            <span className="stat-label">Unpaid Invoices</span>
          </div>
          <div className="stat">
            <span className="stat-value">{data?.pending.prescriptions || 0}</span>
            <span className="stat-label">Prescriptions to Dispense</span>
          </div>
        </div>

        <div className="dashboard-card alerts">
          <h3>Alerts</h3>
          <div className="stat">
            <span className="stat-value warning">{data?.alerts.low_stock_drugs || 0}</span>
            <span className="stat-label">Low Stock Drugs</span>
          </div>
        </div>

        <div className="dashboard-card totals">
          <h3>Overall</h3>
          <div className="stat">
            <span className="stat-value">{data?.totals.patients || 0}</span>
            <span className="stat-label">Total Patients</span>
          </div>
          <div className="stat">
            <span className="stat-value">{data?.totals.doctors || 0}</span>
            <span className="stat-label">Active Doctors</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
