# Design Tokens Documentation

This document provides comprehensive documentation for the design token system used in the Modern Frontend Revamp project.

## Overview

Our design system uses CSS custom properties (variables) as design tokens, providing a consistent and maintainable approach to styling across the application. All tokens support both light and dark themes with automatic system preference detection.

## Color Tokens

### Base Colors

#### Light Theme
- `--background`: Main background color (white)
- `--foreground`: Main text color (dark gray)
- `--card`: Card background color
- `--card-foreground`: Card text color
- `--popover`: Popover background color
- `--popover-foreground`: Popover text color

#### Dark Theme
- Automatically switches when dark mode is enabled
- Maintains proper contrast ratios for accessibility

### Semantic Colors

#### Primary
- `--primary`: Primary brand color (blue)
- `--primary-foreground`: Text color on primary background
- Usage: Primary buttons, links, important UI elements

#### Secondary
- `--secondary`: Secondary color (light gray/dark gray)
- `--secondary-foreground`: Text color on secondary background
- Usage: Secondary buttons, less prominent UI elements

#### Accent
- `--accent`: Accent color for highlights
- `--accent-foreground`: Text color on accent background
- Usage: Hover states, active states, highlights

#### Destructive
- `--destructive`: Error/danger color (red)
- `--destructive-foreground`: Text color on destructive background
- Usage: Delete buttons, error messages, warnings

#### Success
- `--success`: Success color (green)
- `--success-foreground`: Text color on success background
- Usage: Success messages, positive feedback

#### Warning
- `--warning`: Warning color (orange/yellow)
- `--warning-foreground`: Text color on warning background
- Usage: Warning messages, caution indicators

#### Info
- `--info`: Information color (blue)
- `--info-foreground`: Text color on info background
- Usage: Information messages, help text

### UI Element Colors

- `--border`: Border color for UI elements
- `--input`: Input field border color
- `--ring`: Focus ring color for accessibility
- `--muted`: Muted background color
- `--muted-foreground`: Muted text color

### Gradient Tokens

- `--gradient-primary`: Primary gradient (blue to purple)
- `--gradient-secondary`: Secondary gradient (light grays)
- `--gradient-accent`: Accent gradient (green shades)

**Usage in Tailwind:**
```tsx
<div className="gradient-primary">...</div>
<h1 className="text-gradient-primary">...</h1>
```

## Spacing Tokens

Consistent spacing scale for margins, padding, and gaps:

- `--spacing-xs`: 0.25rem (4px)
- `--spacing-sm`: 0.5rem (8px)
- `--spacing-md`: 1rem (16px)
- `--spacing-lg`: 1.5rem (24px)
- `--spacing-xl`: 2rem (32px)
- `--spacing-2xl`: 3rem (48px)
- `--spacing-3xl`: 4rem (64px)

**Usage in Tailwind:**
```tsx
<div className="p-md m-lg gap-sm">...</div>
```

## Border Radius Tokens

Consistent border radius for rounded corners:

- `--radius-sm`: 0.25rem (4px) - Small elements
- `--radius-md`: 0.375rem (6px) - Default
- `--radius-lg`: 0.5rem (8px) - Cards, containers
- `--radius-xl`: 0.75rem (12px) - Large containers
- `--radius-2xl`: 1rem (16px) - Extra large
- `--radius-full`: 9999px - Fully rounded (pills, avatars)

**Usage in Tailwind:**
```tsx
<div className="rounded-lg">...</div>
<button className="rounded-full">...</button>
```

## Shadow Tokens

Elevation system using box shadows:

- `--shadow-sm`: Subtle shadow for slight elevation
- `--shadow-md`: Medium shadow for cards (default)
- `--shadow-lg`: Large shadow for modals, dropdowns
- `--shadow-xl`: Extra large shadow for prominent elements
- `--shadow-2xl`: Maximum shadow for floating elements

**Note:** Shadows automatically adjust for dark mode with increased opacity.

**Usage in Tailwind:**
```tsx
<div className="shadow-md">...</div>
<div className="shadow-xl">...</div>
```

## Typography Tokens

### Font Families

- `--font-sans`: System sans-serif font stack
  - `ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`
- `--font-mono`: Monospace font stack for code
  - `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace`

**Usage in Tailwind:**
```tsx
<p className="font-sans">Regular text</p>
<code className="font-mono">Code snippet</code>
```

## Animation Tokens

### Transition Durations

- `--transition-fast`: 150ms - Quick interactions
- `--transition-base`: 200ms - Default transitions
- `--transition-slow`: 300ms - Smooth, noticeable transitions

**Usage in Tailwind:**
```tsx
<div className="transition-all duration-fast">...</div>
<div className="transition-colors duration-base">...</div>
```

### Predefined Animations

Available via Tailwind classes:

- `animate-fade-in`: Fade in effect
- `animate-fade-out`: Fade out effect
- `animate-slide-up`: Slide up from bottom
- `animate-slide-down`: Slide down from top
- `animate-slide-left`: Slide in from right
- `animate-slide-right`: Slide in from left
- `animate-scale-in`: Scale up with fade
- `animate-scale-out`: Scale down with fade
- `animate-pulse-subtle`: Subtle pulsing effect
- `animate-spin-slow`: Slow rotation
- `animate-bounce-subtle`: Subtle bounce effect

**Usage:**
```tsx
<div className="animate-fade-in">...</div>
<div className="animate-slide-up">...</div>
```

## Z-Index Tokens

Layering system for stacking contexts:

- `--z-dropdown`: 1000 - Dropdown menus
- `--z-sticky`: 1020 - Sticky headers
- `--z-fixed`: 1030 - Fixed elements
- `--z-modal-backdrop`: 1040 - Modal backdrops
- `--z-modal`: 1050 - Modal dialogs
- `--z-popover`: 1060 - Popovers
- `--z-tooltip`: 1070 - Tooltips (highest)

**Usage in Tailwind:**
```tsx
<div className="z-modal">...</div>
<div className="z-tooltip">...</div>
```

## Theme System

### Theme Provider

Wrap your app with the `ThemeProvider` to enable theme switching:

```tsx
import { ThemeProvider } from '@/lib/theme-provider'

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="app-theme">
      {/* Your app */}
    </ThemeProvider>
  )
}
```

### Using the Theme Hook

```tsx
import { useTheme } from '@/lib/theme-provider'

function MyComponent() {
  const { theme, setTheme } = useTheme()
  
  return (
    <button onClick={() => setTheme('dark')}>
      Current theme: {theme}
    </button>
  )
}
```

### Theme Toggle Component

Use the pre-built `ThemeToggle` component:

```tsx
import { ThemeToggle } from '@/components/theme-toggle'

function Header() {
  return (
    <header>
      <ThemeToggle />
    </header>
  )
}
```

## Accessibility Features

### Focus Visible

All interactive elements have accessible focus indicators:

```css
*:focus-visible {
  outline: none;
  ring: 2px solid hsl(var(--ring));
  ring-offset: 2px;
}
```

### Reduced Motion

Respects user's motion preferences:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Color Contrast

All color combinations meet WCAG 2.1 AA standards:
- Normal text: 4.5:1 contrast ratio
- Large text: 3:1 contrast ratio
- UI components: 3:1 contrast ratio

## Utility Classes

### Glassmorphism

```tsx
<div className="glass">
  {/* Frosted glass effect */}
</div>
```

### Custom Scrollbar

```tsx
<div className="scrollbar-thin overflow-auto">
  {/* Styled scrollbar */}
</div>
```

### Text Gradients

```tsx
<h1 className="text-gradient-primary">
  Gradient Text
</h1>
```

## Best Practices

### 1. Use Semantic Tokens

❌ Don't use raw colors:
```tsx
<button className="bg-blue-500">Click me</button>
```

✅ Use semantic tokens:
```tsx
<button className="bg-primary text-primary-foreground">Click me</button>
```

### 2. Maintain Consistency

Always use design tokens instead of arbitrary values:

❌ Avoid:
```tsx
<div className="p-[13px] rounded-[7px]">...</div>
```

✅ Prefer:
```tsx
<div className="p-md rounded-lg">...</div>
```

### 3. Respect Theme Context

Components should work in both light and dark themes without modification.

### 4. Use Appropriate Elevation

- `shadow-sm`: Subtle elevation (cards on page)
- `shadow-md`: Standard elevation (interactive cards)
- `shadow-lg`: High elevation (dropdowns, popovers)
- `shadow-xl`: Maximum elevation (modals, dialogs)

### 5. Animation Guidelines

- Use `duration-fast` for micro-interactions (hover, focus)
- Use `duration-base` for standard transitions (page elements)
- Use `duration-slow` for prominent animations (modals, drawers)

## Extending the Design System

### Adding New Colors

1. Add CSS variable in `src/index.css`:
```css
:root {
  --my-color: 200 100% 50%;
}
```

2. Add to Tailwind config:
```js
colors: {
  'my-color': 'hsl(var(--my-color))',
}
```

### Adding New Animations

1. Define keyframes in Tailwind config:
```js
keyframes: {
  myAnimation: {
    '0%': { /* start state */ },
    '100%': { /* end state */ },
  },
}
```

2. Add animation utility:
```js
animation: {
  'my-animation': 'myAnimation 1s ease-in-out',
}
```

## Resources

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [shadcn/ui Documentation](https://ui.shadcn.com)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [CSS Custom Properties](https://developer.mozilla.org/en-US/docs/Web/CSS/--*)

## Support

For questions or issues with the design system, please refer to the main project documentation or contact the frontend team.
