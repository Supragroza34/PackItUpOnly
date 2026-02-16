import React, { createContext, useState, useContext, useEffect } from 'react';
import adminApi from '../services/adminApi';
import { apiFetch } from '../api';

const AuthContext = createContext();

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            const token = localStorage.getItem('access');
            if (token) {
                const userData = await adminApi.getCurrentUser();
                setUser(userData);
            }
        } catch (err) {
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    const login = async (username, password) => {
        try {
            setError(null);
            // Use JWT token endpoint
            const data = await apiFetch('/auth/token/', {
                method: 'POST',
                body: JSON.stringify({ username, password }),
            });
            localStorage.setItem('access', data.access);
            localStorage.setItem('refresh', data.refresh);
            
            // Fetch user data
            const userData = await adminApi.getCurrentUser();
            setUser(userData);
            return { success: true };
        } catch (err) {
            setError(err.message);
            return { success: false, error: err.message };
        }
    };

    const logout = async () => {
        try {
            localStorage.removeItem('access');
            localStorage.removeItem('refresh');
            setUser(null);
            return { success: true };
        } catch (err) {
            setError(err.message);
            return { success: false, error: err.message };
        }
    };

    const value = {
        user,
        loading,
        error,
        login,
        logout,
        isAuthenticated: !!user,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
