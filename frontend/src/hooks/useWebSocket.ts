// WebSocket hook for real-time job updates
import { useEffect } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAppStore } from '@/store';

const WS_URL = import.meta.env.VITE_WS_URL || 'http://localhost:8000';

let socket: Socket | null = null;

export function useWebSocket() {
  const updateJob = useAppStore((state) => state.updateJob);

  useEffect(() => {
    // Connect to WebSocket
    if (!socket) {
      socket = io(WS_URL, {
        path: '/api/v1/ws',
        transports: ['websocket'],
      });

      socket.on('connect', () => {
        console.log('WebSocket connected');
      });

      socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
      });

      socket.on('job_update', (data: { job_id: string; status: string; progress?: number }) => {
        console.log('Job update:', data);
        updateJob(data.job_id, {
          status: data.status as any,
          progress: data.progress,
        });
      });

      socket.on('error', (error: any) => {
        console.error('WebSocket error:', error);
      });
    }

    return () => {
      // Don't disconnect on unmount, keep connection alive
      // socket?.disconnect();
    };
  }, [updateJob]);

  return socket;
}
