/**
 * Components for working with Heygen Photo Avatars
 * 
 * Used in Option2Form to enable the Photo Avatar workflow
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { avatarApi } from '@/lib/avatar-api';
import { getPresignedUrl, uploadToPresignedUrl } from '@/lib/job-api';
import { generatePortrait } from '@/lib/imagen-api';
import { SparklesIcon, ArrowPathIcon, PlusCircleIcon, PhotoIcon } from '@heroicons/react/24/outline';

interface AvatarSelectorProps {
  value: string;
  onChange: (avatarId: string) => void;
}

/**
 * Component for selecting an avatar from the list or creating a new one
 */
export function AvatarSelector({ value, onChange }: AvatarSelectorProps) {
  const [showCreateModal, setShowCreateModal] = useState(false);
  
  // Get the list of avatars
  const { data: avatarList, isLoading, error } = useQuery({
    queryKey: ['avatars'],
    queryFn: () => avatarApi.listAvatars(),
  });
  
  // If no avatar is selected but we have avatars, select the first one
  useEffect(() => {
    if (!value && avatarList?.avatars && avatarList.avatars.length > 0) {
      onChange(avatarList.avatars[0].avatar_id);
    }
  }, [value, avatarList, onChange]);
  
  return (
    <div className="space-y-4">
      {/* Avatar Selection */}
      <div>
        {isLoading ? (
          <div className="flex items-center space-x-2">
            <ArrowPathIcon className="w-4 h-4 animate-spin text-blue-500" />
            <span className="text-sm text-gray-600">Loading avatars...</span>
          </div>
        ) : error ? (
          <div className="text-sm text-red-600">
            Error loading avatars. Please try again later.
          </div>
        ) : avatarList?.avatars?.length === 0 ? (
          <div className="text-sm text-gray-600">
            No avatars found. Create a new avatar to continue.
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-2">
            {avatarList?.avatars.map((avatar) => (
              <div
                key={avatar.avatar_id}
                onClick={() => onChange(avatar.avatar_id)}
                className={`cursor-pointer p-2 rounded-lg border-2 transition ${
                  value === avatar.avatar_id
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                {avatar.image_url ? (
                  <img
                    src={avatar.image_url}
                    alt={avatar.name || 'Avatar'}
                    className="w-full aspect-square object-cover rounded mb-1"
                  />
                ) : (
                  <div className="w-full aspect-square bg-gray-200 rounded mb-1 flex items-center justify-center">
                    <SparklesIcon className="w-8 h-8 text-gray-400" />
                  </div>
                )}
                <p className="text-xs text-center truncate">
                  {avatar.name || `Avatar ${avatar.avatar_id.substring(0, 8)}`}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create New Avatar Button */}
      <button
        type="button"
        onClick={() => setShowCreateModal(true)}
        className="flex items-center justify-center w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
      >
        <PlusCircleIcon className="w-5 h-5 mr-1" />
        Create New Avatar
      </button>

      {/* Create Avatar Modal */}
      {showCreateModal && (
        <CreateAvatarModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={(avatarId) => {
            onChange(avatarId);
            setShowCreateModal(false);
          }}
        />
      )}
    </div>
  );
}

interface CreateAvatarModalProps {
  onClose: () => void;
  onSuccess: (avatarId: string) => void;
}

/**
 * Modal for creating a new avatar
 */
function CreateAvatarModal({ onClose, onSuccess }: CreateAvatarModalProps) {
  const [name, setName] = useState('');
  const [images, setImages] = useState<File[]>([]);
  const [imageUrls, setImageUrls] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [imageSource, setImageSource] = useState<'upload' | 'generate'>('upload');
  const [portraitPrompt, setPortraitPrompt] = useState('');
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [generatedImageUrl, setGeneratedImageUrl] = useState('');
  
  const queryClient = useQueryClient();
  
  // Mutation for creating an avatar
  const createAvatarMutation = useMutation({
    mutationFn: (urls: string[]) => avatarApi.createAvatar(urls, name),
    onSuccess: (data) => {
      // Invalidate avatar cache
      queryClient.invalidateQueries({ queryKey: ['avatars'] });
      onSuccess(data.avatar_id);
    },
  });
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (images.length === 0 && !generatedImageUrl) {
      alert('Please select at least one image or generate an image');
      return;
    }
    
    setIsUploading(true);
    
    try {
      // Upload all images
      const uploadedUrls = [];
      
      for (const image of images) {
        // Get presigned URL
        const { uploadUrl, fileUrl } = await getPresignedUrl({
          filename: image.name,
          mime: image.type,
          kind: 'IMAGE',
          content_length: image.size,
        });
        
        // Upload file
        await uploadToPresignedUrl(uploadUrl, image);
        uploadedUrls.push(fileUrl);
      }
      
      // Create avatar with uploaded URLs
      createAvatarMutation.mutate(uploadedUrls);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to upload images');
      setIsUploading(false);
    }
  };
  
  // Create preview URLs for selected images
  useEffect(() => {
    const urls = images.map(image => URL.createObjectURL(image));
    setImageUrls(urls);
    
    // Cleanup object URLs when unmounting
    return () => {
      urls.forEach(url => URL.revokeObjectURL(url));
    };
  }, [images]);
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full" onClick={(e) => e.stopPropagation()}>
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">Create New Avatar</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ×
            </button>
          </div>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Avatar Name (Optional)
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., My Professional Avatar"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Photo Source <span className="text-red-500">*</span>
            </label>
            
            {/* Image Source Toggle */}
            <div className="flex gap-4 mb-4">
              <button
                type="button"
                onClick={() => setImageSource('upload')}
                className={`flex-1 px-4 py-2 rounded-lg border-2 transition-colors flex items-center justify-center gap-2 ${
                  imageSource === 'upload'
                    ? 'border-blue-600 bg-blue-50 text-blue-700'
                    : 'border-gray-300 text-gray-700 hover:border-gray-400'
                }`}
              >
                <PhotoIcon className="w-5 h-5" />
                Upload Photos
              </button>
              <button
                type="button"
                onClick={() => setImageSource('generate')}
                className={`flex-1 px-4 py-2 rounded-lg border-2 transition-colors flex items-center justify-center gap-2 ${
                  imageSource === 'generate'
                    ? 'border-blue-600 bg-blue-50 text-blue-700'
                    : 'border-gray-300 text-gray-700 hover:border-gray-400'
                }`}
              >
                <SparklesIcon className="w-5 h-5" />
                Generate with AI
              </button>
            </div>
            
            {imageSource === 'upload' ? (
              <div>
                <input
                  type="file"
                  accept="image/jpeg,image/png"
                  multiple
                  onChange={(e) => {
                    const selectedFiles = Array.from(e.target.files || []);
                    setImages(selectedFiles);
                    setGeneratedImageUrl('');
                  }}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  required={imageSource === 'upload' && !images.length}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Upload 1-5 clear photos with visible face. Photos should have good lighting and clear face visibility.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <div>
                  <input
                    type="text"
                    value={portraitPrompt}
                    onChange={(e) => setPortraitPrompt(e.target.value)}
                    placeholder="e.g., professional business person with a suit and tie"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    required={imageSource === 'generate' && !generatedImageUrl}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Describe the character you want to generate for your avatar
                  </p>
                </div>
                <button
                  type="button"
                  onClick={async () => {
                    if (!portraitPrompt.trim()) {
                      alert('Please enter a description');
                      return;
                    }
                    setIsGeneratingImage(true);
                    try {
                      const result = await generatePortrait({
                        description: portraitPrompt,
                        style: 'photorealistic',
                        aspect_ratio: '1:1',
                      });
                      setGeneratedImageUrl(result.image_url);
                      setImages([]); // Clear uploaded images
                      
                      // Convert generated image URL to a File object array
                      const response = await fetch(result.image_url);
                      const blob = await response.blob();
                      const file = new File([blob], 'generated-avatar.jpg', { type: 'image/jpeg' });
                      setImages([file]);
                      
                      alert('Image generated successfully!');
                    } catch (error) {
                      console.error('Failed to generate image:', error);
                      alert('Failed to generate image. Please try again.');
                    } finally {
                      setIsGeneratingImage(false);
                    }
                  }}
                  disabled={isGeneratingImage || !portraitPrompt.trim()}
                  className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                >
                  {isGeneratingImage ? (
                    <>
                      <ArrowPathIcon className="w-5 h-5 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <SparklesIcon className="w-5 h-5" />
                      Generate Image
                    </>
                  )}
                </button>
                
                {/* Show generated image preview */}
                {generatedImageUrl && (
                  <div className="mt-3">
                    <img
                      src={generatedImageUrl}
                      alt="Generated Avatar"
                      className="max-w-full rounded-lg border border-gray-300"
                    />
                    <p className="text-xs text-gray-500 mt-1">✓ Generated image ready</p>
                  </div>
                )}
              </div>
            )}
          </div>
          
          {/* Image Previews */}
          {imageUrls.length > 0 && (
            <div className="grid grid-cols-3 gap-2">
              {imageUrls.map((url, i) => (
                <div key={i} className="relative">
                  <img
                    src={url}
                    alt={`Preview ${i+1}`}
                    className="w-full aspect-square object-cover rounded border border-gray-200"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      setImages(images.filter((_, idx) => idx !== i));
                    }}
                    className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
          
          {createAvatarMutation.isError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">
                {createAvatarMutation.error?.message || 'Failed to create avatar'}
              </p>
            </div>
          )}
          
          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={isUploading || createAvatarMutation.isPending || images.length === 0}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {isUploading ? 'Uploading...' : createAvatarMutation.isPending ? 'Creating Avatar...' : 'Create Avatar'}
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={isUploading || createAvatarMutation.isPending}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}