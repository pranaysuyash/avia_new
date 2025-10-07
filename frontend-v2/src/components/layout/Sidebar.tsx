import { 
  LayoutDashboard, 
  Upload, 
  FileText, 
  Brain, 
  Users, 
  Search, 
  Settings,
  ChevronRight,
  Mic,
  Video,
  Stethoscope,
  Scale,
  TrendingUp
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

interface SidebarProps {
  collapsed: boolean;
}

interface NavItem {
  icon: React.ElementType;
  label: string;
  href: string;
  badge?: string;
  children?: NavItem[];
}

const navigationItems: NavItem[] = [
  {
    icon: LayoutDashboard,
    label: 'Dashboard',
    href: '/dashboard',
  },
  {
    icon: Upload,
    label: 'Media Processing',
    href: '/media-processing',
  },
  {
    icon: FileText,
    label: 'Content Library',
    href: '/library',
    badge: '47k',
  },
  {
    icon: Brain,
    label: 'AI Processing',
    href: '/ai',
    children: [
      { icon: Mic, label: 'Speech Processing', href: '/ai/speech' },
      { icon: Video, label: 'Video Intelligence', href: '/ai/video' },
      { icon: Brain, label: 'NLP & Analysis', href: '/ai/nlp' },
    ],
  },
  {
    icon: TrendingUp,
    label: 'Enterprise Intelligence',
    href: '/intelligence',
    children: [
      { icon: Stethoscope, label: 'Medical AI', href: '/intelligence/medical' },
      { icon: Scale, label: 'Legal AI', href: '/intelligence/legal' },
      { icon: TrendingUp, label: 'Business Intelligence', href: '/intelligence/business' },
    ],
  },
  {
    icon: Users,
    label: 'Team Workspaces',
    href: '/workspaces',
  },
  {
    icon: Search,
    label: 'Advanced Search',
    href: '/search',
  },
  {
    icon: Settings,
    label: 'Settings',
    href: '/settings',
  },
];

export function Sidebar({ collapsed }: SidebarProps) {
  const [expandedItems, setExpandedItems] = useState<string[]>([]);
  const navigate = useNavigate();
  const location = useLocation();

  const toggleExpanded = (label: string) => {
    setExpandedItems(prev =>
      prev.includes(label)
        ? prev.filter(item => item !== label)
        : [...prev, label]
    );
  };

  const handleNavigation = (href: string, hasChildren: boolean) => {
    if (!hasChildren) {
      navigate(href);
    }
  };

  return (
    <aside
      className={cn(
        'hidden lg:fixed left-0 top-16 h-[calc(100vh-4rem)] bg-card border-r border-border transition-all duration-300 overflow-y-auto scrollbar-thin',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      <nav className="p-2 space-y-1">
        {navigationItems.map((item) => (
          <div key={item.label}>
            <Button
              variant="ghost"
              className={cn(
                'w-full justify-start gap-3 h-10',
                collapsed && 'justify-center px-2',
                location.pathname === item.href && 'bg-primary/10 text-primary'
              )}
              onClick={() => {
                if (item.children) {
                  toggleExpanded(item.label);
                } else {
                  handleNavigation(item.href, false);
                }
              }}
            >
              <item.icon className="h-5 w-5 flex-shrink-0" />
              {!collapsed && (
                <>
                  <span className="flex-1 text-left">{item.label}</span>
                  {item.badge && (
                    <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                      {item.badge}
                    </span>
                  )}
                  {item.children && (
                    <ChevronRight
                      className={cn(
                        'h-4 w-4 transition-transform',
                        expandedItems.includes(item.label) && 'rotate-90'
                      )}
                    />
                  )}
                </>
              )}
            </Button>

            {/* Submenu */}
            {item.children && !collapsed && expandedItems.includes(item.label) && (
              <div className="ml-4 mt-1 space-y-1 border-l border-border pl-2">
                {item.children.map((child) => (
                  <Button
                    key={child.label}
                    variant="ghost"
                    className={cn(
                      "w-full justify-start gap-3 h-9 text-sm",
                      location.pathname === child.href && 'bg-primary/10 text-primary'
                    )}
                    onClick={() => handleNavigation(child.href, false)}
                  >
                    <child.icon className="h-4 w-4 flex-shrink-0" />
                    <span className="flex-1 text-left">{child.label}</span>
                  </Button>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-border bg-card">
          <div className="text-xs text-muted-foreground">
            <p className="font-semibold">System Status</p>
            <div className="flex items-center gap-2 mt-1">
              <div className="w-2 h-2 bg-success rounded-full animate-pulse-subtle" />
              <span>All systems operational</span>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
