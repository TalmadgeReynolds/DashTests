/**
 * Screenplay Page
 * Side-by-side layout with screenplay viewer and job creation interface
 */
import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useScreenplays, useScreenplay, useDeleteScreenplay } from '@/hooks/useScreenplay';
import ScreenplayViewer from '@/components/screenplay/ScreenplayViewer';
import ScreenplayUpload from '@/components/screenplay/ScreenplayUpload';
import PromptSharpener from '@/components/PromptSharpener';

export default function Screenplay() {
  const [selectedScreenplayId, setSelectedScreenplayId] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [selectedPrompt, setSelectedPrompt] = useState('');
  
  // Panel resize state
  const [leftPanelWidth, setLeftPanelWidth] = useState<number>(200); // sidebar width in pixels
  const [centerPanelWidth, setCenterPanelWidth] = useState<number>(60); // center panel width as percentage
  const [isDraggingLeft, setIsDraggingLeft] = useState(false);
  const [isDraggingRight, setIsDraggingRight] = useState(false);
  const [startX, setStartX] = useState(0);
  const [startLeftWidth, setStartLeftWidth] = useState(0);
  const [startCenterWidth, setStartCenterWidth] = useState(0);
  
  const navigate = useNavigate();
  const { data: screenplayList, isLoading, error } = useScreenplays();
  const { data: selectedScreenplay } = useScreenplay(selectedScreenplayId || undefined);
  const deleteScreenplayMutation = useDeleteScreenplay();
  
  // Debug logging
  console.log('Screenplay page state:', { isLoading, hasData: !!screenplayList, error });

  const handleUploadSuccess = (screenplayId: string) => {
    setShowUpload(false);
    setSelectedScreenplayId(screenplayId);
  };

  const handleTextSelected = (_selectedText: string, processedPrompt: string) => {
    // Update the prompt with the processed text
    setSelectedPrompt(processedPrompt);
  };

  const handleCreateJob = () => {
    if (selectedPrompt) {
      // Navigate to job creation page with the prompt pre-filled
      navigate('/create', { state: { prompt: selectedPrompt } });
    }
  };

  // Handle mouse movement when dragging any divider
  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (isDraggingLeft) {
      const newWidth = Math.max(200, Math.min(400, startLeftWidth + (e.clientX - startX)));
      setLeftPanelWidth(newWidth);
    } else if (isDraggingRight) {
      // Calculate new center panel width as a percentage
      const containerWidth = window.innerWidth - leftPanelWidth;
      const delta = e.clientX - startX;
      const deltaPercent = (delta / containerWidth) * 100;
      const newCenterWidth = Math.max(30, Math.min(80, startCenterWidth + deltaPercent));
      setCenterPanelWidth(newCenterWidth);
    }
  }, [isDraggingLeft, isDraggingRight, startLeftWidth, startCenterWidth, startX, leftPanelWidth]);
  
  // Handle mouse up to stop dragging
  const handleMouseUp = useCallback(() => {
    setIsDraggingLeft(false);
    setIsDraggingRight(false);
  }, []);
  
  // Add and remove event listeners for dragging
  useEffect(() => {
    if (isDraggingLeft || isDraggingRight) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      // Set cursor style on body during drag
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      // Reset cursor style
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isDraggingLeft, isDraggingRight, handleMouseMove, handleMouseUp]);

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
  
  // Handle start of dragging the left divider (between screenplay list and PDF viewer)
  const handleLeftDividerMouseDown = (e: React.MouseEvent) => {
    setIsDraggingLeft(true);
    setStartX(e.clientX);
    setStartLeftWidth(leftPanelWidth);
    e.preventDefault();
  };
  
  // Handle start of dragging the right divider (between PDF viewer and prompt editor)
  const handleRightDividerMouseDown = (e: React.MouseEvent) => {
    setIsDraggingRight(true);
    setStartX(e.clientX);
    setStartCenterWidth(centerPanelWidth);
    e.preventDefault();
  };
  
  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <h1 className="text-lg font-semibold text-gray-900">Screenplay Generator</h1>
        </div>
      </div>
      
      {/* Main Content - Resizable Panels */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Screenplay List */}
        <div 
          className="bg-white border-r border-gray-200 overflow-y-auto" 
          style={{ width: `${leftPanelWidth}px` }}
        >
          <div className="p-4 border-b border-gray-200">
            <button
              onClick={() => setShowUpload(true)}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
            >
              Upload Screenplay
            </button>
          </div>
          
          <div className="p-2">
            <h2 className="text-lg font-medium text-gray-900 px-2 mb-3">Screenplays</h2>
            {error ? (
              <div className="p-4 text-center text-red-600">
                Error loading screenplays: {error instanceof Error ? error.message : 'Unknown error'}
              </div>
            ) : isLoading ? (
              <div className="p-4 text-center">Loading...</div>
            ) : screenplayList && screenplayList.screenplays.length > 0 ? (
              <ul className="space-y-1">
                {screenplayList.screenplays.map(screenplay => (
                  <li key={screenplay.id}>
                    <button
                      onClick={() => setSelectedScreenplayId(screenplay.id)}
                      className={`w-full text-left px-3 py-2 rounded-md ${
                        selectedScreenplayId === screenplay.id
                          ? 'bg-blue-100 text-blue-900'
                          : 'hover:bg-gray-100'
                      }`}
                    >
                      <div className="flex justify-between items-center">
                        <span className="font-medium truncate">{screenplay.title}</span>
                        <div
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteScreenplay(screenplay.id);
                          }}
                          className="text-gray-400 hover:text-red-600 ml-2 cursor-pointer"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                            <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                          </svg>
                        </div>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="p-4 text-center text-gray-500">
                No screenplays found
              </div>
            )}            
          </div>
        </div>
        
        {/* Draggable divider between screenplay list and PDF viewer */}
        <div 
          className="w-1 bg-gray-300 hover:bg-blue-500 hover:w-1.5 cursor-col-resize transition-colors relative z-10"
          onMouseDown={handleLeftDividerMouseDown}
        >
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-6 h-10 flex items-center justify-center">
            <div className="h-8 w-0.5 bg-gray-400 rounded-full"></div>
          </div>
        </div>

        {/* Main Content - PDF Viewer */}
        <div 
          className="overflow-hidden flex flex-col" 
          style={{ width: `calc((100% - ${leftPanelWidth}px) * ${centerPanelWidth/100})` }}
        >
          {showUpload ? (
            <ScreenplayUpload onUploadSuccess={handleUploadSuccess} onCancel={() => setShowUpload(false)} />
          ) : selectedScreenplayId && selectedScreenplay ? (
            <ScreenplayViewer 
              screenplay={selectedScreenplay} 
              onTextSelected={handleTextSelected}
            />
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center p-6 max-w-md">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No screenplay selected</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Choose an existing screenplay from the sidebar or upload a new one to get started.
                </p>
              </div>
            </div>
          )}
        </div>
        
        {/* Draggable divider between PDF viewer and prompt editor */}
        <div 
          className="w-1 bg-gray-300 hover:bg-blue-500 hover:w-1.5 cursor-col-resize transition-colors relative z-10"
          onMouseDown={handleRightDividerMouseDown}
        >
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-6 h-10 flex items-center justify-center">
            <div className="h-8 w-0.5 bg-gray-400 rounded-full"></div>
          </div>
        </div>

        {/* Right Panel - Prompt Editor */}
        <div className="bg-white border-l border-gray-200 flex flex-col flex-1">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">✨ Prompt Sharpener</h2>
            <p className="text-xs text-gray-500 mt-1">Select text from screenplay or type below, then enhance with AI</p>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4">
            <PromptSharpener
              initialPrompt={selectedPrompt}
              onPromptChange={setSelectedPrompt}
              showTextarea={true}
            />
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