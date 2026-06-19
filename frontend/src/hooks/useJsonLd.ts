import { useEffect } from 'react'

export interface JsonLdSchema {
  '@context': string
  '@type': string
  [key: string]: any
}

export function useJsonLd(schema: JsonLdSchema) {
  useEffect(() => {
    let script = document.querySelector<HTMLScriptElement>('script[type="application/ld+json"]')
    if (!script) {
      script = document.createElement('script')
      script.type = 'application/ld+json'
      document.head.appendChild(script)
    }
    script.textContent = JSON.stringify(schema)

    return () => {
      if (script?.parentNode) {
        script.parentNode.removeChild(script)
      }
    }
  }, [schema])
}

export function organizationSchema(org: {
  name: string
  ein?: string
  description?: string
  logo?: string
  url: string
  address?: string
  state?: string
}): JsonLdSchema {
  return {
    '@context': 'https://schema.org',
    '@type': 'LocalBusiness',
    name: org.name,
    url: org.url,
    ...(org.description && { description: org.description }),
    ...(org.logo && { image: org.logo }),
    ...(org.ein && { identifier: org.ein }),
    ...(org.state && { areaServed: org.state }),
    sameAs: `https://daanaa.org/organizations/${org.ein || ''}`.trim(),
  }
}

export function organizationSearchResultSchema(orgs: Array<{
  name: string
  url: string
  ein?: string
}>): JsonLdSchema {
  return {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: 'Nonprofit Organization Search Results',
    description: 'Search results for nonprofit organizations',
    mainEntity: {
      '@type': 'ItemList',
      itemListElement: orgs.slice(0, 10).map((org, index) => ({
        '@type': 'ListItem',
        position: index + 1,
        url: org.url,
        name: org.name,
      })),
    },
  }
}

export function categoryPageSchema(category: {
  name: string
  description?: string
  url: string
  itemCount?: number
}): JsonLdSchema {
  return {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: `${category.name} Organizations - Daanaa`,
    url: category.url,
    ...(category.description && { description: category.description }),
    ...(category.itemCount && { numberOfItems: category.itemCount }),
    inLanguage: 'en-US',
    isPartOf: {
      '@type': 'WebSite',
      name: 'Daanaa',
      url: 'https://daanaa.org',
    },
  }
}

export function faqPageSchema(faqs: Array<{
  question: string
  answer: string
}>): JsonLdSchema {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map(faq => ({
      '@type': 'Question',
      name: faq.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: faq.answer,
      },
    })),
  }
}

export function websiteSchema(site: {
  name: string
  url: string
  description: string
  logo?: string
}): JsonLdSchema {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: site.name,
    url: site.url,
    description: site.description,
    ...(site.logo && { image: site.logo }),
    potentialAction: {
      '@type': 'SearchAction',
      target: {
        '@type': 'EntryPoint',
        urlTemplate: `${site.url}/directory?q={search_term_string}`,
      },
      'query-input': 'required name=search_term_string',
    },
  }
}

export function breadcrumbSchema(items: Array<{
  name: string
  url: string
}>): JsonLdSchema {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.url,
    })),
  }
}
