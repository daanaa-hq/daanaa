import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import LampMark from '../components/LampMark'

export default function NotFound() {
  usePageMeta('Page Not Found')
  return (
    <div className="min-h-[100dvh] bg-warm-cream flex items-center justify-center px-6">
      <div className="text-center max-w-[420px]">
        <div className="flex justify-center mb-6 opacity-30">
          <LampMark size="xl" tier="Spark" />
        </div>
        <h1 className="font-display italic text-deep-navy leading-[1.05]">
          Page not found
        </h1>
        <p className="mt-4 font-body text-body-lg text-cool-grey leading-[1.7]">
          The page you're looking for doesn't exist or may have moved.
        </p>
        <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            to="/directory"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-deep-navy text-warm-cream font-body text-body font-medium hover:bg-deep-navy/90 transition-colors"
          >
            Browse nonprofits
          </Link>
          <Link
            to="/"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg border border-light-grey text-deep-navy font-body text-body font-medium hover:bg-deep-navy/5 transition-colors"
          >
            Go home
          </Link>
        </div>
      </div>
    </div>
  )
}
