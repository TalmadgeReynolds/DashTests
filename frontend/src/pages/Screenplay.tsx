/**
 * Screenplay Page
 * Side-by-side layout with screenplay viewer and job creation interface
 */
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useScreenplays, useScreenplay, useDeleteScreenplay } from '@/hooks/useScreenplay';
import ScreenplayViewer from '@/components/screenplay/ScreenplayViewer';
import ScreenplayUpload from '@/components/screenplay/ScreenplayUpload';
import { apiClient } from '@/lib/api-client';
import type { PromptSharpenRequest, PromptSharpenResponse, PromptVariant } from '@/types';

export default function Screenplay() {
  const [selectedScreenplayId, setSelectedScreenplayId] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [selectedPrompt, setSelectedPrompt] = useState('');
  const [isSharpening, setIsSharpening] = useState(false);
  const [sharpenedPrompts, setSharpenedPrompts] = useState<PromptSharpenResponse | null>(null);
  const [selectedVariant, setSelectedVariant] = useState<PromptVariant | null>(null);
  
  const navigate = useNavigate();
  const { data: screenplayList, isLoading } = useScreenplays();
  const { data: selectedScreenplay } = useScreenplay(selectedScreenplayId || undefined);
  const deleteScreenplayMutation = useDeleteScreenplay();

  const handleUploadSuccess = (screenplayId: string) => {
    setShowUpload(false);
    setSelectedScreenplayId(screenplayId);
  };

  const handleTextSelected = (_selectedText: string, processedPrompt: string) => {
    // Update the prompt with the processed text
    setSelectedPrompt(processedPrompt);
    // If sharpened prompts were visible, clear them when new text is selected
    if (sharpenedPrompts) {
      setSharpenedPrompts(null);
      setSelectedVariant(null);
    }
  };

  const handleSharpenPrompt = useCallback(async () => {
    if (!selectedPrompt) return;
    
    try {
      setIsSharpening(true);
      setSharpenedPrompts(null);
      setSelectedVariant(null);
      
      const request: PromptSharpenRequest = {
        original: selectedPrompt, // Changed from 'prompt' to 'original'
        model: 'both',
        variants: 3, // Changed from 'num_variants' to 'variants'
        temperature: 0.3,
        max_tokens: 300
      };
      
      const response = await apiClient.sharpenPrompt(request);
      setSharpenedPrompts(response);
      
      // Automatically select the best variant (the variants are already sorted by score)
      if (response.variants.length > 0) {
        setSelectedVariant(response.variants[0]);
      }
    } catch (error) {
      console.error('Failed to sharpen prompt:', error);
      alert('Failed to sharpen prompt. Please try again.');
    } finally {
      setIsSharpening(false);
    }
  }, [selectedPrompt]);
  
  const handleSelectVariant = useCallback((variant: PromptVariant) => {
    setSelectedVariant(variant);
    setSelectedPrompt(variant.text);
  }, []);
  
  const handleResetSharpening = useCallback(() => {
    setSharpenedPrompts(null);
    setSelectedVariant(null);
  }, []);

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
              className="w-full h-48 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            
            {selectedPrompt && (
              <div className="mt-4 flex gap-2">
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg flex-1">
                  <p className="text-sm text-blue-900">
                    <strong>Characters:</strong> {selectedPrompt.length}
                  </p>
                  <p className="text-sm text-blue-900 mt-1">
                    <strong>Words:</strong> {selectedPrompt.split(/\s+/).filter(w => w).length}
                  </p>
                </div>
                <button
                  onClick={handleSharpenPrompt}
                  disabled={isSharpening || !selectedPrompt || selectedPrompt.length < 10}
                  className="px-3 py-2 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex-shrink-0 text-sm"
                >
                  {isSharpening ? 'Sharpening...' : '✨ Sharpen'}
                </button>
              </div>
            )}
            
            {/* Prompt Sharpening Results */}
            {sharpenedPrompts && (
              <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-3">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="font-medium text-gray-900">Sharpened Prompts</h3>
                  <button 
                    onClick={handleResetSharpening}
                    className="text-xs text-gray-500 hover:text-gray-700"
                  >
                    Reset
                  </button>
                </div>
                
                <div className="space-y-3 max-h-60 overflow-y-auto">
                  {sharpenedPrompts.variants.map((variant, idx) => (
                    <div 
                      key={idx}
                      onClick={() => handleSelectVariant(variant)}
                      className={`p-2 border rounded-lg cursor-pointer transition-colors ${selectedVariant === variant ? 'bg-blue-100 border-blue-300' : 'bg-white border-gray-200 hover:bg-gray-100'}`}
                    >
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-xs font-medium">
                          {variant.source.toUpperCase()} ({Math.round(variant.score * 100)}%)
                        </span>
                        <span className="text-xs text-gray-500">
                          Similarity: {Math.round(variant.similarity * 100)}%
                        </span>
                      </div>
                      <p className="text-sm text-gray-800">{variant.text}</p>
                      {variant.diff && (
                        <details className="mt-1">
                          <summary className="text-xs text-blue-600 cursor-pointer">View changes</summary>
                          <div className="mt-1 text-xs bg-gray-50 p-2 rounded">
                            <pre className="whitespace-pre-wrap">{variant.diff}</pre>
                          </div>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
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
