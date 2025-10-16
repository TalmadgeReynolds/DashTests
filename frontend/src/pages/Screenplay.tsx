/**
 * Screenplay Page
 * Side-by-side layout with screenplay viewer and job creation interface
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useScreenplays, useScreenplay, useDeleteScreenplay } from '@/hooks/useScreenplay';
import ScreenplayViewer from '@/components/screenplay/ScreenplayViewer';
import ScreenplayUpload from '@/components/screenplay/ScreenplayUpload';

export default function Screenplay() {
  const [selectedScreenplayId, setSelectedScreenplayId] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [selectedPrompt, setSelectedPrompt] = useState('');
  
  const navigate = useNavigate();
  const { data: screenplayList, isLoading } = useScreenplays();
  const { data: selectedScreenplay } = useScreenplay(selectedScreenplayId || undefined);
  const deleteScreenplayMutation = useDeleteScreenplay();

  const handleUploadSuccess = (screenplayId: string) => {
    setShowUpload(false);
    setSelectedScreenplayId(screenplayId);
  };

  const handleTextSelected = (_: string, processedPrompt: string) => {
    setSelectedPrompt(processedPrompt);
  };

  const handleCreateJob = () => {
    if (selectedPrompt) {
      // Navigate to job creation page with the prompt pre-filled
      navigate('/create', { state: { prompt: selectedPrompt } });
    }
  };

  const handleDeleteScreenplay = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this screenplay?')) {
      try {
        await deleteScreenplayMutation.mutateAsync(id);
        if (selectedScreenplayId === id) {
          setSelectedScreenplayId(null);
          setSelectedPrompt('');
        }
      } catch (error) {
        console.error('Failed to delete screenplay:', error);
        alert('Failed to delete screenplay. Please try again.');
      }
    }
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Screenplay Studio</h1>
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            {showUpload ? 'Cancel Upload' : 'Upload Screenplay'}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Screenplay List */}
        <div className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
          <div className="p-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Your Screenplays</h2>
            
            {isLoading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : screenplayList?.screenplays.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No screenplays yet</p>
                <p className="text-sm mt-2">Upload your first screenplay to get started</p>
              </div>
            ) : (
              <div className="space-y-2">
                {screenplayList?.screenplays.map((screenplay) => (
                  <div
                    key={screenplay.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedScreenplayId === screenplay.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div
                      onClick={() => {
                        setSelectedScreenplayId(screenplay.id);
                        setShowUpload(false);
                      }}
                      className="flex-1"
                    >
                      <h3 className="font-medium text-gray-900 truncate">
                        {screenplay.title}
                      </h3>
                      <p className="text-xs text-gray-500 mt-1">
                        {screenplay.page_count ? `${screenplay.page_count} pages` : 'Processing...'}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(screenplay.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteScreenplay(screenplay.id);
                      }}
                      className="mt-2 w-full px-2 py-1 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 rounded"
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Center - Screenplay Viewer or Upload */}
        <div className="flex-1 bg-gray-50 overflow-hidden">
          {showUpload ? (
            <div className="h-full overflow-y-auto">
              <ScreenplayUpload onUploadSuccess={handleUploadSuccess} />
            </div>
          ) : selectedScreenplay ? (
            <ScreenplayViewer
              screenplay={selectedScreenplay}
              onTextSelected={handleTextSelected}
            />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <svg
                  className="w-24 h-24 mx-auto text-gray-300 mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <p className="text-lg">Select a screenplay to view</p>
                <p className="text-sm mt-2">or upload a new one to get started</p>
              </div>
            </div>
          )}
        </div>

        {/* Right Panel - Prompt Editor */}
        <div className="w-96 bg-white border-l border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Prompt Editor</h2>
            <p className="text-sm text-gray-500 mt-1">
              Select text from the screenplay to create a prompt
            </p>
          </div>
          
          <div className="flex-1 p-4 overflow-y-auto">
            <textarea
              value={selectedPrompt}
              onChange={(e) => setSelectedPrompt(e.target.value)}
              placeholder="Select text from your screenplay, or type your prompt here..."
              className="w-full h-64 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            
            {selectedPrompt && (
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-900">
                  <strong>Characters:</strong> {selectedPrompt.length}
                </p>
                <p className="text-sm text-blue-900 mt-1">
                  <strong>Words:</strong> {selectedPrompt.split(/\s+/).filter(w => w).length}
                </p>
              </div>
            )}
          </div>
          
          <div className="p-4 border-t border-gray-200">
            <button
              onClick={handleCreateJob}
              disabled={!selectedPrompt}
              className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              Create Job with Prompt
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
