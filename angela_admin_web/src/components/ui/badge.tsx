import * as React from "react"

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "secondary" | "outline"
}

function Badge({ className = "", variant = "default", ...props }: BadgeProps) {
  const variants = {
    default: "bg-purple-600 text-white",
    secondary: "bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100",
    outline: "border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300"
  }

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors ${variants[variant]} ${className}`}
      {...props}
    />
  )
}

export { Badge }
