// Global state management with Zustand
import { create } from 'zustand';
import type { Job, Preset } from '@/types';

interface AppStore {
  // Jobs
  jobs: Job[];
  selectedJobs: string[];
  setJobs: (jobs: Job[]) => void;
  addJob: (job: Job) => void;
  updateJob: (id: string, updates: Partial<Job>) => void;
  removeJob: (id: string) => void;
  toggleJobSelection: (id: string) => void;
  clearSelection: () => void;

  // Presets
  presets: Preset[];
  setPresets: (presets: Preset[]) => void;
  addPreset: (preset: Preset) => void;
  removePreset: (id: string) => void;

  // UI State
  sidebarOpen: boolean;
  contextPanelOpen: boolean;
  toggleSidebar: () => void;
  toggleContextPanel: () => void;

  // Cost budget
  costBudget: number;
  setCostBudget: (budget: number) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  // Jobs
  jobs: [],
  selectedJobs: [],
  setJobs: (jobs) => set({ jobs }),
  addJob: (job) => set((state) => ({ jobs: [job, ...state.jobs] })),
  updateJob: (id, updates) =>
    set((state) => ({
      jobs: state.jobs.map((job) =>
        job.id === id ? { ...job, ...updates } : job
      ),
    })),
  removeJob: (id) =>
    set((state) => ({
      jobs: state.jobs.filter((job) => job.id !== id),
      selectedJobs: state.selectedJobs.filter((jobId) => jobId !== id),
    })),
  toggleJobSelection: (id) =>
    set((state) => ({
      selectedJobs: state.selectedJobs.includes(id)
        ? state.selectedJobs.filter((jobId) => jobId !== id)
        : [...state.selectedJobs, id],
    })),
  clearSelection: () => set({ selectedJobs: [] }),

  // Presets
  presets: [],
  setPresets: (presets) => set({ presets }),
  addPreset: (preset) => set((state) => ({ presets: [...state.presets, preset] })),
  removePreset: (id) =>
    set((state) => ({
      presets: state.presets.filter((preset) => preset.id !== id),
    })),

  // UI State
  sidebarOpen: true,
  contextPanelOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  toggleContextPanel: () =>
    set((state) => ({ contextPanelOpen: !state.contextPanelOpen })),

  // Cost budget
  costBudget: 10.0,
  setCostBudget: (budget) => set({ costBudget: budget }),
}));
