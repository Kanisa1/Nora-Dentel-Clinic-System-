import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navigation.css';

interface NavProps {
  userRole?: string;
}

const Navigation: React.FC<NavProps> = ({ userRole = 'admin' }) => {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="navigation">
      <div className="nav-brand">
        <h1>Nora Dental Clinic</h1>
      </div>
      <ul className="nav-links">
        <li className={isActive('/') ? 'active' : ''}>
          <Link to="/">Dashboard</Link>
        </li>
        <li className={isActive('/patients') ? 'active' : ''}>
          <Link to="/patients">Patients</Link>
        </li>
        {(userRole === 'admin' || userRole === 'doctor') && (
          <li className={isActive('/medical-records') ? 'active' : ''}>
            <Link to="/medical-records">Medical Records</Link>
          </li>
        )}
        <li className={isActive('/tariffs') ? 'active' : ''}>
          <Link to="/tariffs">Tariffs</Link>
        </li>
        {(userRole === 'admin' || userRole === 'cashier') && (
          <li className={isActive('/invoices') ? 'active' : ''}>
            <Link to="/invoices">Invoices</Link>
          </li>
        )}
        {(userRole === 'admin' || userRole === 'finance') && (
          <li className={isActive('/reports') ? 'active' : ''}>
            <Link to="/reports">Reports</Link>
          </li>
        )}
        {userRole === 'admin' && (
          <li className={isActive('/users') ? 'active' : ''}>
            <Link to="/users">Users</Link>
          </li>
        )}
      </ul>
    </nav>
  );
};

export default Navigation;
