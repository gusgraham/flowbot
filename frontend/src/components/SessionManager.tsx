
import React, { useEffect, useRef } from 'react';
import api from '../api/client';

const CHECK_INTERVAL_MS = 15 * 60 * 1000; // Check/Refresh every 15 minutes
const ACTIVITY_TIMEOUT_MS = 30 * 60 * 1000; // Activity window consideration

const SessionManager: React.FC = () => {
    const lastActivityRef = useRef<number>(Date.now());

    useEffect(() => {
        // Activity listener
        const updateActivity = () => {
            lastActivityRef.current = Date.now();
        };

        window.addEventListener('mousemove', updateActivity);
        window.addEventListener('keydown', updateActivity);
        window.addEventListener('click', updateActivity);
        window.addEventListener('scroll', updateActivity);

        // Periodic refresh interval
        const intervalId = setInterval(async () => {
            const now = Date.now();
            const timeSinceLastActivity = now - lastActivityRef.current;

            // Only refresh if user has been active recently (within last 30 mins)
            if (timeSinceLastActivity < ACTIVITY_TIMEOUT_MS) {
                try {
                    console.log('SessionManager: Extending session...');
                    const response = await api.post('/auth/refresh-token');
                    const newToken = response.data.access_token;
                    if (newToken) {
                        localStorage.setItem('token', newToken);
                        console.log('SessionManager: Session extended.');
                    }
                } catch (err) {
                    console.error('SessionManager: Failed to refresh token.', err);
                    // If 401, the interceptor effectively handles it, 
                    // but we can optionally do nothing here and let the next real request fail.
                }
            } else {
                console.log('SessionManager: User inactive, skipping refresh.');
            }
        }, CHECK_INTERVAL_MS);

        return () => {
            window.removeEventListener('mousemove', updateActivity);
            window.removeEventListener('keydown', updateActivity);
            window.removeEventListener('click', updateActivity);
            window.removeEventListener('scroll', updateActivity);
            clearInterval(intervalId);
        };
    }, []);

    return null; // Renderless component
};

export default SessionManager;
