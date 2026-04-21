import React, { useState, useEffect } from 'react';
import { Users, Database, Activity, CheckCircle, XCircle, Clock, Eye } from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [students, setStudents] = useState([]);
  const [recentQueries, setRecentQueries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [studentQueries, setStudentQueries] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API_URL}/admin/dashboard`);
      setStats(response.data);
      setStudents(response.data.recentQueries?.reduce((acc, q) => {
        if (!acc.find(s => s.id === q.user_id)) {
          acc.push({ id: q.user_id, name: q.name, email: q.email });
        }
        return acc;
      }, []) || []);
      setRecentQueries(response.data.recentQueries || []);
    } catch (err) {
      console.error('Failed to fetch dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStudentQueries = async (studentId) => {
    try {
      const response = await axios.get(`${API_URL}/admin/students/${studentId}/queries`);
      setStudentQueries(response.data.queries);
      setSelectedStudent(students.find(s => s.id === studentId));
    } catch (err) {
      console.error('Failed to fetch student queries:', err);
    }
  };

  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1>Admin Dashboard</h1>
        <p>Monitor all student activity and system statistics</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <h3><Users size={16} style={{ marginRight: '8px', display: 'inline' }} />Total Students</h3>
          <div className="value">{stats?.totalStudents || 0}</div>
          <div className="subtext">{stats?.verifiedStudents || 0} verified</div>
        </div>
        <div className="stat-card">
          <h3><Database size={16} style={{ marginRight: '8px', display: 'inline' }} />Total Queries</h3>
          <div className="value">{stats?.totalQueries || 0}</div>
          <div className="subtext">All time executions</div>
        </div>
        <div className="stat-card">
          <h3><CheckCircle size={16} style={{ marginRight: '8px', display: 'inline', color: '#10b981' }} />Successful</h3>
          <div className="value" style={{ color: '#10b981' }}>{stats?.successfulQueries || 0}</div>
          <div className="subtext">Completed queries</div>
        </div>
        <div className="stat-card">
          <h3><XCircle size={16} style={{ marginRight: '8px', display: 'inline', color: '#ef4444' }} />Failed</h3>
          <div className="value" style={{ color: '#ef4444' }}>{stats?.failedQueries || 0}</div>
          <div className="subtext">Errors encountered</div>
        </div>
        <div className="stat-card">
          <h3><Clock size={16} style={{ marginRight: '8px', display: 'inline' }} />Avg. Time</h3>
          <div className="value">{stats?.avgExecutionTime || 0}ms</div>
          <div className="subtext">Per query</div>
        </div>
      </div>

      <div className="table-container">
        <div className="table-header">
          <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={18} />
            Recent Query Activity
          </h3>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Query</th>
                <th>Status</th>
                <th>Time</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {recentQueries.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '40px' }}>
                    No queries yet
                  </td>
                </tr>
              ) : (
                recentQueries.map((query) => (
                  <tr key={query.id}>
                    <td>
                      <div style={{ fontWeight: 500 }}>{query.name}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{query.email}</div>
                    </td>
                    <td style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {query.query_text}
                    </td>
                    <td>
                      <span className={`badge ${query.status === 'success' ? 'badge-success' : 'badge-error'}`}>
                        {query.status}
                      </span>
                    </td>
                    <td>
                      <div>{query.execution_time_ms}ms</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{formatDate(query.timestamp)}</div>
                    </td>
                    <td>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '6px 12px', fontSize: '12px' }}
                        onClick={() => fetchStudentQueries(query.user_id)}
                      >
                        <Eye size={14} />
                        View
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {selectedStudent && (
        <div className="table-container" style={{ marginTop: '20px' }}>
          <div className="table-header">
            <h3 style={{ margin: 0 }}>
              Query History: {selectedStudent.name}
            </h3>
            <button
              className="btn btn-secondary"
              style={{ padding: '6px 12px' }}
              onClick={() => setSelectedStudent(null)}
            >
              Close
            </button>
          </div>
          <div style={{ overflowX: 'auto', maxHeight: '500px', overflowY: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Query</th>
                  <th>Status</th>
                  <th>Time</th>
                  <th>Duration</th>
                </tr>
              </thead>
              <tbody>
                {studentQueries.map((query) => (
                  <tr key={query.id}>
                    <td style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {query.query_text}
                    </td>
                    <td>
                      <span className={`badge ${query.status === 'success' ? 'badge-success' : 'badge-error'}`}>
                        {query.status}
                      </span>
                    </td>
                    <td style={{ fontSize: '12px' }}>{formatDate(query.timestamp)}</td>
                    <td>{query.execution_time_ms}ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminDashboard;
