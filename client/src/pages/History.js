import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle, XCircle, Copy } from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchHistory();
    fetchStats();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API_URL}/history`);
      setHistory(response.data.history);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_URL}/history/stats`);
      setStats(response.data.stats);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const copyQuery = (query) => {
    navigator.clipboard.writeText(query);
  };

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const formatDuration = (ms) => {
    if (!ms) return '-';
    return `${ms}ms`;
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
        <h1>Query History</h1>
        <p>View your past SQL query executions</p>
      </div>

      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Queries</h3>
            <div className="value">{stats.total_queries || 0}</div>
            <div className="subtext">All time</div>
          </div>
          <div className="stat-card">
            <h3>Successful</h3>
            <div className="value" style={{ color: '#10b981' }}>{stats.successful_queries || 0}</div>
            <div className="subtext">Completed queries</div>
          </div>
          <div className="stat-card">
            <h3>Failed</h3>
            <div className="value" style={{ color: '#ef4444' }}>{stats.failed_queries || 0}</div>
            <div className="subtext">Errors encountered</div>
          </div>
          <div className="stat-card">
            <h3>Avg. Time</h3>
            <div className="value">{Math.round(stats.avg_execution_time || 0)}ms</div>
            <div className="subtext">Per query</div>
          </div>
        </div>
      )}

      <div className="history-list">
        <div className="table-header">
          <h3 style={{ margin: 0 }}>Recent Queries</h3>
        </div>

        {history.length === 0 ? (
          <div className="results-empty">
            No queries executed yet. Start writing SQL in the editor!
          </div>
        ) : (
          history.map((item) => (
            <div key={item.id} className="history-item">
              <div className="history-query">{item.query_text}</div>
              <div className="history-meta">
                <span className={item.status === 'success' ? 'status-success' : 'status-error'}>
                  {item.status === 'success' ? <CheckCircle size={14} /> : <XCircle size={14} />}
                  {' '}{item.status}
                </span>
                <span><Clock size={14} /> {formatDuration(item.execution_time_ms)}</span>
                {item.rows_affected > 0 && (
                  <span>{item.rows_affected} row(s)</span>
                )}
                <span>{formatDate(item.timestamp)}</span>
                <button
                  onClick={() => copyQuery(item.query_text)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px' }}
                  title="Copy query"
                >
                  <Copy size={14} />
                </button>
              </div>
              {item.error_message && (
                <div style={{ color: 'var(--error)', fontSize: '12px', marginTop: '8px' }}>
                  Error: {item.error_message}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default History;
