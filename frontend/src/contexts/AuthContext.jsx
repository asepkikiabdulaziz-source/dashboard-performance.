import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';
import {
    storageGetItem,
    storageGetJSON,
    storageSetItem,
    storageRemoveItem,
    clearAuthStorage
} from '../utils/storage';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check if user is logged in
        const token = storageGetItem('access_token');
        const savedUser = storageGetJSON('user');

        if (token && savedUser) {
            setUser(savedUser);
        } else if (token && !savedUser) {
            storageRemoveItem('access_token');
        }
        setLoading(false);
    }, []);

    const login = async (email, password) => {
        try {
            const response = await api.post('/auth/login', { email, password });
            const { access_token, user: userData } = response.data;

            storageSetItem('access_token', access_token);
            storageSetItem('user', JSON.stringify(userData));
            setUser(userData);

            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || 'Login failed'
            };
        }
    };

    const logout = () => {
        clearAuthStorage();
        setUser(null);
    };

    const hasPermission = (permissionCode) => {
        if (!user) return false;
        if (user.role === 'super_admin') return true; // Super Admin Bypass
        return user.permissions?.includes(permissionCode);
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, loading, hasPermission }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};
