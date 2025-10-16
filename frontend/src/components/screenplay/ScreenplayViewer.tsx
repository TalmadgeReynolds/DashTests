/**
 * ScreenplayViewer Component
 * Displays PDF screenplay with text selection capability
 */
import { useState, useCallback, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { useProcessTextSelection } from '@/hooks/useScreenplay';
import type { Screenplay } from '@/types/screenplay';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';
import { getPresignedAccessUrl } from '@/lib/s3-utils';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface ScreenplayViewerProps {
  screenplay: Screenplay;
  onTextSelected?: (selectedText: string, processedPrompt: string) => void;
}

export default function ScreenplayViewer({
  screenplay,
  onTextSelected,
}: ScreenplayViewerProps) {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [selectedText, setSelectedText] = useState('');
  const [pdfUrl, setPdfUrl] = useState<string | null>(null); // Start with null instead of the raw S3 URL
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  const processTextMutation = useProcessTextSelection();

  // Get presigned URL for PDF when component mounts
  useEffect(() => {
    async function getSignedUrl() {
      setLoading(true);
      setError(null);
      try {
        const url = await getPresignedAccessUrl(screenplay.pdf_url);
        // Make sure we got a valid URL that contains the signature
        if (url && url.includes('Signature=')) {
          setPdfUrl(url);
        } else {
          setError('Invalid presigned URL received');
          console.error('Invalid presigned URL:', url);
        }
      } catch (error) {
        console.error('Failed to get presigned URL:', error);
        setError('Failed to get access to the PDF');
      } finally {
        setLoading(false);
      }
    }
    
    getSignedUrl();
  }, [screenplay.pdf_url]);

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
  };

  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection();
    const text = selection?.toString().trim();
    
    if (text && text.length > 0) {
      setSelectedText(text);
    }
  }, []);

  const handleUseSelection = async () => {
    if (!selectedText) {
      alert('Please select some text from the screenplay first');
      return;
    }

    try {
      const result = await processTextMutation.mutateAsync({
        screenplay_id: screenplay.id,
        selected_text: selectedText,
      });
      
      onTextSelected?.(result.selected_text, result.processed_prompt);
      
      // Clear selection
      window.getSelection()?.removeAllRanges();
      setSelectedText('');
    } catch (error) {
      console.error('Failed to process text selection:', error);
      alert('Failed to process selected text. Please try again.');
    }
  };

  const goToPrevPage = () => {
    setPageNumber((prev) => Math.max(prev - 1, 1));
  };

  const goToNextPage = () => {
    setPageNumber((prev) => Math.min(prev + 1, numPages || 1));
  };

  const zoomIn = () => {
    setScale((prev) => Math.min(prev + 0.2, 2.0));
  };

  const zoomOut = () => {
    setScale((prev) => Math.max(prev - 0.2, 0.5));
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {loading && (
        <div className="flex flex-col items-center justify-center p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Getting secure access to PDF...</p>
        </div>
      )}
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">{screenplay.title}</h2>
          <p className="text-sm text-gray-500">{screenplay.filename}</p>
        </div>
        
        {/* Zoom Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={zoomOut}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded"
            disabled={scale <= 0.5}
          >
            −
          </button>
          <span className="text-sm text-gray-700 min-w-[4rem] text-center">
            {Math.round(scale * 100)}%
          </span>
          <button
            onClick={zoomIn}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded"
            disabled={scale >= 2.0}
          >
            +
          </button>
        </div>
      </div>

      {/* PDF Viewer */}
      <div
        className="flex-1 overflow-auto p-4"
        onMouseUp={handleTextSelection}
      >
        <div className="flex justify-center">
          {loading && (
            <div className="flex items-center justify-center p-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          )}
          
          {!loading && error && (
            <div className="p-8 text-center">
              <p className="text-red-600">Failed to load PDF</p>
              <p className="text-sm text-gray-600 mt-2">{error}</p>
              <button 
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                onClick={() => window.location.reload()}
              >
                Retry
              </button>
            </div>
          )}
          
          {!loading && !error && pdfUrl && (
            <Document
              file={pdfUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              loading={
                <div className="flex items-center justify-center p-8">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
              }
              error={
                <div className="p-8 text-center">
                  <p className="text-red-600">Failed to load PDF</p>
                  <p className="text-sm text-gray-600 mt-2">This could be due to insufficient permissions or missing file.</p>
                </div>
              }
            >
              <Page
                pageNumber={pageNumber}
                scale={scale}
                renderTextLayer={true}
                renderAnnotationLayer={true}
                className="shadow-lg"
              />
            </Document>
          )}
        </div>
      </div>

      {/* Footer Controls */}
      {!loading && !error && pdfUrl && (
        <div className="px-4 py-3 bg-white border-t border-gray-200">
          <div className="flex items-center justify-between">
            {/* Page Navigation */}
            <div className="flex items-center gap-3">
              <button
                onClick={goToPrevPage}
                disabled={pageNumber <= 1}
                className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="text-sm text-gray-700">
                Page {pageNumber} of {numPages || '?'}
              </span>
              <button
                onClick={goToNextPage}
                disabled={pageNumber >= (numPages || 1)}
                className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>

          {/* Selection Actions */}
          <div className="flex items-center gap-3">
            {selectedText && (
              <div className="text-sm text-gray-600">
                {selectedText.length} characters selected
              </div>
            )}
            <button
              onClick={handleUseSelection}
              disabled={!selectedText || processTextMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm font-medium"
            >
              {processTextMutation.isPending ? 'Processing...' : 'Use Selection as Prompt'}
            </button>
          </div>
        </div>
      </div>
      )}
    </div>
  );
}
