import React, { useState } from 'react';
import { reportService } from '../services/api';
import './Reports.css';

type ReportType = 'daily' | 'monthly' | 'doctor-income' | 'insurance' | 'hmis' | 'idsr';

const Reports: React.FC = () => {
  const [activeReport, setActiveReport] = useState<ReportType>('daily');
  const [reportData, setReportData] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const [dateParams, setDateParams] = useState({
    date: new Date().toISOString().split('T')[0],
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    start_date: '',
    end_date: '',
  });

  const fetchReport = async () => {
    setLoading(true);
    try {
      let response;
      switch (activeReport) {
        case 'daily':
          response = await reportService.getDaily(dateParams.date);
          break;
        case 'monthly':
          response = await reportService.getMonthly(dateParams.year, dateParams.month);
          break;
        case 'doctor-income':
          response = await reportService.getDoctorIncome({
            start_date: dateParams.start_date,
            end_date: dateParams.end_date,
          });
          break;
        case 'insurance':
          response = await reportService.getInsurance({
            start_date: dateParams.start_date,
            end_date: dateParams.end_date,
          });
          break;
        case 'hmis':
          response = await reportService.getHMIS({
            start_date: dateParams.start_date,
            end_date: dateParams.end_date,
          });
          break;
        case 'idsr':
          response = await reportService.getIDSR({
            start_date: dateParams.start_date,
            end_date: dateParams.end_date,
          });
          break;
      }
      setReportData(response?.data);
    } catch (err) {
      console.error('Failed to fetch report:', err);
    } finally {
      setLoading(false);
    }
  };

  const renderReportContent = () => {
    if (loading) {
      return <div className="loading">Loading report...</div>;
    }

    if (!reportData) {
      return <div className="no-data">Select parameters and generate report</div>;
    }

    // Render report data as JSON for now (can be enhanced with proper formatting)
    return (
      <div className="report-content">
        <pre>{JSON.stringify(reportData, null, 2)}</pre>
      </div>
    );
  };

  return (
    <div className="reports-page">
      <h2>Reports</h2>

      <div className="report-tabs">
        <button
          className={activeReport === 'daily' ? 'active' : ''}
          onClick={() => setActiveReport('daily')}
        >
          Daily Report
        </button>
        <button
          className={activeReport === 'monthly' ? 'active' : ''}
          onClick={() => setActiveReport('monthly')}
        >
          Monthly Report
        </button>
        <button
          className={activeReport === 'doctor-income' ? 'active' : ''}
          onClick={() => setActiveReport('doctor-income')}
        >
          Doctor Income
        </button>
        <button
          className={activeReport === 'insurance' ? 'active' : ''}
          onClick={() => setActiveReport('insurance')}
        >
          Insurance Report
        </button>
        <button
          className={activeReport === 'hmis' ? 'active' : ''}
          onClick={() => setActiveReport('hmis')}
        >
          HMIS Report
        </button>
        <button
          className={activeReport === 'idsr' ? 'active' : ''}
          onClick={() => setActiveReport('idsr')}
        >
          IDSR Report
        </button>
      </div>

      <div className="report-params">
        {activeReport === 'daily' && (
          <div className="form-group">
            <label>Date</label>
            <input
              type="date"
              value={dateParams.date}
              onChange={(e) => setDateParams({ ...dateParams, date: e.target.value })}
            />
          </div>
        )}

        {activeReport === 'monthly' && (
          <>
            <div className="form-group">
              <label>Year</label>
              <input
                type="number"
                value={dateParams.year}
                onChange={(e) => setDateParams({ ...dateParams, year: parseInt(e.target.value) })}
              />
            </div>
            <div className="form-group">
              <label>Month</label>
              <select
                value={dateParams.month}
                onChange={(e) => setDateParams({ ...dateParams, month: parseInt(e.target.value) })}
              >
                {[...Array(12)].map((_, i) => (
                  <option key={i + 1} value={i + 1}>
                    {new Date(2000, i).toLocaleString('default', { month: 'long' })}
                  </option>
                ))}
              </select>
            </div>
          </>
        )}

        {['doctor-income', 'insurance', 'hmis', 'idsr'].includes(activeReport) && (
          <>
            <div className="form-group">
              <label>Start Date</label>
              <input
                type="date"
                value={dateParams.start_date}
                onChange={(e) => setDateParams({ ...dateParams, start_date: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>End Date</label>
              <input
                type="date"
                value={dateParams.end_date}
                onChange={(e) => setDateParams({ ...dateParams, end_date: e.target.value })}
              />
            </div>
          </>
        )}

        <button className="btn-primary" onClick={fetchReport}>
          Generate Report
        </button>
      </div>

      {renderReportContent()}
    </div>
  );
};

export default Reports;
