import { getActionRowLinks } from '../utils/actionRow'

describe('getActionRowLinks', () => {
  describe('website gate', () => {
    it('shows the website link when status is ok', () => {
      const r = getActionRowLinks({ website_status: 'ok', website: 'example.org', donate_url_status: null, donate_url: null, volunteer_url: null })
      expect(r.websiteUrl).toBe('https://example.org/')
      expect(r.isWebsiteBeta).toBe(false)
    })

    it('shows the website link when status is beta, and flags it as beta', () => {
      const r = getActionRowLinks({ website_status: 'beta', website: 'example.org', donate_url_status: null, donate_url: null, volunteer_url: null })
      expect(r.websiteUrl).toBe('https://example.org/')
      expect(r.isWebsiteBeta).toBe(true)
    })

    it('hides the website link for known-bad statuses (dead, redirected, unknown)', () => {
      for (const status of ['dead', 'redirected', 'unknown']) {
        const r = getActionRowLinks({ website_status: status, website: 'example.org', donate_url_status: null, donate_url: null, volunteer_url: null })
        expect(r.websiteUrl).toBeNull()
      }
    })

    it('shows an unchecked website (NULL status) and flags it as beta — 253bf0b51ba', () => {
      const r = getActionRowLinks({ website_status: null, website: 'example.org', donate_url_status: null, donate_url: null, volunteer_url: null })
      expect(r.websiteUrl).toBe('https://example.org/')
      expect(r.isWebsiteBeta).toBe(true)
    })
  })

  describe('donate gate (T3: only beta/claimed, never confidence)', () => {
    it('shows Donate when status is beta and a URL exists', () => {
      const r = getActionRowLinks({ website_status: null, website: null, donate_url_status: 'beta', donate_url: 'https://give.example.org', volunteer_url: null })
      expect(r.donateUrl).toBe('https://give.example.org/')
      expect(r.isDonateBeta).toBe(true)
    })

    it('shows Donate when status is claimed, and does not flag it as beta', () => {
      const r = getActionRowLinks({ website_status: null, website: null, donate_url_status: 'claimed', donate_url: 'https://give.example.org', volunteer_url: null })
      expect(r.donateUrl).toBe('https://give.example.org/')
      expect(r.isDonateBeta).toBe(false)
    })

    it.each(['dead', 'no_link_found', 'blocked_or_restricted', 'mismatch', 'rejected', 'withheld', 'human_review', 'unknown', null])(
      'hides Donate for status=%s even when a URL exists (fail-closed trust posture)',
      (status) => {
        const r = getActionRowLinks({ website_status: null, website: null, donate_url_status: status, donate_url: 'https://give.example.org', volunteer_url: null })
        expect(r.donateUrl).toBeNull()
      }
    )

    it('hides Donate when status is beta but the URL is missing (real data case found during T5 visual testing)', () => {
      const r = getActionRowLinks({ website_status: null, website: null, donate_url_status: 'beta', donate_url: null, volunteer_url: null })
      expect(r.donateUrl).toBeNull()
    })
  })

  describe('volunteer gate', () => {
    it('shows Volunteer whenever a volunteer_url is present, regardless of any status field', () => {
      const r = getActionRowLinks({ website_status: null, website: null, donate_url_status: null, donate_url: null, volunteer_url: 'volunteer.example.org' })
      expect(r.volunteerUrl).toBe('https://volunteer.example.org/')
    })

    it('hides Volunteer when volunteer_url is null or empty', () => {
      expect(getActionRowLinks({ website_status: null, website: null, donate_url_status: null, donate_url: null, volunteer_url: null }).volunteerUrl).toBeNull()
      expect(getActionRowLinks({ website_status: null, website: null, donate_url_status: null, donate_url: null, volunteer_url: '' }).volunteerUrl).toBeNull()
    })
  })

  describe('hasAnyLink / null-org safety', () => {
    it('hasAnyLink is true when at least one of the three links is present', () => {
      const r = getActionRowLinks({ website_status: 'ok', website: 'example.org', donate_url_status: null, donate_url: null, volunteer_url: null })
      expect(r.hasAnyLink).toBe(true)
    })

    it('hasAnyLink is false when none are present -- the empty-action-row case the "Give by EIN" fallback exists for', () => {
      const r = getActionRowLinks({ website_status: null, website: null, donate_url_status: null, donate_url: null, volunteer_url: null })
      expect(r.hasAnyLink).toBe(false)
    })

    it('does not throw on a null/undefined org (component may call this before data loads)', () => {
      expect(() => getActionRowLinks(null)).not.toThrow()
      expect(() => getActionRowLinks(undefined)).not.toThrow()
      expect(getActionRowLinks(null).hasAnyLink).toBe(false)
    })
  })

  describe('malicious/malformed URL rejection (security boundary)', () => {
    it('rejects javascript: URLs in donate_url', () => {
      const r = getActionRowLinks({ website_status: null, website: null, donate_url_status: 'claimed', donate_url: 'javascript:alert(1)', volunteer_url: null })
      expect(r.donateUrl).toBeNull()
    })

    it('rejects javascript: URLs in volunteer_url', () => {
      const r = getActionRowLinks({ website_status: null, website: null, donate_url_status: null, donate_url: null, volunteer_url: 'javascript:alert(1)' })
      expect(r.volunteerUrl).toBeNull()
    })
  })
})
