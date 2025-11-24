import axios from 'axios';

const api = axios.create({
    baseURL: '/api', // Proxy will handle this in dev, or full URL in prod
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add interceptor for JWT token if we implement auth storage
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export default api;
