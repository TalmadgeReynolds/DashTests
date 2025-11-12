/**
 * MinimaxVideoPage
 * Page for MiniMax Hailuo 2.3 video generation
 */
import MinimaxVideoGenerator from '@/components/MinimaxVideoGenerator';

export default function MinimaxVideoPage() {
  const handleVideoGenerated = (videoUrl: string, taskId: string) => {
    console.log('Video generated:', { videoUrl, taskId });
    // You can add additional logic here, like saving to a gallery or database
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <MinimaxVideoGenerator 
        onVideoGenerated={handleVideoGenerated}
        defaultMode="t2v"
      />
    </div>
  );
}
