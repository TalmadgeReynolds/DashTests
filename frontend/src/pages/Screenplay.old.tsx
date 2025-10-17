/**
 * Screenplay Page
 * Side-by-side layout with screenplay viewer and job creation interface
 */
import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useScreenplays, useScreenplay, useDeleteScreenplay } from '@/hooks/useScreenplay';
import ScreenplayViewer from '@/components/screenplay/ScreenplayViewer';
import ScreenplayUpload from '@/components/screenplay/ScreenplayUpload';
import { apiClient } from '@/lib/api-client';
import type { 
  PromptSharpenRequest, 
  PromptSharpenResponse, 
  PromptVariant,
  EmphasisLayer,
  CreativeElement 
} from '@/types';

export default function Screenplay() {
  const [selectedScreenplayId, setSelectedScreenplayId] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [selectedPrompt, setSelectedPrompt] = useState('');
  const [isSharpening, setIsSharpening] = useState(false);
  const [sharpenedPrompts, setSharpenedPrompts] = useState<PromptSharpenResponse | null>(null);
  const [selectedVariant, setSelectedVariant] = useState<PromptVariant | null>(null);
  
  // Panel resize state
  const [leftPanelWidth, setLeftPanelWidth] = useState<number>(200); // sidebar width in pixels
  const [centerPanelWidth, setCenterPanelWidth] = useState<number>(60); // center panel width as percentage
  const [isDraggingLeft, setIsDraggingLeft] = useState(false);
  const [isDraggingRight, setIsDraggingRight] = useState(false);
  const [startX, setStartX] = useState(0);
  const [startLeftWidth, setStartLeftWidth] = useState(0);
  const [startCenterWidth, setStartCenterWidth] = useState(0);
  
  // Panel resize state
  const [leftPanelWidth, setLeftPanelWidth] = useState<number>(200); // sidebar width in pixels
  const [centerPanelWidth, setCenterPanelWidth] = useState<number>(60); // center panel width as percentage
  const [isDraggingLeft, setIsDraggingLeft] = useState(false);
  const [isDraggingRight, setIsDraggingRight] = useState(false);
  const [startX, setStartX] = useState(0);
  const [startLeftWidth, setStartLeftWidth] = useState(0);
  const [startCenterWidth, setStartCenterWidth] = useState(0);
  
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

  const [structuredMode, setStructuredMode] = useState(false);
  const [selectedEmphasis, setSelectedEmphasis] = useState<EmphasisLayer[]>([]);
  const [showElementsView, setShowElementsView] = useState(false);
  
  // Keep the original emphasis values as is - the backend expects lowercase values
  // The emphasis layers are already matching the backend's expected values
  // So we don't need this conversion function anymore
  
  const handleSharpenPrompt = useCallback(async () => {
    if (!selectedPrompt) return;
    
    try {
      setIsSharpening(true);
      setSharpenedPrompts(null);
      setSelectedVariant(null);
      setShowElementsView(false);
      
      // Create a clean request object with only the necessary fields
      // This avoids sending unnecessary fields that might cause validation issues
      const request: PromptSharpenRequest = {
        original: selectedPrompt,
        model: 'both',
        variants: 3,
        temperature: 0.3,
        max_tokens: structuredMode ? 500 : 300,
        structured: structuredMode
      };
      
      // Only add emphasis if structuredMode is true AND there are selected emphasis layers
      if (structuredMode && selectedEmphasis.length > 0) {
        request.emphasis = selectedEmphasis;
      }
      
      console.log("Sending sharpen request:", JSON.stringify(request, null, 2));
      
      try {
        const response = await apiClient.sharpenPrompt(request);
        console.log("Received sharpen response:", JSON.stringify(response, null, 2));
        setSharpenedPrompts(response);
        
        // Automatically select the best variant (the variants are already sorted by score)
        if (response.variants.length > 0) {
          setSelectedVariant(response.variants[0]);
          
          // If in structured mode and elements are available, show elements view
          if (structuredMode && response.variants[0].elements) {
            setShowElementsView(true);
          }
        }
      } catch (apiError: unknown) {
        console.error("API Error Details:", apiError);
        
        // Try to handle specific validation errors for better UX
        const errorMessage = apiError instanceof Error ? apiError.message : 'Unknown error';
        
        if (errorMessage.includes('max_tokens')) {
          // We have a token limit issue
          const newRequest = {
            ...request,
            max_tokens: 400 // Try with a lower token count
          };
          
          try {
            console.log("Retrying with lower token count:", newRequest);
            const response = await apiClient.sharpenPrompt(newRequest);
            console.log("Retry successful:", response);
            setSharpenedPrompts(response);
            
            if (response.variants.length > 0) {
              setSelectedVariant(response.variants[0]);
              
              if (structuredMode && response.variants[0].elements) {
                setShowElementsView(true);
              }
            }
            return; // Early return on successful retry
          } catch (retryError) {
            console.error("Retry also failed:", retryError);
            // Continue to general error handling
          }
        }
        
        alert(`Failed to sharpen prompt: ${errorMessage}`);
        // Don't rethrow, let the outer catch handle cleanup
      }
    } catch (error) {
      console.error('Failed to sharpen prompt:', error);
      alert('Failed to sharpen prompt. Please try again.');
    } finally {
      setIsSharpening(false);
    }
  }, [selectedPrompt, structuredMode, selectedEmphasis]);
  
  const handleSelectVariant = useCallback((variant: PromptVariant) => {
    setSelectedVariant(variant);
    
    // If we're in structured mode and the variant has a model_optimized field, use that for the prompt
    if (structuredMode && variant.model_optimized) {
      setSelectedPrompt(variant.model_optimized);
    } else {
      // Otherwise use the regular text
      setSelectedPrompt(variant.text);
    }
  }, [structuredMode]);
  
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

      {/* Main Content - Resizable Panels */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Screenplay List */}
        <div 
          className="bg-white border-r border-gray-200 overflow-y-auto" 
          style={{ width: `${leftPanelWidth}px` }}>
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

        {/* Draggable divider between screenplay list and PDF viewer */}
        <div 
          className="w-1 bg-gray-300 hover:bg-blue-500 hover:w-1.5 cursor-col-resize transition-colors relative z-10"
          onMouseDown={handleLeftDividerMouseDown}
        >
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-6 h-10 flex items-center justify-center">
            <div className="h-8 w-0.5 bg-gray-400 rounded-full"></div>
          </div>
        </div>

        {/* Center - Screenplay Viewer or Upload */}
        <div 
          className="bg-gray-50 overflow-hidden" 
          style={{ width: `calc((100% - ${leftPanelWidth}px) * ${centerPanelWidth/100})` }}
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
        
        {/* Draggable divider between PDF viewer and prompt editor */}
        <div 
          className="w-1 bg-gray-300 hover:bg-blue-500 hover:w-1.5 cursor-col-resize transition-colors relative z-10"
          onMouseDown={handleRightDividerMouseDown}
        >
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-6 h-10 flex items-center justify-center">
            <div className="h-8 w-0.5 bg-gray-400 rounded-full"></div>
          </div>
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
              <div className="mt-4 space-y-3">
                {/* Stats */}
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-900">
                    <strong>Characters:</strong> {selectedPrompt.length}
                  </p>
                  <p className="text-sm text-blue-900 mt-1">
                    <strong>Words:</strong> {selectedPrompt.split(/\s+/).filter(w => w).length}
                  </p>
                </div>
                
                {/* Structured Mode Toggle */}
                <div className="flex items-center justify-between p-3 bg-gray-50 border border-gray-200 rounded-lg">
                  <div className="flex items-start">
                    <div>
                      <p className="font-medium text-sm">Structured Mode</p>
                      <p className="text-xs text-gray-500">Deconstruct text into creative elements</p>
                    </div>
                    <div className="relative ml-2 group">
                      <svg className="w-4 h-4 text-gray-500 cursor-help" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                      </svg>
                      <div className="absolute left-0 top-full mt-2 w-64 p-2 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-50 pointer-events-none">
                        <p>Structured Mode analyzes your text and extracts key creative elements:</p>
                        <ul className="mt-1 ml-3 list-disc">
                          <li>Characters & traits</li>
                          <li>Actions & movements</li>
                          <li>Expressions & emotions</li>
                          <li>Camera & framing</li>
                          <li>Location & atmosphere</li>
                          <li>Art direction & style</li>
                        </ul>
                        <p className="mt-1">It creates both human-readable and model-optimized prompts for better AI generation.</p>
                      </div>
                    </div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="sr-only peer"
                      checked={structuredMode}
                      onChange={() => setStructuredMode(!structuredMode)} 
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
                  </label>
                </div>
                
                {/* Sharpen Layers */}
                {structuredMode && (
                  <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                    <div className="flex items-center mb-2">
                      <p className="font-medium text-sm">Emphasis Layers</p>
                      <div className="relative ml-2 group">
                        <svg className="w-4 h-4 text-gray-500 cursor-help" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                        </svg>
                        <div className="absolute left-0 top-full mt-2 w-64 p-2 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-50 pointer-events-none">
                          <p className="font-medium">Emphasis layers control what aspects get enhanced:</p>
                          <ul className="mt-1 ml-3 list-disc">
                            <li><span className="font-medium text-emerald-300">Descriptive</span>: Physical details, appearances, textures</li>
                            <li><span className="font-medium text-emerald-300">Dynamic</span>: Motion, action, energy, movement</li>
                            <li><span className="font-medium text-emerald-300">Cinematic</span>: Camera angles, lighting, composition</li>
                            <li><span className="font-medium text-emerald-300">Conceptual</span>: Symbolism, themes, emotions</li>
                          </ul>
                          <p className="mt-1">Select multiple layers to balance different aspects.</p>
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {(['descriptive', 'dynamic', 'cinematic', 'conceptual'] as EmphasisLayer[]).map((layer) => {
                        const tooltips = {
                          descriptive: "Enhances visual details and appearances",
                          dynamic: "Emphasizes movement and action",
                          cinematic: "Focuses on camera work and composition",
                          conceptual: "Highlights themes and emotional meaning"
                        };
                        
                        return (
                          <div key={layer} className="relative group">
                            <button
                              onClick={() => {
                                if (selectedEmphasis.includes(layer)) {
                                  setSelectedEmphasis(selectedEmphasis.filter(e => e !== layer));
                                } else {
                                  setSelectedEmphasis([...selectedEmphasis, layer]);
                                }
                              }}
                              className={`px-2 py-1 rounded text-xs font-medium capitalize ${
                                selectedEmphasis.includes(layer) 
                                  ? 'bg-emerald-600 text-white' 
                                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                              }`}
                            >
                              {layer}
                            </button>
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 w-40 p-1 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
                              {tooltips[layer as keyof typeof tooltips]}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    <p className="text-xs text-gray-500 mt-2">Select layers to emphasize in the prompt</p>
                  </div>
                )}
                
                {/* Sharpen Button */}
                <div className="flex justify-end">
                  <button
                    onClick={handleSharpenPrompt}
                    disabled={isSharpening || !selectedPrompt || selectedPrompt.length < 10}
                    className="px-4 py-2 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex-shrink-0"
                  >
                    {isSharpening ? 'Sharpening...' : `✨ ${structuredMode ? 'Analyze & Sharpen' : 'Sharpen'}`}
                  </button>
                </div>
              </div>
            )}
            
            {/* Prompt Sharpening Results */}
            {sharpenedPrompts && (
              <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-3">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="font-medium text-gray-900">Sharpened Prompts</h3>
                  <div className="flex items-center gap-2">
                    {structuredMode && (
                      <button
                        onClick={() => setShowElementsView(!showElementsView)}
                        className="text-xs px-2 py-1 bg-blue-50 text-blue-600 rounded border border-blue-200 hover:bg-blue-100"
                      >
                        {showElementsView ? "Show Text View" : "Show Elements View"}
                      </button>
                    )}
                    <button 
                      onClick={handleResetSharpening}
                      className="text-xs text-gray-500 hover:text-gray-700"
                    >
                      Reset
                    </button>
                  </div>
                </div>
                
                <div className="space-y-3 max-h-80 overflow-y-auto">
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
                      
                      {/* Structured Elements View */}
                      {structuredMode && showElementsView && variant.elements && (
                        <div className="mt-2 space-y-2">
                          <div className="grid grid-cols-2 gap-2">
                            {Object.entries(variant.elements).map(([key, value]) => {
                              if (!value) return null;
                              
                              // Define colors for different element types
                              const elementColors: Record<string, {bg: string, border: string, text: string}> = {
                                character: {bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-800'},
                                action: {bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-800'},
                                expression: {bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-800'},
                                camera: {bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-800'},
                                location: {bg: 'bg-teal-50', border: 'border-teal-200', text: 'text-teal-800'},
                                art_direction: {bg: 'bg-rose-50', border: 'border-rose-200', text: 'text-rose-800'},
                                dialogue: {bg: 'bg-indigo-50', border: 'border-indigo-200', text: 'text-indigo-800'},
                                context: {bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-800'},
                              };
                              
                              const colors = elementColors[key] || {bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-700'};
                              
                              return (
                                <div key={key} className={`${colors.bg} p-2 rounded border ${colors.border}`}>
                                  <p className={`text-xs font-medium ${colors.text} capitalize flex items-center`}>
                                    {key.replace('_', ' ')}
                                  </p>
                                  <p className="text-sm mt-1">{value}</p>
                                </div>
                              );
                            })}
                          </div>
                          
                          {variant.model_optimized && (
                            <div className="mt-3">
                              <div className="flex items-center justify-between mb-1">
                                <p className="text-xs font-medium text-gray-700">Model-Optimized Version</p>
                                <button 
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    navigator.clipboard.writeText(variant.model_optimized || '');
                                  }}
                                  className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded border border-gray-200"
                                >
                                  Copy
                                </button>
                              </div>
                              <div className="bg-blue-50 text-sm p-2 rounded border border-blue-200">
                                {variant.model_optimized}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                      
                      {/* Text View */}
                      {(!structuredMode || !showElementsView || !variant.elements) && (
                        <>
                          <div className="flex justify-between items-start">
                            <p className="text-sm text-gray-800 flex-1">{variant.text}</p>
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                navigator.clipboard.writeText(variant.text);
                              }}
                              className="ml-2 text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded border border-gray-200 flex-shrink-0"
                            >
                              Copy
                            </button>
                          </div>
                          {variant.diff && (
                            <details className="mt-1">
                              <summary className="text-xs text-blue-600 cursor-pointer">View changes</summary>
                              <div className="mt-1 text-xs bg-gray-50 p-2 rounded">
                                <pre className="whitespace-pre-wrap">{variant.diff}</pre>
                              </div>
                            </details>
                          )}
                        </>
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
