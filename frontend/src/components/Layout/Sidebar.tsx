import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Database, 
  Activity, 
  Sparkles,
  Settings,
  Brain,
  X,
  Layers,
  TrendingUp,
  BookOpen
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Connections', href: '/connections', icon: Database },
  { name: 'Monitoring', href: '/monitoring', icon: Activity },
  { name: 'Optimizer', href: '/optimizer', icon: Sparkles },
  { name: 'Workload Analysis', href: '/workload-analysis', icon: TrendingUp },
  { name: 'Index Management', href: '/index-management', icon: Layers },
  { name: 'Pattern Library', href: '/pattern-library', icon: BookOpen },
  { name: 'Configuration', href: '/configuration', icon: Settings },
  { name: 'ML Performance', href: '/ml-performance', icon: Brain },
];

export default function Sidebar({ isOpen, onToggle }: SidebarProps) {
  const location = useLocation();

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay for mobile */}
      <div 
        className="fixed inset-0 bg-gray-900/50 lg:hidden z-40"
        onClick={onToggle}
      />
      
      {/* Sidebar */}
      <aside className="fixed top-0 left-0 z-50 h-screen w-64 bg-white dark:bg-gray-800 shadow-xl border-r border-gray-200 dark:border-gray-700 transition-transform duration-300">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  SQL Optimizer
                </h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">AI-Powered</p>
              </div>
            </div>
            <button
              onClick={onToggle}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`
                    flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200
                    ${isActive 
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg' 
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }
                  `}
                >
                  <item.icon className="w-5 h-5" />
                  <span className="font-medium">{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="px-4 py-3 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-700 dark:to-gray-600 rounded-lg">
              <p className="text-xs font-medium text-gray-700 dark:text-gray-300">
                Version 1.0.0
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Powered by Ollama AI
              </p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
