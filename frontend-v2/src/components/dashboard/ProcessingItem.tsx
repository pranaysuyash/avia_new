import { Play, Eye, FileText, Loader2, type LucideIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface ProcessingItemProps {
  name: string
  type: string
  status: 'completed' | 'processing' | 'failed'
  accuracy: number
  duration: string
  aiFeatures: string[]
  icon: LucideIcon
  color: 'blue' | 'purple' | 'green' | 'orange'
}

const colorClasses = {
  blue: {
    gradient: 'from-blue-500 to-cyan-500',
    badge: 'bg-blue-100 text-blue-700'
  },
  purple: {
    gradient: 'from-purple-500 to-violet-500',
    badge: 'bg-purple-100 text-purple-700'
  },
  green: {
    gradient: 'from-green-500 to-emerald-500',
    badge: 'bg-green-100 text-green-700'
  },
  orange: {
    gradient: 'from-orange-500 to-amber-500',
    badge: 'bg-orange-100 text-orange-700'
  }
}

export function ProcessingItem({
  name,
  type,
  status,
  accuracy,
  duration,
  aiFeatures,
  icon: Icon,
  color
}: ProcessingItemProps) {
  return (
    <div className="p-6 hover:bg-slate-50 transition-colors">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="flex items-start space-x-4 flex-1">
          <div className={cn(
            "p-3 rounded-xl bg-gradient-to-r flex-shrink-0",
            colorClasses[color].gradient
          )}>
            <Icon className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-3 mb-1 flex-wrap">
              <div className="font-semibold text-slate-900 truncate">{name}</div>
              <Badge className={colorClasses[color].badge}>
                {type}
              </Badge>
            </div>
            <div className="text-sm text-slate-500 mb-2">
              {duration} • {status}
            </div>
            <div className="flex flex-wrap gap-1">
              {aiFeatures.map((feature, idx) => (
                <span
                  key={idx}
                  className="text-xs px-2 py-1 bg-slate-100 text-slate-600 rounded-md"
                >
                  {feature}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-6 flex-shrink-0">
          {accuracy > 0 && (
            <div className="flex items-center space-x-3">
              <div className="text-right">
                <div className="text-sm font-semibold text-slate-900">Accuracy</div>
                <div className="text-xs text-slate-500">AI Confidence</div>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-24 bg-slate-200 rounded-full h-2">
                  <div
                    className={cn(
                      "h-2 rounded-full",
                      accuracy > 98 ? 'bg-green-500' :
                      accuracy > 95 ? 'bg-blue-500' : 'bg-orange-500'
                    )}
                    style={{ width: `${accuracy}%` }}
                  />
                </div>
                <span className={cn(
                  "text-sm font-bold",
                  accuracy > 98 ? 'text-green-600' :
                  accuracy > 95 ? 'text-blue-600' : 'text-orange-600'
                )}>
                  {accuracy}%
                </span>
              </div>
            </div>
          )}

          {status === 'processing' && (
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
          )}

          <div className="flex space-x-2">
            <Button size="sm" variant="outline">
              <Play className="w-3 h-3" />
            </Button>
            <Button size="sm" variant="outline">
              <Eye className="w-3 h-3" />
            </Button>
            <Button size="sm" variant="outline">
              <FileText className="w-3 h-3" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
