// Job detail page
import { useParams } from 'react-router-dom';

export default function JobDetail() {
  const { id } = useParams();
  
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Job Detail</h1>
      <div className="card">
        <p className="text-slate-600">Job ID: {id}</p>
        <p className="text-slate-600 mt-2">Detail view coming soon...</p>
      </div>
    </div>
  );
}
