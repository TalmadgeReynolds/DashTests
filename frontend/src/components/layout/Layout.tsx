// Main layout component with nav and panels
import type { ReactNode } from 'react';
import { NavRail } from './NavRail';
import { TopBar } from './TopBar';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="h-screen flex flex-col bg-slate-50">
      {/* Top Bar */}
      <TopBar />
      
      <div className="flex-1 flex overflow-hidden">
        {/* Navigation Rail */}
        <NavRail />
        
        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
