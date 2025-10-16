/**
 * React Query hooks for Jobs API operations
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ENDPOINTS } from '@/lib/api-config';
import type { Job } from '@/types/job';

// Query keys
export const jobKeys = {
  all: ['jobs'] as const,
  lists: () => [...jobKeys.all, 'list'] as const,
  list: (filters: string) => [...jobKeys.lists(), { filters }] as const,
  details: () => [...jobKeys.all, 'detail'] as const,
  detail: (id: string) => [...jobKeys.details(), id] as const,
};

// API functions
async function fetchJobs(): Promise<Job[]> {
  const response = await fetch(`${ENDPOINTS.JOBS}`);
  if (!response.ok) {
    throw new Error('Failed to fetch jobs');
  }
  return response.json();
}

async function fetchJob(id: string): Promise<Job> {
  const response = await fetch(`${ENDPOINTS.JOBS}/${id}`);
  if (!response.ok) {
    throw new Error('Failed to fetch job');
  }
  return response.json();
}

// Hooks
export function useJobs() {
  return useQuery({
    queryKey: jobKeys.lists(),
    queryFn: fetchJobs,
  });
}

export function useJob(id: string | undefined) {
  return useQuery({
    queryKey: jobKeys.detail(id || ''),
    queryFn: () => fetchJob(id!),
    enabled: !!id,
  });
}