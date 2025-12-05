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

// Add interceptor for 401 Unauthorized responses
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            localStorage.removeItem('token');
            // Only redirect if not already on login page to avoid loops
            if (!window.location.pathname.includes('/login')) {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default api;
