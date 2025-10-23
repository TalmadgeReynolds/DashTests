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
  EmphasisLayer
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
  const [variantCount, setVariantCount] = useState<number>(3); // Default to 3 variants
  const [showComparison, setShowComparison] = useState<boolean>(false);
  
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
        variants: variantCount,
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
          } catch (retryError) {
            console.error("Retry also failed:", retryError);
            alert('Failed to sharpen prompt. Please try again with a shorter prompt.');
          }
        } else {
          // Handle other errors
          alert('Failed to sharpen prompt: ' + errorMessage);
        }
      }
    } finally {
      setIsSharpening(false);
    }
  }, [selectedPrompt, structuredMode, selectedEmphasis, variantCount]);
  
  const handleSelectVariant = useCallback((variant: PromptVariant) => {
    setSelectedVariant(variant);
    
    // If in structured mode and elements are available, show elements view
    if (structuredMode && variant.elements) {
      setShowElementsView(true);
    } else {
      setShowElementsView(false);
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
            {isLoading ? (
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
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-medium text-gray-900">Prompt Editor</h2>
            {sharpenedPrompts && (
              <button
                onClick={handleResetSharpening}
                className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 rounded border border-gray-300"
              >
                Reset
              </button>
            )}
          </div>
          
          <div className="flex-1 overflow-y-auto p-4">
            {/* Prompt Input */}
            {!sharpenedPrompts && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Selected Text / Prompt
                  </label>
                  <textarea
                    value={selectedPrompt}
                    onChange={(e) => setSelectedPrompt(e.target.value)}
                    className="w-full h-40 p-3 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Select text from screenplay or type a prompt here..."
                  />
                </div>
                
                {/* Mode Switch */}
                <div className="flex justify-between items-center">
                  <div className="flex items-center">
                    <label className="block text-sm font-medium text-gray-700 mr-2">
                      Structured Mode
                    </label>
                    <button
                      onClick={() => setStructuredMode(!structuredMode)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                        structuredMode ? 'bg-emerald-600' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`${
                          structuredMode ? 'translate-x-6' : 'translate-x-1'
                        } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
                      />
                    </button>
                  </div>
                  <span className="text-xs text-gray-500">
                    {structuredMode ? 'Extract narrative elements' : 'Simple text enhancement'}
                  </span>
                </div>
                
                {/* Variant Count Selector */}
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Variant Count: {variantCount}
                  </label>
                  <input 
                    type="range" 
                    min="1" 
                    max="6" 
                    value={variantCount}
                    onChange={(e) => setVariantCount(parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>1</span>
                    <span>2</span>
                    <span>3</span>
                    <span>4</span>
                    <span>5</span>
                    <span>6</span>
                  </div>
                </div>
                
                {/* Emphasis Selection for Structured Mode */}
                {structuredMode && (
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Emphasis
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {['descriptive', 'dynamic', 'cinematic', 'conceptual'].map(layer => {
                        const tooltips = {
                          descriptive: "Enhances visual details and appearances",
                          dynamic: "Emphasizes movement and action",
                          cinematic: "Focuses on camera work and composition",
                          conceptual: "Highlights themes and emotional meaning",
                        };
                        
                        return (
                          <div key={layer} className="relative group">
                            <button
                              onClick={() => {
                                if (selectedEmphasis.includes(layer as EmphasisLayer)) {
                                  setSelectedEmphasis(selectedEmphasis.filter(e => e !== layer as EmphasisLayer));
                                } else {
                                  setSelectedEmphasis([...selectedEmphasis, layer as EmphasisLayer]);
                                }
                              }}
                              className={`px-2 py-1 rounded text-xs font-medium capitalize ${
                                selectedEmphasis.includes(layer as EmphasisLayer) 
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
                        className={`px-2 py-1 text-xs rounded border ${
                          showElementsView 
                            ? 'bg-emerald-100 border-emerald-200 text-emerald-800' 
                            : 'bg-gray-100 border-gray-200 text-gray-700'
                        }`}
                      >
                        {showElementsView ? 'Hide Elements' : 'Show Elements'}
                      </button>
                    )}
                    <button
                      onClick={() => setShowComparison(!showComparison)}
                      className={`px-2 py-1 text-xs rounded border ${
                        showComparison 
                          ? 'bg-blue-100 border-blue-200 text-blue-800' 
                          : 'bg-gray-100 border-gray-200 text-gray-700'
                      }`}
                    >
                      {showComparison ? 'Hide Comparison' : 'Compare Variants'}
                    </button>
                  </div>
                </div>
                
                {/* Display mode - either comparison or normal view */}
                {showComparison ? (
                  // Comparison View
                  <div className="space-y-4">
                    <div className="bg-gray-100 border border-gray-300 p-4 rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <h4 className="font-medium">Original Prompt</h4>
                        <button 
                          onClick={() => navigator.clipboard.writeText(sharpenedPrompts.original)}
                          className="text-xs px-2 py-1 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded border border-gray-300 transition-colors"
                        >
                          Copy
                        </button>
                      </div>
                      <div className="text-sm whitespace-pre-wrap bg-white p-3 border border-gray-200 rounded">{sharpenedPrompts.original}</div>
                    </div>
                    
                    <h4 className="font-medium text-gray-800">Generated Variants ({sharpenedPrompts.variants.length})</h4>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {sharpenedPrompts.variants.map((variant, idx) => (
                        <div
                          key={idx}
                          className={`p-4 border rounded-lg cursor-pointer transition-all ${
                            selectedVariant?.text === variant.text
                            ? 'bg-blue-50 border-blue-300 shadow-sm'
                            : 'bg-white border-gray-200 hover:bg-gray-50'
                          }`}
                          onClick={() => handleSelectVariant(variant)}
                        >
                          <div className="flex justify-between items-center mb-3">
                            <div className="flex items-center">
                              <span className="text-sm font-medium">Variant {idx + 1}</span>
                              <span className="ml-2 text-xs px-1.5 py-0.5 rounded bg-blue-100 text-blue-800">
                                Score: {Math.round(variant.score * 100)}
                              </span>
                              <span className="ml-2 text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">
                                {variant.source}
                              </span>
                            </div>
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                navigator.clipboard.writeText(variant.text);
                              }}
                              className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded border border-gray-200 transition-colors"
                            >
                              Copy
                            </button>
                          </div>
                          <div className="text-sm mt-2 whitespace-pre-wrap bg-white p-3 border border-gray-200 rounded">{variant.text}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  // Normal view
                  <div className="space-y-4">
                    {sharpenedPrompts.variants.map((variant, idx) => (
                      <div
                        key={idx}
                        className={`p-3 border rounded-lg cursor-pointer ${
                          selectedVariant?.text === variant.text
                            ? 'bg-blue-50 border-blue-200'
                            : 'bg-white border-gray-200 hover:bg-gray-50'
                        }`}
                        onClick={() => handleSelectVariant(variant)}
                      >
                        <div className="flex justify-between items-center mb-1">
                          <div className="flex items-center">
                            <span className="text-sm font-medium">Variant {idx + 1}</span>
                            {variant.score && (
                              <span className={`ml-2 px-1.5 py-0.5 text-xs rounded ${
                                variant.score > 0.7 ? 'bg-green-100 text-green-800' : 
                                variant.score > 0.5 ? 'bg-yellow-100 text-yellow-800' : 
                                'bg-gray-100 text-gray-800'
                              }`}>
                                Score: {Math.round(variant.score * 100)}
                              </span>
                            )}
                          </div>
                          <button 
                            onClick={(e) => {
                              e.stopPropagation();
                              navigator.clipboard.writeText(variant.text);
                            }}
                            className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded border border-gray-200"
                          >
                            Copy
                          </button>
                        </div>
                        
                        {/* Text or Elements View */}
                        {structuredMode && showElementsView && selectedVariant?.text === variant.text && variant.elements ? (
                          <>
                            {/* Structured Elements View */}
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
                          </>
                        ) : (
                          <>
                            <div className="text-sm mt-2">
                              <p>{variant.text}</p>
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
                )}
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