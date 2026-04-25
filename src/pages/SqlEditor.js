import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { Play, Download, AlertCircle, CheckCircle, Clock, BookOpen } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function SqlEditor() {
  const [query, setQuery] = useState('SELECT * FROM users;');
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [executionInfo, setExecutionInfo] = useState(null);
  const [tables, setTables] = useState([]);
  const [showSchema, setShowSchema] = useState(false);
  const [schema, setSchema] = useState(null);
  const [practices, setPractices] = useState([]);
  const [showPractices, setShowPractices] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const { saveQueryHistory, user } = useAuth();

  useEffect(() => {
    setDarkMode(document.documentElement.classList.contains('dark'));
    fetchTables();
    fetchPractices();
  }, []);

  const fetchTables = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/tables`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTables(response.data.tables || []);
    } catch (err) {
      console.error('Tables fetch error:', err);
    }
  };

  const fetchPractices = async () => {
    try {
      const response = await axios.get(`${API_URL}/practices`);
      setPractices(response.data.practices || []);
    } catch (err) {
      console.error('Practices fetch error:', err);
    }
  };

  const fetchSchema = async (tableName) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/schema/${tableName}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSchema({ table: tableName, columns: response.data.columns });
    } catch (err) {
      console.error('Schema fetch error:', err);
    }
  };

  const handleEditorChange = (value) => {
    setQuery(value || '');
  };

  const handleRunQuery = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResults(null);
    setExecutionInfo(null);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/query/execute`,
        { query },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setResults(response.data);
      setExecutionInfo({
        queryCount: response.data.queryCount,
        executionTime: response.data.executionTime,
        message: response.data.message
      });
      
      // Save to Firebase history
      await saveQueryHistory(query, response.data.message);
    } catch (err) {
      console.error('Query error:', err.response?.data);
      setError(err.response?.data?.error || err.response?.data?.message || 'Query execution failed');
    } finally {
      setLoading(false);
    }
  };

  const loadPractice = (practice) => {
    setQuery(practice.query);
  };

  const exportToCsv = () => {
    if (!results?.results) return;
    const allData = results.results.filter(r => r.results && r.results.length > 0).flatMap(r => r.results);
    if (allData.length === 0) return;

    const headers = Object.keys(allData[0]);
    const csvContent = [headers.join(','), ...allData.map(row => headers.map(h => {
      const val = row[h];
      if (val === null || val === undefined) return '';
      const str = String(val).replace(/"/g, '""');
      return str.includes(',') ? `"${str}"` : str;
    }).join(','))].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `query_results_${Date.now()}.csv`;
    link.click();
  };

  return (
    <div>
      <div className="page-header">
        <h1>SQL Editor</h1>
        <p>Execute SQL queries on MySQL (XAMPP 3306)</p>
      </div>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <button className="btn btn-secondary" onClick={() => setShowSchema(!showSchema)}>
          <BookOpen size={16} /> Schema
        </button>
        <button className="btn btn-secondary" onClick={() => setShowPractices(!showPractices)}>
          <Play size={16} /> Practice
        </button>
        {user?.role === 'admin' && (
          <span style={{ color: 'var(--success)', fontSize: '12px', alignSelf: 'center', marginLeft: '8px' }}>
            Admin: DROP/GRANT/REVOKE allowed
          </span>
        )}
      </div>

      {showSchema && (
        <div className="results-container" style={{ marginBottom: '16px' }}>
          <div className="results-header">
            <strong>Database Schema</strong>
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px' }}>
            {tables.map(t => (
              <button key={t} onClick={() => fetchSchema(t)} className="btn btn-secondary" style={{ fontSize: '12px' }}>
                {t}
              </button>
            ))}
          </div>
          {schema && (
            <table className="results-table">
              <thead>
                <tr>
                  <th>Column</th>
                  <th>Type</th>
                  <th>Null</th>
                  <th>Key</th>
                </tr>
              </thead>
              <tbody>
                {schema.columns.map((col, i) => (
                  <tr key={i}>
                    <td><strong>{col.Field}</strong></td>
                    <td>{col.Type}</td>
                    <td>{col.Null}</td>
                    <td>{col.Key}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {showPractices && (
        <div className="results-container" style={{ marginBottom: '16px' }}>
          <div className="results-header"><strong>Practice Exercises</strong></div>
          {practices.map(p => (
            <div key={p.id} style={{ padding: '12px', borderBottom: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <strong>{p.title}</strong>
                  <span style={{ marginLeft: '8px', fontSize: '12px', color: p.difficulty === 'Easy' ? 'var(--success)' : p.difficulty === 'Medium' ? 'var(--warning)' : 'var(--error)' }}>
                    {p.difficulty}
                  </span>
                </div>
                <button onClick={() => loadPractice(p)} className="btn btn-primary" style={{ fontSize: '12px', padding: '4px 12px' }}>
                  Load
                </button>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '4px 0' }}>{p.description}</p>
            </div>
          ))}
        </div>
      )}

      <div className="editor-container">
        <div className="editor-toolbar">
          <div className="editor-toolbar-left">
            <span style={{ fontWeight: 600, fontSize: '14px' }}>Query Editor</span>
          </div>
          <div className="editor-toolbar-right">
            <button className="btn btn-run" onClick={handleRunQuery} disabled={loading || !query.trim()}>
              <Play size={16} />
              {loading ? 'Running...' : 'Run Query'}
            </button>
          </div>
        </div>

        <div className="monaco-wrapper">
          <Editor height="100%" language="sql" theme={darkMode ? 'vs-dark' : 'light'}
            value={query} onChange={handleEditorChange}
            options={{ minimap: { enabled: false }, fontSize: 14, lineNumbers: 'on', wordWrap: 'on' }}
          />
        </div>
      </div>

      {error && (
        <div className="results-container">
          <div style={{ color: 'var(--error)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={20} />
            <strong>Error</strong>
          </div>
          <div className="results-empty" style={{ color: 'var(--error)' }}>{error}</div>
        </div>
      )}

      {results && (
        <div className="results-container">
          <div className="results-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              {results.success ? <CheckCircle size={20} color="var(--success)" /> : <AlertCircle size={20} color="var(--warning)" />}
              <span style={{ fontWeight: 600 }}>{results.success ? 'Success' : 'Partial Success'}</span>
              {executionInfo && (
                <span><Clock size={14} /> {executionInfo.executionTime}</span>
              )}
            </div>
            {results.results?.some(r => r.results && r.results.length > 0) && (
              <button className="btn btn-secondary" onClick={exportToCsv}>
                <Download size={16} /> Export CSV
              </button>
            )}
          </div>

          {results.results?.map((result, index) => (
            <div key={index} style={{ marginBottom: '20px', borderBottom: '1px solid var(--border)', padding: '16px' }}>
              <div style={{ marginBottom: '8px' }}>
                <strong>Query {index + 1}:</strong>
                <code style={{ marginLeft: '8px', fontSize: '12px', background: 'var(--bg-primary)', padding: '4px 8px', borderRadius: '4px' }}>
                  {result.query.substring(0, 100)}{result.query.length > 100 ? '...' : ''}
                </code>
                <span style={{ marginLeft: '8px', fontSize: '12px', color: result.success ? 'var(--success)' : 'var(--error)' }}>
                  ({result.queryType})
                </span>
              </div>
              
              {result.success && result.results && result.results.length > 0 && (
                <div style={{ overflowX: 'auto' }}>
                  <table className="results-table">
                    <thead>
                      <tr>{Object.keys(result.results[0]).map(key => <th key={key}>{key}</th>)}</tr>
                    </thead>
                    <tbody>
                      {result.results.map((row, idx) => (
                        <tr key={idx}>
                          {Object.values(row).map((val, i) => (
                            <td key={i}>{val === null ? <span style={{ color: 'var(--text-light)' }}>NULL</span> : String(val)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              
              {result.success && !result.results && (
                <div className="results-empty">{result.rowsAffected} row(s) affected</div>
              )}

              {result.error && <div style={{ color: 'var(--error)', fontSize: '14px' }}>Error: {result.error}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default SqlEditor;