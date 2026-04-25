import React, { useState, useEffect, useCallback } from 'react';
import { Users, Shield, AlertTriangle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

function AdminDashboard() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const { getAllUsers, makeAdmin, user } = useAuth();

  const loadUsers = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAllUsers();
      setUsers(data);
    } catch (err) {
      console.error('Failed to load users:', err);
    } finally {
      setLoading(false);
    }
  }, [getAllUsers]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const handleMakeAdmin = async (uid) => {
    try {
      await makeAdmin(uid);
      await loadUsers();
    } catch (err) {
      console.error('Make admin error:', err);
    }
  };

  if (user?.role !== 'admin') {
    return (
      <div className="auth-container">
        <div className="auth-card" style={{ textAlign: 'center' }}>
          <AlertTriangle size={48} color="var(--warning)" />
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
        <p>Manage users and monitor SQL Lab</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <Users size={24} />
          <div className="value">{users.length}</div>
          <div className="subtext">Total Users</div>
        </div>
        <div className="stat-card">
          <Shield size={24} />
          <div className="value">{users.filter(u => u.role === 'admin').length}</div>
          <div className="subtext">Admins</div>
        </div>
        <div className="stat-card">
          <Users size={24} />
          <div className="value">{users.filter(u => u.role === 'student').length}</div>
          <div className="subtext">Students</div>
        </div>
      </div>

      <div className="results-container">
        <div className="results-header">
          <strong>All Users ({users.length})</strong>
        </div>

        {loading ? (
          <div className="loading-spinner"><div className="spinner"></div></div>
        ) : (
          <table className="results-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.uid}>
                  <td>{u.name || 'N/A'}</td>
                  <td>{u.email}</td>
                  <td>
                    <span style={{ 
                      color: u.role === 'admin' ? 'var(--success)' : 'var(--primary)',
                      fontWeight: 600
                    }}>
                      {u.role}
                    </span>
                  </td>
                  <td>
                    {u.role !== 'admin' && (
                      <button 
                        onClick={() => handleMakeAdmin(u.uid)} 
                        className="btn btn-secondary"
                        style={{ fontSize: '12px', padding: '4px 8px' }}
                      >
                        Make Admin
                      </button>
                    )}
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

export default AdminDashboard;