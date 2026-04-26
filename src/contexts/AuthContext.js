import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'https://sql-lab-new.onrender.com/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchProfile();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API_URL}/auth/profile`);
      setUser(response.data.user);
    } catch (error) {
      localStorage.removeItem('token');
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const response = await axios.post(`${API_URL}/auth/login`, { email, password });
    const { token, user: userData } = response.data;
    localStorage.setItem('token', token);
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    setUser(userData);
    return { success: true };
  };

  const signup = async (name, email, password) => {
    const response = await axios.post(`${API_URL}/auth/signup`, { name, email, password });
    const { token, user: userData } = response.data;
    localStorage.setItem('token', token);
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    setUser(userData);
    return { success: true };
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  const saveQueryHistory = async (query, results) => {
    localStorage.setItem('query_history', JSON.stringify([
      { query, results, timestamp: new Date().toISOString() },
      ...JSON.parse(localStorage.getItem('query_history') || '[]').slice(0, 49)
    ]));
  };

  const getQueryHistory = async () => {
    return JSON.parse(localStorage.getItem('query_history') || '[]');
  };

  const getAllUsers = async () => {
    return [];
  };

  const makeAdmin = async (uid) => {};

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout, saveQueryHistory, getQueryHistory, getAllUsers, makeAdmin }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}