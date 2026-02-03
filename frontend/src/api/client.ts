import axios from 'axios';

const api = axios.create({
    baseURL: '/api', // Proxy will handle this in dev, or full URL in prod
    headers: {
        'Content-Type': 'application/json',
    },
});

// Track if we're currently refreshing to avoid concurrent refresh attempts
let isRefreshing = false;
let failedQueue: Array<{ resolve: (token: string) => void; reject: (error: any) => void }> = [];

const processQueue = (error: any, token: string | null = null) => {
    failedQueue.forEach((prom) => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token!);
        }
    });
    failedQueue = [];
};

// Add interceptor for JWT token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Add interceptor for 401 Unauthorized responses - try to refresh before logging out
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // If 401 and we haven't already tried refreshing for this request
        if (error.response?.status === 401 && !originalRequest._retry) {
            // Don't try to refresh the refresh-token endpoint itself
            if (originalRequest.url === '/auth/refresh-token') {
                localStorage.removeItem('token');
                if (!window.location.pathname.includes('/login')) {
                    window.location.href = '/login';
                }
                return Promise.reject(error);
            }

            if (isRefreshing) {
                // Queue this request while refresh is in progress
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                }).then((token) => {
                    originalRequest.headers.Authorization = `Bearer ${token}`;
                    return api(originalRequest);
                }).catch((err) => {
                    return Promise.reject(err);
                });
            }

            originalRequest._retry = true;
            isRefreshing = true;

            try {
                // Attempt to refresh the token
                const response = await axios.post('/api/auth/refresh-token', {}, {
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem('token')}`
                    }
                });

                const newToken = response.data.access_token;
                if (newToken) {
                    localStorage.setItem('token', newToken);
                    api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
                    processQueue(null, newToken);

                    // Retry the original request with new token
                    originalRequest.headers.Authorization = `Bearer ${newToken}`;
                    return api(originalRequest);
                }
            } catch (refreshError) {
                processQueue(refreshError, null);
                localStorage.removeItem('token');
                if (!window.location.pathname.includes('/login')) {
                    window.location.href = '/login';
                }
                return Promise.reject(refreshError);
            } finally {
                isRefreshing = false;
            }
        }

        return Promise.reject(error);
    }
);

export default api;
