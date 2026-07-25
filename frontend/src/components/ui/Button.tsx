import React from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'destructive' | 'ghost'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: 'bg-soft-gold text-deep-navy hover:opacity-90',
  secondary: 'bg-white border border-light-grey text-deep-navy hover:bg-warm-cream/20',
  outline: 'border border-soft-gold text-soft-gold hover:bg-soft-gold/10',
  destructive: 'bg-destructive text-white hover:opacity-90',
  ghost: 'text-cool-grey hover:text-deep-navy',
}

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'text-xs px-3 py-1.5 h-8',
  md: 'text-sm px-4 py-2 h-10',
  lg: 'text-base px-6 py-3 h-12',
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', ...props }, ref) => {
    const baseClasses = 'inline-flex items-center justify-center font-body font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
    const variantClass = variantClasses[variant]
    const sizeClass = sizeClasses[size]
    const finalClassName = [baseClasses, variantClass, sizeClass, className].filter(Boolean).join(' ')

    return (
      <button
        className={finalClassName}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button }
