import { useEffect } from 'react'

const SITE = 'MERIT'

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

export function usePageMeta(title: string, description?: string) {
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

    return () => {
      document.title = SITE
    }
  }, [title, description])
}
