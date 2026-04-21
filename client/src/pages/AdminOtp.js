import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function AdminOtp() {
  const [otps, setOtps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchOtps = async () => {
    try {
      const response = await axios.get(`${API_URL}/admin/otps`);
      setOtps(response.data.otps);
      setError('');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to fetch OTPs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOtps();
    const interval = setInterval(fetchOtps, 5000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const copyOtp = (otp) => {
    navigator.clipboard.writeText(otp);
  };

  if (loading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        Loading...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: 'red' }}>
        {error}
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <h2 style={{ marginBottom: '20px' }}>Active OTPs</h2>
      <p style={{ marginBottom: '20px', color: '#666' }}>
        These OTPs will expire in 5 minutes. Auto-refreshes every 5 seconds.
      </p>

      {otps.length === 0 ? (
        <p style={{ color: '#666' }}>No active OTPs</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <thead>
            <tr style={{ background: '#667eea', color: 'white' }}>
              <th style={{ padding: '12px', textAlign: 'left' }}>Email</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Name</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>OTP</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Created</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Expires</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {otps.map((otp) => (
              <tr key={otp.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: '12px' }}>{otp.email}</td>
                <td style={{ padding: '12px' }}>{otp.name || '-'}</td>
                <td style={{ padding: '12px', fontFamily: 'monospace', fontSize: '18px', fontWeight: 'bold', color: '#667eea' }}>
                  {otp.otp}
                </td>
                <td style={{ padding: '12px' }}>{formatTime(otp.created_at)}</td>
                <td style={{ padding: '12px' }}>{formatTime(otp.expires_at)}</td>
                <td style={{ padding: '12px' }}>
                  <button
                    onClick={() => copyOtp(otp.otp)}
                    style={{
                      padding: '6px 12px',
                      background: '#667eea',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Copy
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default AdminOtp;
