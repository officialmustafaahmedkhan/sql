import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { Play, Download, AlertCircle, CheckCircle, Clock, Rows } from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function SqlEditor() {
  const [query, setQuery] = useState(`SELECT * FROM students;

INSERT INTO students (first_name, last_name, email, department, enrollment_year, gpa)
VALUES ('John', 'Doe', 'john@iobm.edu.pk', 'Computer Science', 2024, 3.75);

SELECT * FROM students;`);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [executionInfo, setExecutionInfo] = useState(null);
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    setDarkMode(document.documentElement.classList.contains('dark'));
    // Set Authorization header from localStorage
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, []);

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
      const response = await axios.post(`${API_URL}/query/execute`, { query });
      setResults(response.data);
      setExecutionInfo({
        queryCount: response.data.queryCount,
        executionTime: response.data.executionTime,
        message: response.data.message
      });
    } catch (err) {
      console.error('Query error:', err.response?.data);
      setError(err.response?.data?.error || err.response?.data?.message || 'Query execution failed');
    } finally {
      setLoading(false);
    }
  };

  const exportToCsv = () => {
    if (!results?.results || results.results.length === 0) return;
    
    const allData = results.results
      .filter(r => r.results && r.results.length > 0)
      .flatMap(r => r.results);
    
    if (allData.length === 0) return;

    const headers = Object.keys(allData[0]);
    const csvContent = [
      headers.join(','),
      ...allData.map(row =>
        headers.map(h => {
          const val = row[h];
          if (val === null || val === undefined) return '';
          const str = String(val).replace(/"/g, '""');
          return str.includes(',') || str.includes('"') || str.includes('\n') ? `"${str}"` : str;
        }).join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `query_results_${Date.now()}.csv`;
    link.click();
  };

  return (
    <div>
      <div className="page-header">
        <h1>SQL Editor</h1>
        <p>Write and execute SQL queries against your database</p>
      </div>

      <div className="editor-container">
        <div className="editor-toolbar">
          <div className="editor-toolbar-left">
            <span style={{ fontWeight: 600, fontSize: '14px' }}>Query Editor</span>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              (Multiple queries supported - separate with ;)
            </span>
          </div>
          <div className="editor-toolbar-right">
            <button
              className="btn btn-run"
              onClick={handleRunQuery}
              disabled={loading || !query.trim()}
            >
              <Play size={16} />
              {loading ? 'Running...' : 'Run Query'}
            </button>
          </div>
        </div>

        <div className="monaco-wrapper">
          <Editor
            height="100%"
            language="sql"
            theme={darkMode ? 'vs-dark' : 'light'}
            value={query}
            onChange={handleEditorChange}
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              lineNumbers: 'on',
              scrollBeyondLastLine: false,
              automaticLayout: true,
              tabSize: 2,
              wordWrap: 'on'
            }}
          />
        </div>
      </div>

      {error && (
        <div className="results-container">
          <div className="results-header" style={{ color: 'var(--error)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertCircle size={20} />
              <span style={{ fontWeight: 600 }}>Error</span>
            </div>
          </div>
          <div className="results-empty" style={{ color: 'var(--error)' }}>
            {error}
          </div>
        </div>
      )}

      {results && (
        <div className="results-container">
          <div className="results-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              {results.success ? (
                <CheckCircle size={20} color="var(--success)" />
              ) : (
                <AlertCircle size={20} color="var(--warning)" />
              )}
              <span style={{ fontWeight: 600 }}>{results.success ? 'Success' : 'Partial Success'}</span>
              {executionInfo && (
                <div className="query-info" style={{ background: 'transparent', padding: 0 }}>
                  <span><Clock size={14} /> {executionInfo.executionTime}</span>
                  <span><Rows size={14} /> {executionInfo.queryCount} query(s)</span>
                </div>
              )}
            </div>
            {results.results && results.results.some(r => r.results && r.results.length > 0) && (
              <button className="btn btn-secondary" onClick={exportToCsv}>
                <Download size={16} />
                Export CSV
              </button>
            )}
          </div>

          {results.results && results.results.map((result, index) => (
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
                      <tr>
                        {Object.keys(result.results[0]).map(key => (
                          <th key={key}>{key}</th>
                        ))}
                      </tr>
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
                <div className="results-empty">
                  {result.rowsAffected} row(s) affected
                </div>
              )}

              {result.error && (
                <div style={{ color: 'var(--error)', fontSize: '14px' }}>
                  Error: {result.error}
                </div>
              )}
            </div>
          ))}

          {results.errors && results.errors.length > 0 && (
            <div style={{ padding: '16px', background: '#fef2f2', borderRadius: '8px' }}>
              <h4 style={{ color: 'var(--error)', marginBottom: '8px' }}>Errors:</h4>
              {results.errors.map((err, idx) => (
                <div key={idx} style={{ marginBottom: '8px' }}>
                  <strong>Query:</strong> {err.query}<br />
                  <strong>Error:</strong> {err.error}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default SqlEditor;
