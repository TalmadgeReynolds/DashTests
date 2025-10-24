import { useEffect, useRef } from 'react';
import * as Plyr from 'plyr';
import 'plyr/dist/plyr.css';

interface VideoPlayerProps {
  src: string;
  className?: string;
}

interface PlyrInstance {
  destroy: () => void;
}

export function VideoPlayer({ src, className = '' }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const playerRef = useRef<PlyrInstance>(null);

  // Immediate logging on component mount
  console.log('[VideoPlayer] Component mounted with:', { 
    src, 
    className,
    isProRes: src?.toLowerCase().includes('.mov'),
    fileType: src?.split('?')[0]?.split('.').pop(),
    videoElement: {
      supported: {
        prores: videoRef.current?.canPlayType('video/quicktime;codecs="prores"'),
        proResHQ: videoRef.current?.canPlayType('video/quicktime;codecs="apch"'),
        proRes422: videoRef.current?.canPlayType('video/quicktime;codecs="apcn"'),
        quicktime: videoRef.current?.canPlayType('video/quicktime'),
        mp4: videoRef.current?.canPlayType('video/mp4')
      }
    }
  });
  
  // Force console log visibility
  console.warn('[VideoPlayer] Debug Mode Active - ProRes Support Check');

  useEffect(() => {
    const videoElement = videoRef.current;
    console.log('[VideoPlayer] UseEffect triggered with:', { 
      hasVideoElement: !!videoElement,
      hasPlayerRef: !!playerRef.current,
      src 
    });

    if (!videoElement || playerRef.current) {
      console.log('[VideoPlayer] Early return because:', {
        noVideoElement: !videoElement,
        hasExistingPlayer: !!playerRef.current
      });
      return;
    }

    console.log('[VideoPlayer] Initializing with source:', {
      url: src,
      supportedTypes: {
        h264: videoElement.canPlayType('video/mp4; codecs=avc1.42E01E'),
        hevc: videoElement.canPlayType('video/mp4; codecs=hevc'),
        prores: videoElement.canPlayType('video/quicktime; codecs=prores'),
        proRes422: videoElement.canPlayType('video/quicktime; codecs=apcn'),
        proRes4444: videoElement.canPlayType('video/quicktime; codecs=ap4h')
      }
    });
    
    const handleError = (e: Event) => {
      const video = e.target as HTMLVideoElement;
      const error = video.error;
      console.error('[VideoPlayer] Video error:', {
        code: error?.code,
        message: error?.message,
        src: video.src,
        networkState: video.networkState,
        readyState: video.readyState,
        currentSrc: video.currentSrc,
        videoWidth: video.videoWidth,
        videoHeight: video.videoHeight
      });
    };

    const handleMetadata = () => {
      console.log('[VideoPlayer] Video metadata loaded:', {
        duration: videoElement.duration,
        videoWidth: videoElement.videoWidth,
        videoHeight: videoElement.videoHeight,
        readyState: videoElement.readyState,
        currentSrc: videoElement.currentSrc,
      });

      // Try to get video tracks info
      try {
        if ('captureStream' in videoElement) {
          const stream = (videoElement as HTMLVideoElement & { captureStream(): MediaStream }).captureStream();
          const tracks = stream.getVideoTracks();
          if (tracks.length > 0) {
            console.log('[VideoPlayer] Video track info:', {
              settings: tracks[0].getSettings(),
              constraints: tracks[0].getConstraints(),
              capabilities: tracks[0].getCapabilities()
            });
          } else {
            console.warn('[VideoPlayer] No video tracks found');
          }
        }
      } catch (error) {
        console.warn('[VideoPlayer] Could not get video track info:', error);
      }
    };

    // Add more event listeners for debugging
    videoElement.addEventListener('error', handleError);
    videoElement.addEventListener('loadedmetadata', handleMetadata);
    videoElement.addEventListener('loadeddata', () => {
      console.log('[VideoPlayer] Video data loaded:', {
        readyState: videoElement.readyState,
        networkState: videoElement.networkState
      });
    });
    videoElement.addEventListener('canplay', () => {
      console.log('[VideoPlayer] Video can play:', {
        readyState: videoElement.readyState,
        networkState: videoElement.networkState,
        paused: videoElement.paused,
        currentTime: videoElement.currentTime
      });
    });

    try {
      playerRef.current = new Plyr(videoElement, {
        controls: [
          'play-large',
          'play',
          'progress',
          'current-time',
          'mute',
          'volume',
          'settings',
          'fullscreen'
        ],
        debug: true
      });
    } catch (error) {
      console.error('[VideoPlayer] Failed to initialize Plyr:', error);
    }

    return () => {
      console.log('[VideoPlayer] Cleaning up player');
      videoElement.removeEventListener('error', handleError);
      videoElement.removeEventListener('loadedmetadata', handleMetadata);
      if (playerRef.current) {
        playerRef.current.destroy();
        playerRef.current = null;
      }
    };
  }, [src]); // Include src in dependencies

  return (
    <video
      ref={videoRef}
      className={className}
      controls
      crossOrigin="anonymous"
      id="video-player"
      aria-label="Video player"
      preload="metadata"
      onLoadedMetadata={() => {
        if (videoRef.current) {
          console.log('[VideoPlayer] Metadata loaded:', {
            duration: videoRef.current.duration,
            size: `${videoRef.current.videoWidth}x${videoRef.current.videoHeight}`,
            type: videoRef.current.currentSrc?.split('?')[0]?.split('.').pop(),
            readyState: videoRef.current.readyState
          });
        }
      }}
      onError={() => {
        if (videoRef.current) {
          const { currentSrc, videoWidth, videoHeight, readyState, networkState, error } = videoRef.current;
          console.error('[VideoPlayer] Video element state:', {
            currentSrc,
            videoWidth,
            videoHeight,
            readyState,
            networkState,
            error
          });
        }
      }}
      playsInline
    >
      <source 
        src={src} 
        type="video/quicktime" 
        onError={() => {
          console.log('[VideoPlayer] QuickTime format failed');
          if (videoRef.current) {
            const { currentSrc, videoWidth, videoHeight, readyState, networkState, error } = videoRef.current;
            console.error('[VideoPlayer] Video element state:', {
              currentSrc,
              videoWidth,
              videoHeight,
              readyState,
              networkState,
              error
            });
          }
        }}
      />
      <source 
        src={src} 
        type="video/quicktime;codecs=prores" 
        onError={() => console.log('[VideoPlayer] ProRes format failed')}
      />
      <source 
        src={src} 
        type="video/quicktime;codecs=apcn" 
        onError={() => console.log('[VideoPlayer] ProRes 422 format failed')}
      />
      <source src={src} type="video/quicktime;codecs=apch" />
      <source src={src} type="video/mp4;codecs=avc1.42E01E,mp4a.40.2" />
      <source src={src} 
        type="video/mp4" 
        onError={() => console.log('[VideoPlayer] MP4 format failed')}
      />
      <p>Your browser doesn't support this video format. Please ensure you have ProRes codec support in your browser.</p>
    </video>
  );
}