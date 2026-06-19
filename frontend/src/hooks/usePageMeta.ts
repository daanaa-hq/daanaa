import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

const SITE = 'Daanaa'
const SITE_URL = 'https://daanaa.org'

function setMeta(selector: string, attr: string, value: string) {
  let el = document.querySelector<HTMLMetaElement>(selector)
  if (!el) {
    el = document.createElement('meta')
    const [attrName, attrVal] = selector.match(/\[([^\]]+)="([^"]+)"\]/)
      ? selector.replace(/^meta\[/, '').replace(/\]$/, '').split('=').map(s => s.replace(/"/g, ''))
      : [attr, value]
    el.setAttribute(attrName, attrVal)
    document.head.appendChild(el)
  }
  el.setAttribute(attr, value)
}

function setCanonical(url: string) {
  let el = document.querySelector<HTMLLinkElement>('link[rel="canonical"]')
  if (!el) {
    el = document.createElement('link')
    el.rel = 'canonical'
    document.head.appendChild(el)
  }
  el.href = url
}

interface PageMetaOptions {
  description?: string
  canonical?: string
  ogImage?: string
  twitterCard?: 'summary' | 'summary_large_image'
}

export function usePageMeta(title: string, descriptionOrOptions?: string | PageMetaOptions) {
  const location = useLocation()

  const options: PageMetaOptions = typeof descriptionOrOptions === 'string'
    ? { description: descriptionOrOptions }
    : (descriptionOrOptions || {})

  const { description = options.description, canonical, ogImage, twitterCard = 'summary' } = options

  useEffect(() => {
    const fullTitle = title ? `${title} · ${SITE}` : SITE
    document.title = fullTitle

    if (description) {
      setMeta('meta[name="description"]', 'content', description)
      setMeta('meta[property="og:description"]', 'content', description)
      setMeta('meta[name="twitter:description"]', 'content', description)
    }

    setMeta('meta[property="og:title"]', 'content', fullTitle)
    setMeta('meta[name="twitter:title"]', 'content', fullTitle)

    const canonicalUrl = canonical || `${SITE_URL}${location.pathname}`
    setCanonical(canonicalUrl)

    if (ogImage) {
      setMeta('meta[property="og:image"]', 'content', ogImage)
      setMeta('meta[property="twitter:image"]', 'content', ogImage)
    }

    setMeta('meta[name="twitter:card"]', 'content', twitterCard)

    return () => {
      document.title = SITE
    }
  }, [title, description, canonical, ogImage, twitterCard, location.pathname])
}
