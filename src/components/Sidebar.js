import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  Database, 
  History, 
  LayoutDashboard, 
  LogOut, 
  Code2,
  Key
} from 'lucide-react';

function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <Database size={28} color="#667eea" />
        <h2>SQL Lab</h2>
      </div>
      
      <nav className="nav-links">
        <NavLink to="/editor" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
          <Code2 size={20} />
          <span>SQL Editor</span>
        </NavLink>
        
        <NavLink to="/history" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
          <History size={20} />
          <span>Query History</span>
        </NavLink>

        {user?.role === 'admin' && (
          <>
            <NavLink to="/admin" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              <LayoutDashboard size={20} />
              <span>Admin Dashboard</span>
            </NavLink>
            <NavLink to="/admin-otps" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              <Key size={20} />
              <span>View OTPs</span>
            </NavLink>
          </>
        )}
      </nav>

      <div style={{ marginTop: 'auto', paddingTop: '20px', borderTop: '1px solid var(--border)' }}>
        <div style={{ padding: '12px 16px', marginBottom: '12px' }}>
          <div style={{ fontWeight: 600, marginBottom: '4px' }}>{user?.name}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{user?.email}</div>
          <div style={{ fontSize: '11px', color: 'var(--primary)', marginTop: '4px', textTransform: 'capitalize' }}>
            {user?.role}
          </div>
        </div>
        <button className="nav-link" onClick={handleLogout} style={{ width: '100%', border: 'none', cursor: 'pointer' }}>
          <LogOut size={20} />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;
