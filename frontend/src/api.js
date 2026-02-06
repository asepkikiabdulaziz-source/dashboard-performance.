import axios from 'axios';
import { storageGetItem, clearAuthStorage } from './utils/storage';

// Use environment variable for API URL, fallback to relative path for same-domain deployment
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add auth token
api.interceptors.request.use(
    (config) => {
        const token = storageGetItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Token expired or invalid
            clearAuthStorage();
            if (typeof window !== 'undefined') {
                window.location.reload();
            }
        }
        return Promise.reject(error);
    }
);

export default api;
