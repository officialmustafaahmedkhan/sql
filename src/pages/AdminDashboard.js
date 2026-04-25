import React, { useState, useEffect } from 'react';
import { Users, Play, CheckCircle, XCircle, Clock, Activity } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const API_URL = 'https://sql-n5k6.onrender.com/api';

function AdminDashboard() {
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalQueries: 0,
    successfulQueries: 0,
    unsuccessfulQueries: 0,
    avgTime: '0ms'
  });
  const { user } = useAuth();

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (err) {
      console.error('Failed to load stats:', err);
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
        <h1>Admin Dashboard</h1>
        <p>SQL Lab Statistics Overview</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <Users size={28} />
          <div className="value">{stats.totalUsers}</div>
          <div className="subtext">Total Users</div>
        </div>
        <div className="stat-card">
          <Play size={28} />
          <div className="value">{stats.totalQueries}</div>
          <div className="subtext">Total Queries</div>
        </div>
        <div className="stat-card" style={{ borderColor: 'var(--success)' }}>
          <CheckCircle size={28} />
          <div className="value" style={{ color: 'var(--success)' }}>{stats.successfulQueries}</div>
          <div className="subtext">Successful</div>
        </div>
        <div className="stat-card" style={{ borderColor: 'var(--error)' }}>
          <XCircle size={28} />
          <div className="value" style={{ color: 'var(--error)' }}>{stats.unsuccessfulQueries}</div>
          <div className="subtext">Failed</div>
        </div>
        <div className="stat-card">
          <Clock size={28} />
          <div className="value">{stats.avgTime}</div>
          <div className="subtext">Avg Time</div>
        </div>
        <div className="stat-card">
          <Activity size={28} />
          <div className="value">{stats.totalQueries > 0 ? ((stats.successfulQueries / stats.totalQueries) * 100).toFixed(1) : 0}%</div>
          <div className="subtext">Success Rate</div>
        </div>
      </div>
    </div>
  );
}

export default AdminDashboard;