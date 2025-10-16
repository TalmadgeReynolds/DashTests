/**
 * Simple test script to verify avatar API functionality
 * Run with: npm run dev
 * Then visit: http://localhost:5173/test-avatar-api
 */

import { useEffect, useState } from 'react';
import { avatarApi } from '@/lib/avatar-api';

export default function TestAvatarApi() {
  const [loading, setLoading] = useState(true);
  const [avatars, setAvatars] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const result = await avatarApi.listAvatars();
        console.log('Avatars:', result);
        setAvatars(result.avatars || []);
        setError(null);
      } catch (err) {
        console.error('Error fetching avatars:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }
    
    fetchData();
  }, []);

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Avatar API Test</h1>
      
      {loading ? (
        <div className="text-gray-600">Loading avatars...</div>
      ) : error ? (
        <div className="p-4 bg-red-50 border border-red-300 rounded-lg">
          <h2 className="font-semibold text-red-700">Error:</h2>
          <p className="text-red-800">{error}</p>
          <div className="mt-4 p-3 bg-gray-100 rounded text-sm">
            <p className="font-medium">Troubleshooting:</p>
            <ul className="list-disc pl-5 mt-2 space-y-1">
              <li>Make sure the backend server is running</li>
              <li>Check that the avatar routes are properly implemented</li>
              <li>Verify Heygen API credentials are configured</li>
              <li>Check browser console for more detailed error information</li>
            </ul>
          </div>
        </div>
      ) : avatars.length === 0 ? (
        <div className="p-4 bg-yellow-50 border border-yellow-300 rounded-lg">
          <p className="text-yellow-800">
            No avatars found. The API is working but no avatars exist yet.
          </p>
          <button
            className="mt-3 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            onClick={() => {
              // This would normally go to the avatar creation page
              alert('In a real app, this would redirect to the avatar creation UI');
            }}
          >
            Create New Avatar
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-green-700">
            ✅ Successfully connected to avatar API and found {avatars.length} avatar(s)
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {avatars.map((avatar, i) => (
              <div key={i} className="border border-gray-200 rounded-lg p-4 shadow-sm">
                <div className="font-medium">{avatar.name || `Avatar ${i+1}`}</div>
                <div className="text-sm text-gray-600">ID: {avatar.avatar_id}</div>
                {avatar.image_url && (
                  <img 
                    src={avatar.image_url} 
                    alt={avatar.name || `Avatar ${i+1}`}
                    className="mt-3 w-32 h-32 object-cover rounded-lg"
                  />
                )}
                <div className="mt-2 text-xs text-gray-500">
                  Created: {new Date(avatar.created_at || Date.now()).toLocaleString()}
                </div>
                <pre className="mt-3 text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                  {JSON.stringify(avatar, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}