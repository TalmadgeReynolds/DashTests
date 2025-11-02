/**
 * React Query hooks for Screenplay API operations
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ENDPOINTS } from '@/lib/api-config';
import type {
  Screenplay,
  ScreenplayCreate,
  ScreenplayListResponse,
  TextSelection,
  TextSelectionResponse,
  PresignRequest,
  PresignResponse,
} from '@/types/screenplay';

// Query keys
export const screenplayKeys = {
  all: ['screenplays'] as const,
  lists: () => [...screenplayKeys.all, 'list'] as const,
  list: (filters: string) => [...screenplayKeys.lists(), { filters }] as const,
  details: () => [...screenplayKeys.all, 'detail'] as const,
  detail: (id: string) => [...screenplayKeys.details(), id] as const,
};

// API functions
async function fetchScreenplays(skip = 0, limit = 50): Promise<ScreenplayListResponse> {
  console.log('fetchScreenplays: Starting request to', `${ENDPOINTS.SCREENPLAYS}?skip=${skip}&limit=${limit}`);
  try {
    const response = await fetch(
      `${ENDPOINTS.SCREENPLAYS}?skip=${skip}&limit=${limit}`
    );
    console.log('fetchScreenplays: Response status', response.status);
    if (!response.ok) {
      throw new Error('Failed to fetch screenplays');
    }
    const data = await response.json();
    console.log('fetchScreenplays: Received data', data);
    return data;
  } catch (error) {
    console.error('fetchScreenplays: Error', error);
    throw error;
  }
}

async function fetchScreenplay(id: string): Promise<Screenplay> {
  const response = await fetch(`${ENDPOINTS.SCREENPLAYS}/${id}`);
  if (!response.ok) {
    throw new Error('Failed to fetch screenplay');
  }
  return response.json();
}

async function createScreenplay(data: ScreenplayCreate): Promise<Screenplay> {
  const response = await fetch(`${ENDPOINTS.SCREENPLAYS}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create screenplay');
  }
  return response.json();
}

async function deleteScreenplay(id: string): Promise<void> {
  const response = await fetch(`${ENDPOINTS.SCREENPLAYS}/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete screenplay');
  }
}

async function processTextSelection(
  data: TextSelection
): Promise<TextSelectionResponse> {
  const response = await fetch(`${ENDPOINTS.SCREENPLAYS}/text-selection`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to process text selection');
  }
  return response.json();
}

async function getPresignedUploadUrl(data: PresignRequest): Promise<PresignResponse> {
  const response = await fetch(`${ENDPOINTS.UPLOADS}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get presigned URL');
  }
  return response.json();
}

async function uploadFileToPresignedUrl(url: string, file: File): Promise<void> {
  const response = await fetch(url, {
    method: 'PUT',
    headers: {
      'Content-Type': file.type,
    },
    body: file,
  });
  if (!response.ok) {
    throw new Error('Failed to upload file');
  }
}

// Hooks
export function useScreenplays(skip = 0, limit = 50) {
  return useQuery({
    queryKey: screenplayKeys.list(`skip=${skip}&limit=${limit}`),
    queryFn: () => fetchScreenplays(skip, limit),
  });
}

export function useScreenplay(id: string | undefined) {
  return useQuery({
    queryKey: screenplayKeys.detail(id || ''),
    queryFn: () => fetchScreenplay(id!),
    enabled: !!id,
  });
}

export function useCreateScreenplay() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createScreenplay,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: screenplayKeys.lists() });
    },
  });
}

export function useDeleteScreenplay() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteScreenplay,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: screenplayKeys.lists() });
    },
  });
}

export function useProcessTextSelection() {
  return useMutation({
    mutationFn: processTextSelection,
  });
}

export function useUploadScreenplay() {
  const createScreenplayMutation = useCreateScreenplay();

  return useMutation({
    mutationFn: async ({
      file,
      title,
    }: {
      file: File;
      title: string;
    }): Promise<Screenplay> => {
      // Step 1: Get presigned upload URL
      const presignData: PresignRequest = {
        filename: file.name,
        mime: file.type,
        kind: 'SCREENPLAY',
        content_length: file.size,
      };

      const { uploadUrl, fileUrl } = await getPresignedUploadUrl(presignData);

      // Step 2: Upload file to presigned URL
      await uploadFileToPresignedUrl(uploadUrl, file);

      // Step 3: Create screenplay record in database
      const screenplayData: ScreenplayCreate = {
        title,
        filename: file.name,
        pdf_url: fileUrl,
        file_size_bytes: file.size,
      };

      return createScreenplayMutation.mutateAsync(screenplayData);
    },
  });
}
