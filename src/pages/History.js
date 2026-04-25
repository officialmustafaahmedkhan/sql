import React, { useState, useEffect } from 'react';
import { Clock, Copy, Trash2, Play } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

function History({ onLoadQuery }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const { getQueryHistory } = useAuth();

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await getQueryHistory();
      setHistory(data.reverse());
    } catch (err) {
      console.error('Failed to fetch history:', err);
    } finally {
      setLoading(false);
    }
  };

  const copyQuery = (query) => {
    navigator.clipboard.writeText(query);
  };

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
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
        <p>View your past SQL queries from Firebase</p>
      </div>

      <div className="history-list">
        <div className="table-header">
          <h3 style={{ margin: 0 }}>Recent Queries ({history.length})</h3>
        </div>

        {history.length === 0 ? (
          <div className="results-empty">
            No queries yet. Run SQL in the editor!
          </div>
        ) : (
          history.map((item, index) => (
            <div key={index} className="history-item">
              <div className="history-query">{item.query}</div>
              <div className="history-meta">
                <span><Clock size={14} /> {formatDate(item.timestamp)}</span>
                <button onClick={() => copyQuery(item.query)} title="Copy" style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px' }}>
                  <Copy size={14} />
                </button>
                <button onClick={() => onLoadQuery && onLoadQuery(item.query)} title="Run again" style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px', color: 'var(--success)' }}>
                  <Play size={14} />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default History;