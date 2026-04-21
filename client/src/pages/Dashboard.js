import React from 'react';
import { useAuth } from '../contexts/AuthContext';

function Dashboard() {
  const { user } = useAuth();

  return (
    <div>
      <div className="page-header">
        <h1>Welcome, {user?.name}!</h1>
        <p>Your SQL Lab Dashboard</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Quick Start</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
            Go to the SQL Editor to start writing queries.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
