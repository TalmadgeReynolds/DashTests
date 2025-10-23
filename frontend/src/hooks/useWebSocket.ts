// WebSocket hook for real-time job updates
import { useEffect } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAppStore } from '@/store';

// Configuration options
const WS_URL = import.meta.env.VITE_WS_URL || 'http://localhost:8000';
const MAX_RETRY_ATTEMPTS = 3;
const WEBSOCKETS_ENABLED = import.meta.env.VITE_ENABLE_WEBSOCKETS !== 'false';

// Module state
let socket: Socket | null = null;
let retryAttempts = 0;
let websocketsAvailable = true;

export function useWebSocket() {
  const updateJob = useAppStore((state) => state.updateJob);

  useEffect(() => {
    // Skip connection if WebSockets are disabled or have failed too many times
    if (!WEBSOCKETS_ENABLED || !websocketsAvailable) {
      if (!websocketsAvailable && retryAttempts >= MAX_RETRY_ATTEMPTS) {
        console.info('WebSockets unavailable after multiple attempts. Real-time updates disabled.');
      }
      return;
    }

    // Connect to WebSocket if not already connected
    if (!socket) {
      try {
        socket = io(WS_URL, {
          path: '/api/v1/ws',
          transports: ['websocket'],
          reconnectionAttempts: MAX_RETRY_ATTEMPTS,
        });

        socket.on('connect', () => {
          console.log('WebSocket connected');
          retryAttempts = 0; // Reset retry counter on successful connection
        });

        socket.on('disconnect', () => {
          console.log('WebSocket disconnected');
        });

        socket.on('connect_error', (error) => {
          retryAttempts++;
          console.warn(`WebSocket connection error (attempt ${retryAttempts}/${MAX_RETRY_ATTEMPTS}):`, error.message);
          
          if (retryAttempts >= MAX_RETRY_ATTEMPTS) {
            websocketsAvailable = false;
            console.info('WebSocket connection failed too many times. Disabling real-time updates.');
            if (socket) {
              socket.disconnect();
              socket = null;
            }
          }
        });

        socket.on('job_update', (data: { job_id: string; status: string; progress?: number }) => {
          console.log('Job update:', data);
          updateJob(data.job_id, {
            status: data.status as any,
            progress: data.progress,
          });
        });
      } catch (error) {
        console.error('Error initializing WebSocket:', error);
        websocketsAvailable = false;
      }
    }

    // Cleanup on unmount
    return () => {
      // We don't disconnect on component unmount to maintain connection across page navigation
    };
  }, [updateJob]);

  return socket;
}
