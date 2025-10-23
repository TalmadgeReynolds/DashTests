// Navigation rail sidebar
import { NavLink } from 'react-router-dom';
import { 
  HomeIcon, 
  FolderIcon, 
  PlusCircleIcon, 
  BookmarkIcon, 
  DocumentDuplicateIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

const navItems = [
  { to: '/dashboard', icon: HomeIcon, label: 'Home' },
  { to: '/jobs', icon: FolderIcon, label: 'Jobs' },
  { to: '/create', icon: PlusCircleIcon, label: 'Create' },
  { to: '/screenplay', icon: DocumentTextIcon, label: 'Script' },
  { to: '/enhancement', icon: SparklesIcon, label: 'Enhance' },
  { to: '/library', icon: BookmarkIcon, label: 'Library' },
  { to: '/batch', icon: DocumentDuplicateIcon, label: 'Batch' },
  { to: '/settings', icon: Cog6ToothIcon, label: 'Settings' },
];

export function NavRail() {
  return (
    <nav className="w-18 bg-white border-r border-slate-200 flex flex-col items-center py-4 gap-2">
      {navItems.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) =>
            `w-14 h-14 flex flex-col items-center justify-center rounded-lg transition-colors ${
              isActive
                ? 'bg-indigo-50 text-indigo-600'
                : 'text-slate-600 hover:bg-slate-100'
            }`
          }
        >
          <item.icon className="w-6 h-6" />
          <span className="text-xs mt-1">{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
