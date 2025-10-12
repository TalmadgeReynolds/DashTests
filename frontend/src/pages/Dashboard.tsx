// Dashboard page - Job gallery
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/Button';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const navigate = useNavigate();
  
  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => apiClient.getJobs(),
  });

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Dashboard</h1>
        </div>
        <div className="text-slate-600">Loading jobs...</div>
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Dashboard</h1>
        </div>
        
        <div className="max-w-md mx-auto mt-16 text-center">
          <div className="text-6xl mb-4">📹</div>
          <h2 className="text-xl font-semibold mb-2">No jobs yet</h2>
          <p className="text-slate-600 mb-6">Create your first AI video</p>
          <Button onClick={() => navigate('/create')}>
            Get Started →
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <Button onClick={() => navigate('/create')}>+ New Job</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {jobs.map((job) => (
          <div
            key={job.id}
            className="card cursor-pointer"
            onClick={() => navigate(`/jobs/${job.id}`)}
          >
            <div className="aspect-video bg-slate-200 rounded-lg mb-3" />
            <h3 className="font-semibold mb-2 truncate">Job #{job.id.slice(0, 8)}</h3>
            <div className="text-sm text-slate-600 mb-2">
              {job.engine} • {job.duration || 0}s • ${job.cost?.toFixed(2) || '0.00'}
            </div>
            <div className={`badge-${job.status.toLowerCase()}`}>
              {job.status}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
