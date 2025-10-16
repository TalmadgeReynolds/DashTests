import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  MicrophoneIcon,
  SpeakerWaveIcon,
  TrashIcon,
  PlusIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';
import { voiceApi, type Voice } from '@/lib/voice-api';

export default function VoiceLibrary() {
  const [searchFilter, setSearchFilter] = useState('');
  const [selectedVoice, setSelectedVoice] = useState<Voice | null>(null);
  const [showCloneModal, setShowCloneModal] = useState(false);
  const queryClient = useQueryClient();

  // Fetch voices
  const { data: voices, isLoading } = useQuery({
    queryKey: ['voices', searchFilter],
    queryFn: () => voiceApi.listVoices(searchFilter || undefined),
  });

  // Fetch subscription info
  const { data: subscriptionInfo } = useQuery({
    queryKey: ['subscription'],
    queryFn: () => voiceApi.getSubscriptionInfo(),
  });

  // Delete voice mutation
  const deleteMutation = useMutation({
    mutationFn: (voiceId: string) => voiceApi.deleteVoice(voiceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['voices'] });
      setSelectedVoice(null);
    },
  });

  const handleDelete = (voiceId: string, voiceName: string) => {
    if (confirm(`Delete voice "${voiceName}"? This cannot be undone.`)) {
      deleteMutation.mutate(voiceId);
    }
  };

  const usagePercent = subscriptionInfo
    ? (subscriptionInfo.character_count / subscriptionInfo.character_limit) * 100
    : 0;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Voice Library</h1>
              <p className="mt-2 text-gray-600">
                Manage your ElevenLabs voices and create custom voice clones
              </p>
            </div>
            <button
              onClick={() => setShowCloneModal(true)}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            >
              <PlusIcon className="h-5 w-5" />
              Clone Voice
            </button>
          </div>

          {/* Subscription Info */}
          {subscriptionInfo && (
            <div className="mt-6 rounded-lg bg-white p-4 shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Subscription Tier</p>
                  <p className="text-lg font-semibold capitalize">{subscriptionInfo.tier}</p>
                </div>
                <div className="flex-1 px-8">
                  <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                    <span>Character Usage</span>
                    <span>
                      {subscriptionInfo.character_count.toLocaleString()} /{' '}
                      {subscriptionInfo.character_limit.toLocaleString()}
                    </span>
                  </div>
                  <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all ${
                        usagePercent > 80 ? 'bg-red-500' : 'bg-blue-500'
                      }`}
                      style={{ width: `${Math.min(usagePercent, 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search voices..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="w-full rounded-lg border border-gray-300 pl-10 pr-4 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Voice Grid */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent" />
            <p className="mt-4 text-gray-600">Loading voices...</p>
          </div>
        ) : voices && voices.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {voices.map((voice) => (
              <div
                key={voice.voice_id}
                className={`rounded-lg border-2 bg-white p-4 shadow-sm transition-all cursor-pointer ${
                  selectedVoice?.voice_id === voice.voice_id
                    ? 'border-blue-500 ring-2 ring-blue-200'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedVoice(voice)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="rounded-full bg-blue-100 p-2">
                      <MicrophoneIcon className="h-6 w-6 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{voice.name}</h3>
                      <p className="text-sm text-gray-500 capitalize">{voice.category}</p>
                    </div>
                  </div>
                  {voice.category === 'cloned' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(voice.voice_id, voice.name);
                      }}
                      className="rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-600"
                      disabled={deleteMutation.isPending}
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  )}
                </div>

                {voice.labels && Object.keys(voice.labels).length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {Object.entries(voice.labels).map(([key, value]) => (
                      <span
                        key={key}
                        className="inline-block rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600"
                      >
                        {value}
                      </span>
                    ))}
                  </div>
                )}

                <div className="mt-3 flex items-center gap-2">
                  <button className="flex-1 inline-flex items-center justify-center gap-1 rounded bg-blue-50 px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-100">
                    <SpeakerWaveIcon className="h-4 w-4" />
                    Use Voice
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <MicrophoneIcon className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-4 text-gray-600">
              {searchFilter ? 'No voices found matching your search' : 'No voices available'}
            </p>
          </div>
        )}

        {/* Clone Voice Modal */}
        {showCloneModal && (
          <CloneVoiceModal
            onClose={() => setShowCloneModal(false)}
            onSuccess={() => {
              setShowCloneModal(false);
              queryClient.invalidateQueries({ queryKey: ['voices'] });
            }}
          />
        )}
      </div>
    </div>
  );
}

// Clone Voice Modal Component
function CloneVoiceModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [files, setFiles] = useState<File[]>([]);

  const cloneMutation = useMutation({
    mutationFn: () => voiceApi.cloneVoice(name, files, description),
    onSuccess,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name && files.length > 0) {
      cloneMutation.mutate();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Clone Voice</h2>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Voice Name *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My Brand Voice"
                required
                className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Professional narration voice..."
                rows={2}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Audio Samples * (1-5 files)
              </label>
              <input
                type="file"
                accept="audio/mp3,audio/wav,audio/m4a"
                multiple
                onChange={(e) => setFiles(Array.from(e.target.files || []))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2"
              />
              <p className="mt-1 text-xs text-gray-500">
                Upload 1-5 audio files (MP3, WAV, M4A). Total duration: 1-5 minutes recommended.
              </p>
              {files.length > 0 && (
                <div className="mt-2 space-y-1">
                  {files.map((file, idx) => (
                    <div key={idx} className="text-sm text-gray-600">
                      • {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {cloneMutation.error && (
            <div className="mt-4 rounded bg-red-50 p-3 text-sm text-red-600">
              {cloneMutation.error.message}
            </div>
          )}

          <div className="mt-6 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50"
              disabled={cloneMutation.isPending}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!name || files.length === 0 || cloneMutation.isPending}
              className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {cloneMutation.isPending ? 'Cloning...' : 'Clone Voice'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
