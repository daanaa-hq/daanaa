import React from 'react'

interface DiscoveryWhyHereProps {
  explanation: string
  className?: string
}

export const DiscoveryWhyHere: React.FC<DiscoveryWhyHereProps> = ({
  explanation,
  className = '',
}) => {
  return (
    <p className={`text-sm text-gray-600 dark:text-gray-400 ${className}`}>
      {explanation}
    </p>
  )
}
