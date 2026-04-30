import React, { useState, useEffect, useCallback } from 'react';
import { CheckCircle, XCircle, Clock, UserPlus } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'https://sql-lab-new.onrender.com/api';

function PendingRequests() {
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/admin/pending`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPending(response.data.pending || []);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleApprove = async (email) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_URL}/admin/approve`, { email, action: 'approve' }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      await loadData();
    } catch (err) {
      console.error('Approve error:', err);
    }
  };

  const handleReject = async (email) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_URL}/admin/approve`, { email, action: 'reject' }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      await loadData();
    } catch (err) {
      console.error('Reject error:', err);
    }
  };

  if (user?.role !== 'admin') {
    return (
      <div className="auth-container">
        <div className="auth-card" style={{ textAlign: 'center' }}>
          <h2>Access Denied</h2>
          <p>Only administrators can access this page.</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1>Pending Requests</h1>
        <p>Approve or reject new user registrations</p>
      </div>

      <div className="results-container">
        <div className="results-header">
          <strong>Pending Requests ({pending.length})</strong>
        </div>

        {loading ? (
          <div className="loading-spinner"><div className="spinner"></div></div>
        ) : pending.length === 0 ? (
          <div className="results-empty">
            <UserPlus size={48} style={{ marginBottom: '12px', opacity: 0.5 }} />
            <p>No pending requests</p>
          </div>
        ) : (
          <table className="results-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Requested At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {pending.map((r, i) => (
                <tr key={i}>
                  <td>{r.name}</td>
                  <td>{r.email}</td>
                  <td style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={14} /> {new Date(r.timestamp).toLocaleString()}
                  </td>
                  <td>
                    <button 
                      onClick={() => handleApprove(r.email)} 
                      style={{ background: 'var(--success)', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', marginRight: '8px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                    >
                      <CheckCircle size={14} /> Approve
                    </button>
                    <button 
                      onClick={() => handleReject(r.email)} 
                      style={{ background: 'var(--error)', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                    >
                      <XCircle size={14} /> Reject
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default PendingRequests;