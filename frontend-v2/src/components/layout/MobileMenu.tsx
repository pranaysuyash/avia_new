import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  LayoutDashboard,
  Upload,
  FileText,
  Brain,
  Users,
  Search,
  Settings,
  Mic,
  Video,
  Stethoscope,
  Scale,
  TrendingUp,
  ChevronRight,
} from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';

interface MobileMenuProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
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
    href: '/',
  },
  {
    icon: Upload,
    label: 'Media Ingestion',
    href: '/upload',
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

export function MobileMenu({ open, onOpenChange }: MobileMenuProps) {
  const [expandedItems, setExpandedItems] = useState<string[]>([]);

  const toggleExpanded = (label: string) => {
    setExpandedItems(prev =>
      prev.includes(label)
        ? prev.filter(item => item !== label)
        : [...prev, label]
    );
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="left" className="w-80 p-0">
        <SheetHeader className="p-6 pb-4">
          <SheetTitle className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600" />
            <span>AI Media Platform</span>
          </SheetTitle>
        </SheetHeader>

        <Separator />

        <ScrollArea className="h-[calc(100vh-8rem)]">
          <nav className="p-4 space-y-1">
            {navigationItems.map((item) => (
              <div key={item.label}>
                <Button
                  variant="ghost"
                  className="w-full justify-start gap-3 h-10"
                  onClick={() => item.children && toggleExpanded(item.label)}
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" />
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
                </Button>

                {/* Submenu */}
                {item.children && expandedItems.includes(item.label) && (
                  <div className="ml-4 mt-1 space-y-1 border-l border-border pl-2">
                    {item.children.map((child) => (
                      <Button
                        key={child.label}
                        variant="ghost"
                        className="w-full justify-start gap-3 h-9 text-sm"
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
        </ScrollArea>

        <Separator />

        <div className="p-4">
          <div className="text-xs text-muted-foreground">
            <p className="font-semibold">System Status</p>
            <div className="flex items-center gap-2 mt-1">
              <div className="w-2 h-2 bg-success rounded-full animate-pulse-subtle" />
              <span>All systems operational</span>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
