import { TrendingUp, TrendingDown, type LucideIcon } from "lucide-react"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface StatsCardProps {
  label: string
  value: string
  change: string
  icon: LucideIcon
  color: 'blue' | 'purple' | 'green' | 'orange' | 'cyan' | 'pink' | 'indigo' | 'teal'
  trend?: 'up' | 'down'
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

export function StatsCard({ label, value, change, icon: Icon, color, trend = 'up' }: StatsCardProps) {
  const isPositive = trend === 'up'
  
  return (
    <Card className="p-6 hover:shadow-lg transition-all hover:border-slate-300">
      <div className="flex items-center justify-between mb-4">
        <div className={cn(
          "p-3 rounded-xl bg-gradient-to-r",
          colorClasses[color]
        )}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div className={cn(
          "flex items-center space-x-1 text-sm font-semibold",
          isPositive ? "text-green-600" : "text-red-600"
        )}>
          {isPositive ? (
            <TrendingUp className="w-3 h-3" />
          ) : (
            <TrendingDown className="w-3 h-3" />
          )}
          <span>{change}</span>
        </div>
      </div>
      <div className="text-3xl font-bold text-slate-900 mb-2">{value}</div>
      <div className="text-sm text-slate-500">{label}</div>
    </Card>
  )
}
