import { useEffect } from 'react'

const SITE = 'MERIT'

export function usePageMeta(title: string, description?: string) {
  useEffect(() => {
    document.title = title ? `${title} · ${SITE}` : SITE

    let metaDesc = document.querySelector<HTMLMetaElement>('meta[name="description"]')
    if (!metaDesc) {
      metaDesc = document.createElement('meta')
      metaDesc.setAttribute('name', 'description')
      document.head.appendChild(metaDesc)
    }
    if (description) metaDesc.setAttribute('content', description)

    return () => {
      document.title = SITE
    }
  }, [title, description])
}
