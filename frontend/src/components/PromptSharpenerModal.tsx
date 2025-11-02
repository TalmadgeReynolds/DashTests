/**
 * PromptSharpenerModal
 * Modal dialog wrapper for the PromptSharpener component
 */
import { useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import PromptSharpener from './PromptSharpener';
import type { PromptVariant } from '@/types';

interface PromptSharpenerModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialPrompt: string;
  onApplyVariant: (text: string, variant?: PromptVariant) => void;
}

export default function PromptSharpenerModal({
  isOpen,
  onClose,
  initialPrompt,
  onApplyVariant,
}: PromptSharpenerModalProps) {
  
  const handleVariantSelect = (variant: PromptVariant) => {
    // Store the selected variant for the Apply button
    // Using the variant text as the prompt
    const textToUse = variant.model_optimized || variant.text;
    onApplyVariant(textToUse, variant);
  };

  // Handle escape key and body scroll lock
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      
      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          onClose();
        }
      };
      
      document.addEventListener('keydown', handleEscape);
      return () => {
        document.body.style.overflow = '';
        document.removeEventListener('keydown', handleEscape);
      };
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div 
          className="relative w-full max-w-4xl bg-white rounded-2xl shadow-2xl transform transition-all"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium leading-6 text-gray-900 flex items-center gap-2">
              ✨ AI Prompt Sharpener
            </h3>
            <button
              type="button"
              className="rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              onClick={onClose}
            >
              <span className="sr-only">Close</span>
              <XMarkIcon className="h-6 w-6" aria-hidden="true" />
            </button>
          </div>

          {/* Content */}
          <div className="px-6 py-4 max-h-[70vh] overflow-y-auto">
            <PromptSharpener
              initialPrompt={initialPrompt}
              onVariantSelect={handleVariantSelect}
              showTextarea={true}
            />
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-2xl">
            <p className="text-sm text-gray-500">
              💡 Select a variant above and it will automatically be applied to your script
            </p>
            <div className="flex gap-3">
              <button
                type="button"
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                onClick={onClose}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
