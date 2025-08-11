import * as React from "react"

interface CollapsibleProps {
  children: React.ReactNode
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

export const Collapsible = React.forwardRef<
  HTMLDivElement,
  CollapsibleProps
>(({ children, open = false, onOpenChange, ...props }, ref) => {
  const [isOpen, setIsOpen] = React.useState(open)

  React.useEffect(() => {
    setIsOpen(open)
  }, [open])

  return (
    <div ref={ref} {...props}>
      {React.Children.map(children, child => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, { isOpen, setIsOpen, onOpenChange } as any)
        }
        return child
      })}
    </div>
  )
})

Collapsible.displayName = "Collapsible"

export const CollapsibleTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & { isOpen?: boolean; setIsOpen?: (open: boolean) => void; onOpenChange?: (open: boolean) => void }
>(({ children, isOpen, setIsOpen, onOpenChange, ...props }, ref) => {
  const handleClick = () => {
    const newState = !isOpen
    setIsOpen?.(newState)
    onOpenChange?.(newState)
  }

  return (
    <button ref={ref} onClick={handleClick} {...props}>
      {children}
    </button>
  )
})

CollapsibleTrigger.displayName = "CollapsibleTrigger"

export const CollapsibleContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { isOpen?: boolean }
>(({ children, isOpen, ...props }, ref) => {
  if (!isOpen) return null

  return (
    <div ref={ref} {...props}>
      {children}
    </div>
  )
})

CollapsibleContent.displayName = "CollapsibleContent"