// Main App with routing
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useWebSocket } from '@/hooks/useWebSocket';
import { Layout } from '@/components/layout/Layout';
import Dashboard from '@/pages/Dashboard';
import Composer from '@/pages/Composer';
import JobDetail from '@/pages/JobDetail';
import Screenplay from '@/pages/Screenplay';
import TestAvatarApi from '@/pages/TestAvatarApi';
import Enhancement from '@/pages/Enhancement';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});

function AppContent() {
  // Initialize WebSocket connection
  useWebSocket();

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/create" element={<Composer />} />
        <Route path="/jobs/:id" element={<JobDetail />} />
        <Route path="/screenplay" element={<Screenplay />} />
        <Route path="/enhancement" element={<Enhancement />} />
        <Route path="/test-avatar-api" element={<TestAvatarApi />} />
        {/* Add more routes as needed */}
      </Routes>
    </Layout>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
