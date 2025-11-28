import React, { useState, useEffect, useCallback } from 'react';
import { invoiceService, Invoice } from '../services/api';
import './Invoices.css';

const Invoices: React.FC = () => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [paymentAmount, setPaymentAmount] = useState<string>('');
  const [paymentMethod, setPaymentMethod] = useState<string>('cash');

  const fetchInvoices = useCallback(async () => {
    try {
      setLoading(true);
      const params: { status?: string } = {};
      if (statusFilter) {
        params.status = statusFilter;
      }
      const response = await invoiceService.getAll(params);
      setInvoices(response.data.results || []);
    } catch (err) {
      console.error('Failed to fetch invoices:', err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchInvoices();
  }, [fetchInvoices]);

  const handlePayment = async () => {
    if (!selectedInvoice || !paymentAmount) return;

    try {
      await invoiceService.addPayment(selectedInvoice.id, {
        amount: parseFloat(paymentAmount),
        payment_method: paymentMethod,
      });
      setSelectedInvoice(null);
      setPaymentAmount('');
      setPaymentMethod('cash');
      fetchInvoices();
    } catch (err) {
      console.error('Failed to add payment:', err);
    }
  };

  const getStatusBadge = (status: string) => {
    const classes: Record<string, string> = {
      pending: 'badge badge-warning',
      partial: 'badge badge-info',
      paid: 'badge badge-success',
      cancelled: 'badge badge-danger',
    };
    return classes[status] || 'badge';
  };

  return (
    <div className="invoices-page">
      <div className="page-header">
        <h2>Invoices</h2>
      </div>

      <div className="filters">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="partial">Partially Paid</option>
          <option value="paid">Paid</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {loading ? (
        <div className="loading">Loading invoices...</div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Invoice #</th>
              <th>Patient</th>
              <th>Date</th>
              <th>Subtotal</th>
              <th>Insurance</th>
              <th>Patient Pays</th>
              <th>Paid</th>
              <th>Balance</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map(invoice => (
              <tr key={invoice.id}>
                <td>{invoice.invoice_number}</td>
                <td>{invoice.patient_name}</td>
                <td>{invoice.invoice_date}</td>
                <td>${invoice.subtotal}</td>
                <td>${invoice.insurance_coverage}</td>
                <td>${invoice.patient_responsibility}</td>
                <td>${invoice.amount_paid}</td>
                <td>${invoice.balance_due}</td>
                <td>
                  <span className={getStatusBadge(invoice.status)}>
                    {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
                  </span>
                </td>
                <td>
                  {invoice.status !== 'paid' && invoice.status !== 'cancelled' && (
                    <button
                      className="btn-small btn-success"
                      onClick={() => setSelectedInvoice(invoice)}
                    >
                      Add Payment
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {invoices.length === 0 && (
              <tr>
                <td colSpan={10} className="no-data">No invoices found</td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      {selectedInvoice && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Add Payment</h3>
            <p>Invoice: {selectedInvoice.invoice_number}</p>
            <p>Balance Due: ${selectedInvoice.balance_due}</p>
            <div className="form-group">
              <label>Amount</label>
              <input
                type="number"
                value={paymentAmount}
                onChange={(e) => setPaymentAmount(e.target.value)}
                max={parseFloat(selectedInvoice.balance_due)}
                step="0.01"
              />
            </div>
            <div className="form-group">
              <label>Payment Method</label>
              <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}>
                <option value="cash">Cash</option>
                <option value="card">Card</option>
                <option value="insurance">Insurance</option>
                <option value="bank_transfer">Bank Transfer</option>
                <option value="mobile_money">Mobile Money</option>
              </select>
            </div>
            <div className="form-actions">
              <button onClick={() => setSelectedInvoice(null)}>Cancel</button>
              <button className="btn-primary" onClick={handlePayment}>
                Process Payment
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Invoices;
