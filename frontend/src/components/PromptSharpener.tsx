/**
 * PromptSharpener Component
 * Reusable prompt enhancement tool using OpenAI/Claude
 * Supports structured mode with creative element extraction
 */
import { useState, useCallback, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';
import type { 
  PromptSharpenRequest, 
  PromptSharpenResponse, 
  PromptVariant,
  EmphasisLayer
} from '@/types';
import { InformationCircleIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface PromptSharpenerProps {
  initialPrompt?: string;
  onPromptChange?: (prompt: string) => void;
  onVariantSelect?: (variant: PromptVariant) => void;
  showTextarea?: boolean; // If false, only shows controls (expects external textarea)
  className?: string;
}

export default function PromptSharpener({
  initialPrompt = '',
  onPromptChange,
  onVariantSelect,
  showTextarea = true,
  className = '',
}: PromptSharpenerProps) {
  const [selectedPrompt, setSelectedPrompt] = useState(initialPrompt);
  const [isSharpening, setIsSharpening] = useState(false);
  const [sharpenedPrompts, setSharpenedPrompts] = useState<PromptSharpenResponse | null>(null);
  const [selectedVariant, setSelectedVariant] = useState<PromptVariant | null>(null);
  
  const [structuredMode, setStructuredMode] = useState(true); // Default to structured mode for color-coded elements
  const [selectedModel, setSelectedModel] = useState<'gpt' | 'claude' | 'both'>('gpt'); // Default to GPT (faster)
  const [selectedEmphasis, setSelectedEmphasis] = useState<EmphasisLayer[]>([]);
  const [showElementsView, setShowElementsView] = useState(true); // Auto-show elements when available
  const [variantCount, setVariantCount] = useState<number>(3);
  const [showComparison, setShowComparison] = useState<boolean>(false);
  const [showInfoBox, setShowInfoBox] = useState(true);

  // Update local prompt when initial prompt changes
  useEffect(() => {
    if (initialPrompt) {
      setSelectedPrompt(initialPrompt);
    }
  }, [initialPrompt]);

  const handlePromptChange = (value: string) => {
    setSelectedPrompt(value);
    onPromptChange?.(value);
  };

  const handleSharpenPrompt = useCallback(async () => {
    if (!selectedPrompt) return;
    
    try {
      setIsSharpening(true);
      setSharpenedPrompts(null);
      setSelectedVariant(null);
      setShowElementsView(false);
      
      const request: PromptSharpenRequest = {
        original: selectedPrompt,
        model: selectedModel,
        variants: variantCount,
        temperature: 0.3,
        max_tokens: structuredMode ? 500 : 300,
        structured: structuredMode
      };
      
      if (structuredMode && selectedEmphasis.length > 0) {
        request.emphasis = selectedEmphasis;
      }
      
      console.log("Sending sharpen request:", JSON.stringify(request, null, 2));
      
      try {
        const response = await apiClient.sharpenPrompt(request);
        console.log("Received sharpen response:", JSON.stringify(response, null, 2));
        setSharpenedPrompts(response);
        
        if (response.variants.length > 0) {
          setSelectedVariant(response.variants[0]);
          onVariantSelect?.(response.variants[0]);
          
          if (structuredMode && response.variants[0].elements) {
            setShowElementsView(true);
          }
        }
      } catch (apiError: unknown) {
        console.error("API Error Details:", apiError);
        
        const errorMessage = apiError instanceof Error ? apiError.message : 'Unknown error';
        
        if (errorMessage.includes('max_tokens')) {
          const newRequest = {
            ...request,
            max_tokens: 400
          };
          
          try {
            console.log("Retrying with lower token count:", newRequest);
            const response = await apiClient.sharpenPrompt(newRequest);
            console.log("Retry successful:", response);
            setSharpenedPrompts(response);
            
            if (response.variants.length > 0) {
              setSelectedVariant(response.variants[0]);
              onVariantSelect?.(response.variants[0]);
              
              if (structuredMode && response.variants[0].elements) {
                setShowElementsView(true);
              }
            }
          } catch (retryError) {
            console.error("Retry also failed:", retryError);
            alert('Failed to sharpen prompt. Please try again with a shorter prompt.');
          }
        } else {
          alert('Failed to sharpen prompt: ' + errorMessage);
        }
      }
    } finally {
      setIsSharpening(false);
    }
  }, [selectedPrompt, structuredMode, selectedModel, selectedEmphasis, variantCount, onVariantSelect]);
  
  const handleSelectVariant = useCallback((variant: PromptVariant) => {
    setSelectedVariant(variant);
    onVariantSelect?.(variant);
    
    if (structuredMode && variant.elements) {
      setShowElementsView(true);
    } else {
      setShowElementsView(false);
    }
  }, [structuredMode, onVariantSelect]);
  
  const handleResetSharpening = useCallback(() => {
    setSharpenedPrompts(null);
    setSelectedVariant(null);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+Enter to sharpen
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && !isSharpening && selectedPrompt) {
        e.preventDefault();
        handleSharpenPrompt();
      }
      
      // Escape to close results
      if (e.key === 'Escape' && sharpenedPrompts) {
        handleResetSharpening();
      }
      
      // Ctrl+1-6 to select variants
      if ((e.ctrlKey || e.metaKey) && sharpenedPrompts) {
        const num = parseInt(e.key);
        if (num >= 1 && num <= 6 && sharpenedPrompts.variants[num - 1]) {
          e.preventDefault();
          handleSelectVariant(sharpenedPrompts.variants[num - 1]);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleSharpenPrompt, handleResetSharpening, handleSelectVariant, isSharpening, selectedPrompt, sharpenedPrompts]);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Info Box */}
      {showInfoBox && !sharpenedPrompts && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 relative">
          <button
            onClick={() => setShowInfoBox(false)}
            className="absolute top-2 right-2 text-blue-400 hover:text-blue-600"
          >
            <XMarkIcon className="w-4 h-4" />
          </button>
          <div className="flex items-start gap-3">
            <InformationCircleIcon className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-medium text-blue-900 text-sm mb-1">
                ✨ AI Prompt Enhancement
              </h4>
              <p className="text-xs text-blue-800 mb-2">
                Transform your prompts using GPT-4o and Claude 3.5. Get multiple variants ranked by quality.
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs text-blue-700">
                <div>
                  <strong>Simple Mode:</strong> Quick enhancement with cinematic details
                </div>
                <div>
                  <strong>Structured Mode:</strong> 🎨 Color-coded breakdown (Character, Action, Camera, Location, etc.)
                </div>
              </div>
              <div className="mt-2 pt-2 border-t border-blue-200 text-xs text-blue-600">
                <strong>Shortcuts:</strong> Ctrl+Enter to sharpen · Ctrl+1-6 to select variant · Esc to close
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Prompt Input */}
      {showTextarea && !sharpenedPrompts && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-2">
            Prompt Text
            <div className="relative group">
              <InformationCircleIcon className="w-4 h-4 text-gray-400 cursor-help" />
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 w-64 p-2 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
                Enter the text you want to enhance. For best results, include the main subject and action.
              </div>
            </div>
          </label>
          <textarea
            value={selectedPrompt}
            onChange={(e) => handlePromptChange(e.target.value)}
            className="w-full h-32 p-3 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
            placeholder="Enter your prompt here..."
          />
          <div className="text-xs text-gray-500 mt-1">
            {selectedPrompt.length} characters
          </div>
        </div>
      )}

      {/* Controls Section */}
      {!sharpenedPrompts && (
        <div className="space-y-4 bg-gray-50 border border-gray-200 rounded-lg p-4">
          {/* Mode Switch */}
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <label className="block text-sm font-medium text-gray-700">
                Structured Mode
              </label>
              <div className="relative group">
                <InformationCircleIcon className="w-4 h-4 text-gray-400 cursor-help" />
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 w-64 p-2 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
                  <strong>Structured Mode</strong> breaks down your prompt into creative elements: Character, Action, Expression, Camera, Location, Art Direction, Dialogue, and Context. Perfect for detailed scene analysis.
                </div>
              </div>
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

          {/* Model Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              AI Model
              <div className="relative group">
                <InformationCircleIcon className="w-4 h-4 text-gray-400 cursor-help" />
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 w-64 p-2 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
                  <strong>GPT-4o</strong>: ⚡ Fast, structured, detailed.<br/>
                  <strong>Claude 4.5</strong>: 🎨 Creative, natural (slower).<br/>
                  <strong>Both</strong>: Mix of both (takes longer).
                </div>
              </div>
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setSelectedModel('gpt')}
                className={`flex-1 px-3 py-2 rounded text-sm font-medium transition-colors ${
                  selectedModel === 'gpt'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                🤖 GPT-4o
              </button>
              <button
                onClick={() => setSelectedModel('claude')}
                className={`flex-1 px-3 py-2 rounded text-sm font-medium transition-colors ${
                  selectedModel === 'claude'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                🧠 Claude
              </button>
              <button
                onClick={() => setSelectedModel('both')}
                className={`flex-1 px-3 py-2 rounded text-sm font-medium transition-colors ${
                  selectedModel === 'both'
                    ? 'bg-emerald-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                ✨ Both
              </button>
            </div>
          </div>
          
          {/* Variant Count Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              Variant Count: {variantCount}
              <div className="relative group">
                <InformationCircleIcon className="w-4 h-4 text-gray-400 cursor-help" />
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 w-64 p-2 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
                  Generate multiple variants to choose from. More variants = more options but takes longer.
                </div>
              </div>
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
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                Emphasis Layers
                <div className="relative group">
                  <InformationCircleIcon className="w-4 h-4 text-gray-400 cursor-help" />
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 w-64 p-2 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
                    Select which aspects to emphasize in the enhanced prompt. You can select multiple layers.
                  </div>
                </div>
              </label>
              <div className="flex flex-wrap gap-2">
                {['descriptive', 'dynamic', 'cinematic', 'conceptual'].map(layer => {
                  const tooltips = {
                    descriptive: "Enhances visual details, colors, textures, and physical appearances",
                    dynamic: "Emphasizes movement, action, energy, and physical dynamics",
                    cinematic: "Focuses on camera work, framing, lighting, and shot composition",
                    conceptual: "Highlights themes, symbolism, emotion, and deeper meaning",
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
                        className={`px-3 py-1.5 rounded text-sm font-medium capitalize transition-colors ${
                          selectedEmphasis.includes(layer as EmphasisLayer) 
                            ? 'bg-emerald-600 text-white shadow-sm' 
                            : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                        }`}
                      >
                        {layer}
                      </button>
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
                        {tooltips[layer as keyof typeof tooltips]}
                      </div>
                    </div>
                  );
                })}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {selectedEmphasis.length === 0 
                  ? 'No emphasis selected - balanced enhancement' 
                  : `${selectedEmphasis.length} layer${selectedEmphasis.length > 1 ? 's' : ''} selected`}
              </p>
            </div>
          )}
          
          {/* Sharpen Button */}
          <div className="flex justify-end pt-2">
            <button
              onClick={handleSharpenPrompt}
              disabled={isSharpening || !selectedPrompt || selectedPrompt.length < 10}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isSharpening ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Sharpening...
                </>
              ) : (
                <>
                  ✨ {structuredMode ? 'Analyze & Sharpen' : 'Sharpen Prompt'}
                </>
              )}
            </button>
          </div>
        </div>
      )}
      
      {/* Prompt Sharpening Results */}
      {sharpenedPrompts && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-medium text-gray-900 flex items-center gap-2">
              ✨ Sharpened Prompts
              <span className="text-xs font-normal text-gray-500">
                ({sharpenedPrompts.variants.length} variant{sharpenedPrompts.variants.length > 1 ? 's' : ''})
              </span>
            </h3>
            <div className="flex items-center gap-2">
              {structuredMode && (
                <button
                  onClick={() => setShowElementsView(!showElementsView)}
                  className={`px-3 py-1.5 text-xs rounded-md border font-medium transition-colors ${
                    showElementsView 
                      ? 'bg-emerald-100 border-emerald-300 text-emerald-800' 
                      : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {showElementsView ? '📝 Hide Elements' : '🎬 Show Elements'}
                </button>
              )}
              <button
                onClick={() => setShowComparison(!showComparison)}
                className={`px-3 py-1.5 text-xs rounded-md border font-medium transition-colors ${
                  showComparison 
                    ? 'bg-blue-100 border-blue-300 text-blue-800' 
                    : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                {showComparison ? '📋 Single View' : '⚖️ Compare All'}
              </button>
              <button
                onClick={handleResetSharpening}
                className="px-3 py-1.5 text-xs bg-white hover:bg-gray-50 text-gray-600 rounded-md border border-gray-300 font-medium transition-colors"
              >
                ↺ Reset
              </button>
            </div>
          </div>
          
          {/* Display mode - either comparison or normal view */}
          {showComparison ? (
            // Comparison View
            <div className="space-y-4">
              <div className="bg-white border border-gray-300 p-4 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium text-gray-700">Original Prompt</h4>
                  <button 
                    onClick={() => navigator.clipboard.writeText(sharpenedPrompts.original)}
                    className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded border border-gray-300 transition-colors"
                  >
                    📋 Copy
                  </button>
                </div>
                <div className="text-sm whitespace-pre-wrap bg-gray-50 p-3 border border-gray-200 rounded">{sharpenedPrompts.original}</div>
              </div>
              
              <h4 className="font-medium text-gray-800 text-sm">Generated Variants</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {sharpenedPrompts.variants.map((variant, idx) => (
                  <div 
                    key={idx}
                    onClick={() => handleSelectVariant(variant)}
                    className={`bg-white border rounded-lg p-3 cursor-pointer transition-all hover:shadow-md ${
                      selectedVariant?.text === variant.text 
                        ? 'border-emerald-500 ring-2 ring-emerald-200' 
                        : 'border-gray-300'
                    }`}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">Variant {idx + 1}</span>
                        {variant.score && (
                          <span className={`px-1.5 py-0.5 text-xs rounded font-medium ${
                            variant.score > 0.7 ? 'bg-green-100 text-green-800' : 
                            variant.score > 0.5 ? 'bg-yellow-100 text-yellow-800' : 
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {Math.round(variant.score * 100)}
                          </span>
                        )}
                        <span className="text-xs text-gray-500">
                          {variant.source === 'gpt' ? '🤖 GPT-4o' : '🧠 Claude'}
                        </span>
                      </div>
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          navigator.clipboard.writeText(variant.text);
                        }}
                        className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded border border-gray-200"
                      >
                        📋
                      </button>
                    </div>
                    
                    <div className="text-sm">
                      <p>{variant.text}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            // Single Variant View with Details
            <div className="space-y-3">
              {/* Score Explanation */}
              <div className="bg-blue-50 border border-blue-200 rounded-md p-2 text-xs text-blue-800">
                <strong>Quality Score:</strong> Based on semantic similarity to your original + visual detail richness. Higher = better quality enhancement.
              </div>
              
              {/* Variant Selector Tabs */}
              <div className="flex gap-2 overflow-x-auto pb-2">
                {sharpenedPrompts.variants.map((variant, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSelectVariant(variant)}
                    className={`flex-shrink-0 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      selectedVariant?.text === variant.text
                        ? 'bg-emerald-600 text-white'
                        : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span>#{idx + 1}</span>
                      {variant.score && (
                        <span className={`px-1 py-0.5 text-xs rounded ${
                          selectedVariant?.text === variant.text
                            ? 'bg-emerald-700 text-emerald-100'
                            : variant.score > 0.7 ? 'bg-green-100 text-green-800' : 
                              variant.score > 0.5 ? 'bg-yellow-100 text-yellow-800' : 
                              'bg-gray-100 text-gray-800'
                        }`}>
                          {Math.round(variant.score * 100)}
                        </span>
                      )}
                    </div>
                  </button>
                ))}
              </div>

              {/* Selected Variant Details */}
              {selectedVariant && (
                <div className="bg-white border border-gray-300 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-3">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-gray-900">Selected Variant</h4>
                      <span className="text-xs text-gray-500">
                        {selectedVariant.source === 'gpt' ? '🤖 GPT-4o' : '🧠 Claude'}
                      </span>
                    </div>
                    <button 
                      onClick={() => navigator.clipboard.writeText(selectedVariant.text)}
                      className="text-sm px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md font-medium transition-colors"
                    >
                      📋 Copy Text
                    </button>
                  </div>

                  {/* Text or Elements View */}
                  {structuredMode && showElementsView && selectedVariant.elements ? (
                    <div className="space-y-3">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {Object.entries(selectedVariant.elements).map(([key, value]) => {
                          if (!value) return null;
                          
                          const elementColors: Record<string, {bg: string, border: string, text: string, icon: string}> = {
                            character: {bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-800', icon: '👤'},
                            action: {bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-800', icon: '⚡'},
                            expression: {bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-800', icon: '😊'},
                            camera: {bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-800', icon: '🎥'},
                            location: {bg: 'bg-teal-50', border: 'border-teal-200', text: 'text-teal-800', icon: '📍'},
                            art_direction: {bg: 'bg-rose-50', border: 'border-rose-200', text: 'text-rose-800', icon: '🎨'},
                            dialogue: {bg: 'bg-indigo-50', border: 'border-indigo-200', text: 'text-indigo-800', icon: '💬'},
                            context: {bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-800', icon: '📖'},
                          };
                          
                          const colors = elementColors[key] || {bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-700', icon: '📝'};
                          
                          return (
                            <div key={key} className={`${colors.bg} p-3 rounded-md border ${colors.border}`}>
                              <p className={`text-xs font-semibold ${colors.text} capitalize flex items-center gap-1 mb-1`}>
                                <span>{colors.icon}</span>
                                {key.replace('_', ' ')}
                              </p>
                              <p className="text-sm text-gray-800">{value}</p>
                            </div>
                          );
                        })}
                      </div>
                      
                      {selectedVariant.model_optimized && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <div className="flex items-center justify-between mb-2">
                            <p className="text-sm font-medium text-gray-700 flex items-center gap-1">
                              <span>🤖</span>
                              Model-Optimized Version
                            </p>
                            <button 
                              onClick={() => navigator.clipboard.writeText(selectedVariant.model_optimized || '')}
                              className="text-xs px-2 py-1 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded border border-blue-300"
                            >
                              📋 Copy
                            </button>
                          </div>
                          <div className="bg-blue-50 text-sm p-3 rounded-md border border-blue-200">
                            {selectedVariant.model_optimized}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div>
                      <div className="text-sm whitespace-pre-wrap bg-gray-50 p-3 rounded-md border border-gray-200 mb-2">
                        {selectedVariant.text}
                      </div>
                      {selectedVariant.diff && (
                        <details className="mt-2">
                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                            📝 View detailed changes
                          </summary>
                          <div className="mt-2 text-xs bg-gray-50 p-3 rounded-md border border-gray-200">
                            <pre className="whitespace-pre-wrap font-mono">{selectedVariant.diff}</pre>
                          </div>
                        </details>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
