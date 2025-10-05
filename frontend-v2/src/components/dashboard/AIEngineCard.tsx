import { CheckCircle2, type LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

interface AIEngineCardProps {
  name: string
  icon: LucideIcon
  status: 'active' | 'inactive' | 'error'
  jobs: number
  color: 'blue' | 'purple' | 'green' | 'orange' | 'cyan' | 'pink' | 'indigo' | 'teal'
}

const colorClasses = {
  blue: 'from-blue-500 to-blue-600',
  purple: 'from-purple-500 to-purple-600',
  green: 'from-green-500 to-green-600',
  orange: 'from-orange-500 to-orange-600',
  cyan: 'from-cyan-500 to-cyan-600',
  pink: 'from-pink-500 to-pink-600',
  indigo: 'from-indigo-500 to-indigo-600',
  teal: 'from-teal-500 to-teal-600'
}

export function AIEngineCard({ name, icon: Icon, status, jobs, color }: AIEngineCardProps) {
  return (
    <div className="p-4 rounded-lg border border-slate-200 hover:border-slate-300 transition-colors hover:shadow-md">
      <div className="flex items-center justify-between mb-3">
        <div className={cn(
          "p-2 rounded-lg bg-gradient-to-r",
          colorClasses[color]
        )}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <div className="flex items-center space-x-1">
          <CheckCircle2 className={cn(
            "w-4 h-4",
            status === 'active' ? 'text-green-500' : 
            status === 'error' ? 'text-red-500' : 'text-slate-400'
          )} />
          <span className={cn(
            "text-xs font-medium",
            status === 'active' ? 'text-green-600' : 
            status === 'error' ? 'text-red-600' : 'text-slate-500'
          )}>
            {status}
          </span>
        </div>
      </div>
      <div className="text-sm font-semibold text-slate-900 mb-1">{name}</div>
      <div className="text-xs text-slate-500">{jobs} active jobs</div>
    </div>
  )
}
