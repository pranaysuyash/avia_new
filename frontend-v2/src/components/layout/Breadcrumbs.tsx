import { ChevronRight, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
}

export function Breadcrumbs({ items }: BreadcrumbsProps) {
  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm">
      <Button
        variant="ghost"
        size="sm"
        className="h-8 px-2"
        aria-label="Home"
      >
        <Home className="h-4 w-4" />
      </Button>

      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        
        return (
          <div key={index} className="flex items-center gap-2">
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
            
            {isLast ? (
              <span className="font-medium text-foreground">
                {item.label}
              </span>
            ) : (
              <Button
                variant="ghost"
                size="sm"
                className="h-8 px-2 text-muted-foreground hover:text-foreground"
              >
                {item.label}
              </Button>
            )}
          </div>
        );
      })}
    </nav>
  );
}
