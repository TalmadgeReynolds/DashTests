// Top bar with branding and user info
export function TopBar() {
  return (
    <div className="h-16 bg-white border-b border-slate-200 flex items-center px-6">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
          <span className="text-white font-bold text-lg">🎬</span>
        </div>
        <h1 className="text-xl font-bold text-slate-900">AI Lip-Sync</h1>
      </div>
      
      <div className="ml-auto flex items-center gap-4">
        <div className="text-sm text-slate-600">
          Credits: <span className="font-semibold text-indigo-600">$125.50</span>
        </div>
        <div className="w-8 h-8 bg-slate-200 rounded-full" />
      </div>
    </div>
  );
}
