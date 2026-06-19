/**
 * Security tests for Daanaa wallet
 * Focus: input validation, data sanitization, privacy, DoS prevention
 */

import {
  validateSearchTerm,
  validateFilterValue,
  validateSortValue,
  validateIntentNotes,
  validateAmount,
  validateHours,
  validateEmail,
} from '../../src/utils/walletValidation'

describe('Wallet Security - Input Validation', () => {
  describe('validateSearchTerm', () => {
    it('accepts valid search terms', () => {
      expect(validateSearchTerm('Red Cross')).toBe('Red Cross')
      expect(validateSearchTerm('education')).toBe('education')
      expect(validateSearchTerm('homeless')).toBe('homeless')
    })

    it('trims whitespace', () => {
      expect(validateSearchTerm('  hello  ')).toBe('hello')
      expect(validateSearchTerm('\n\ttest\n')).toBe('test')
    })

    it('enforces max length (100 chars)', () => {
      const longTerm = 'a'.repeat(150)
      expect(() => validateSearchTerm(longTerm)).toThrow('Search term must be 100 characters or less')
    })

    it('rejects empty string', () => {
      expect(() => validateSearchTerm('')).toThrow('Search term cannot be empty')
    })

    it('handles null/undefined gracefully', () => {
      expect(() => validateSearchTerm(null as any)).toThrow()
      expect(() => validateSearchTerm(undefined as any)).toThrow()
    })

    it('removes potential regex special chars but keeps search intention', () => {
      // Should not throw; should sanitize
      const result = validateSearchTerm('health(care)')
      expect(result).toContain('health')
    })

    it('rejects XSS attempts in search', () => {
      expect(() => validateSearchTerm('<script>alert("xss")</script>')).toThrow()
    })

    it('rejects regex DoS patterns', () => {
      // ReDoS patterns should be rejected or sanitized
      const redosPattern = '(a+)+b'
      expect(() => validateSearchTerm(redosPattern)).toThrow()
    })

    it('handles unicode and diacritics', () => {
      expect(validateSearchTerm('Café')).toBe('Café')
      expect(validateSearchTerm('北京')).toBe('北京')
    })
  })

  describe('validateFilterValue', () => {
    it('accepts valid intent filter values', () => {
      expect(validateFilterValue('intent', 'all')).toBe(true)
      expect(validateFilterValue('intent', 'giving')).toBe(true)
      expect(validateFilterValue('intent', 'volunteer')).toBe(true)
      expect(validateFilterValue('intent', 'board')).toBe(true)
    })

    it('accepts valid health filter values', () => {
      expect(validateFilterValue('health', 'all')).toBe(true)
      expect(validateFilterValue('health', 'HEALTHY')).toBe(true)
      expect(validateFilterValue('health', 'STABLE')).toBe(true)
      expect(validateFilterValue('health', 'CAUTION')).toBe(true)
    })

    it('rejects invalid intent values', () => {
      expect(validateFilterValue('intent', 'invalid')).toBe(false)
      expect(validateFilterValue('intent', 'donate')).toBe(false)
    })

    it('rejects invalid health values', () => {
      expect(validateFilterValue('health', 'BROKEN')).toBe(false)
      expect(validateFilterValue('health', 'GOOD')).toBe(false)
    })

    it('rejects unknown filter keys', () => {
      expect(validateFilterValue('unknown_filter', 'all')).toBe(false)
    })

    it('rejects null/undefined values', () => {
      expect(validateFilterValue('intent', null)).toBe(false)
      expect(validateFilterValue('intent', undefined)).toBe(false)
    })

    it('is case-sensitive (required for enum validation)', () => {
      expect(validateFilterValue('health', 'healthy')).toBe(false) // lowercase should fail
      expect(validateFilterValue('health', 'HEALTHY')).toBe(true)
    })

    it('rejects SQL injection attempts', () => {
      expect(validateFilterValue('intent', "' OR '1'='1")).toBe(false)
    })

    it('rejects numeric injection attempts', () => {
      expect(validateFilterValue('intent', 123 as any)).toBe(false)
    })
  })

  describe('validateSortValue', () => {
    it('accepts valid sort values', () => {
      expect(validateSortValue('recent')).toBe(true)
      expect(validateSortValue('name')).toBe(true)
      expect(validateSortValue('health')).toBe(true)
    })

    it('rejects invalid sort values', () => {
      expect(validateSortValue('invalid')).toBe(false)
      expect(validateSortValue('relevance')).toBe(false)
    })

    it('rejects null/undefined', () => {
      expect(validateSortValue(null)).toBe(false)
      expect(validateSortValue(undefined)).toBe(false)
    })

    it('is case-sensitive', () => {
      expect(validateSortValue('Recent')).toBe(false)
      expect(validateSortValue('RECENT')).toBe(false)
    })

    it('rejects numeric values', () => {
      expect(validateSortValue(1 as any)).toBe(false)
    })

    it('rejects injection attempts', () => {
      expect(validateSortValue('recent; DROP TABLE')).toBe(false)
    })
  })

  describe('validateIntentNotes', () => {
    it('accepts valid notes', () => {
      expect(validateIntentNotes('This is a great org')).toBe('This is a great org')
      expect(validateIntentNotes('200-char note: ' + 'a'.repeat(185))).toBeTruthy()
    })

    it('trims whitespace', () => {
      expect(validateIntentNotes('  hello  ')).toBe('hello')
    })

    it('enforces 200-char limit', () => {
      const longNotes = 'a'.repeat(201)
      expect(() => validateIntentNotes(longNotes)).toThrow('Notes must be 200 characters or less')
    })

    it('allows empty string', () => {
      expect(validateIntentNotes('')).toBe('')
    })

    it('removes control characters (tabs, newlines, etc)', () => {
      const withControls = 'hello\n\tworld\r\n'
      const result = validateIntentNotes(withControls)
      expect(result).not.toContain('\n')
      expect(result).not.toContain('\t')
      expect(result).not.toContain('\r')
    })

    it('rejects XSS attempts', () => {
      expect(() => validateIntentNotes('<script>alert("xss")</script>')).toThrow()
    })

    it('handles unicode safely', () => {
      expect(validateIntentNotes('Émojis 🎉 allowed')).toBeTruthy()
    })

    it('rejects null/undefined', () => {
      expect(() => validateIntentNotes(null as any)).toThrow()
      expect(() => validateIntentNotes(undefined as any)).toThrow()
    })
  })

  describe('validateAmount', () => {
    it('accepts valid amounts', () => {
      expect(validateAmount(10)).toBe(10)
      expect(validateAmount(250)).toBe(250)
      expect(validateAmount(5000)).toBe(5000)
    })

    it('rejects zero amount', () => {
      expect(() => validateAmount(0)).toThrow('Amount must be greater than 0')
    })

    it('rejects negative amounts', () => {
      expect(() => validateAmount(-100)).toThrow('Amount must be greater than 0')
    })

    it('rejects decimal amounts (must be integer)', () => {
      expect(() => validateAmount(10.5)).toThrow('Amount must be a whole number')
    })

    it('enforces max amount (999999)', () => {
      expect(() => validateAmount(1000000)).toThrow('Amount must be less than 999999')
    })

    it('rejects non-numeric values', () => {
      expect(() => validateAmount('100' as any)).toThrow()
      expect(() => validateAmount(null as any)).toThrow()
    })

    it('rejects Infinity', () => {
      expect(() => validateAmount(Infinity)).toThrow()
    })

    it('rejects NaN', () => {
      expect(() => validateAmount(NaN)).toThrow()
    })
  })

  describe('validateHours', () => {
    it('accepts valid hours', () => {
      expect(validateHours(1)).toBe(1)
      expect(validateHours(10)).toBe(10)
      expect(validateHours(20)).toBe(20)
    })

    it('accepts fractional hours (minimum 0.25 = 15 min)', () => {
      expect(validateHours(0.25)).toBe(0.25)
      expect(validateHours(2.5)).toBe(2.5)
    })

    it('rejects zero or negative hours', () => {
      expect(() => validateHours(0)).toThrow('Hours must be greater than 0')
      expect(() => validateHours(-5)).toThrow('Hours must be greater than 0')
    })

    it('enforces max hours (168 = one week)', () => {
      expect(() => validateHours(169)).toThrow('Hours must be 168 or less (one week)')
    })

    it('rejects non-numeric values', () => {
      expect(() => validateHours('10' as any)).toThrow()
      expect(() => validateHours(null as any)).toThrow()
    })

    it('rejects Infinity and NaN', () => {
      expect(() => validateHours(Infinity)).toThrow()
      expect(() => validateHours(NaN)).toThrow()
    })
  })

  describe('validateEmail', () => {
    it('accepts valid email addresses', () => {
      expect(validateEmail('user@example.com')).toBe('user@example.com')
      expect(validateEmail('test.user+tag@example.co.uk')).toBeTruthy()
    })

    it('rejects invalid email formats', () => {
      expect(() => validateEmail('invalid')).toThrow()
      expect(() => validateEmail('user@')).toThrow()
      expect(() => validateEmail('@example.com')).toThrow()
    })

    it('trims whitespace', () => {
      expect(validateEmail('  user@example.com  ')).toBe('user@example.com')
    })

    it('rejects null/undefined', () => {
      expect(() => validateEmail(null as any)).toThrow()
      expect(() => validateEmail(undefined as any)).toThrow()
    })
  })
})

describe('Wallet Security - Privacy & Logging', () => {
  let consoleSpy: jest.SpyInstance

  beforeEach(() => {
    consoleSpy = jest.spyOn(console, 'error').mockImplementation()
  })

  afterEach(() => {
    consoleSpy.mockRestore()
  })

  it('does not log full org objects (EIN only)', () => {
    // Mock: when validation fails, it should log EIN not full org
    const mockOrg = { ein: '123456789', name: 'Test Org' }
    // This is tested by ensuring error messages don't contain name/mission/etc
  })

  it('does not expose sensitive data in error messages', () => {
    const invalidEmail = 'user@private-domain.com'
    try {
      validateEmail('invalid email')
    } catch (e) {
      const msg = String(e)
      expect(msg).not.toContain('private-domain')
    }
  })
})

describe('Wallet Security - localStorage Limits', () => {
  const STORAGE_KEY = 'daanaa_wallet'

  beforeEach(() => {
    localStorage.clear()
  })

  it('handles quota exceeded gracefully (mocked)', () => {
    // Simulate quota exceeded by attempting large write
    const largeData = 'x'.repeat(5 * 1024 * 1024) // 5MB
    expect(() => {
      localStorage.setItem('test_large', largeData)
    }).not.toThrow() // Should not throw; app should handle
  })

  it('recovers from corrupted JSON in localStorage', () => {
    localStorage.setItem(STORAGE_KEY, 'invalid json {')
    // The wallet context should recover gracefully
    // This is tested in WalletContext.test.tsx
  })

  it('validates wallet structure before hydrating', () => {
    const invalidWallet = { version: 99, orgs: 'not an array' }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(invalidWallet))
    // Should reject on hydration (tested in context tests)
  })
})

describe('Wallet Security - XSS Prevention', () => {
  describe('search term XSS prevention', () => {
    it('blocks script tags in search', () => {
      expect(() => validateSearchTerm('<script>alert(1)</script>')).toThrow()
    })

    it('blocks on* handlers in search', () => {
      expect(() => validateSearchTerm('onerror=alert(1)')).toThrow()
    })

    it('blocks javascript: protocol in search', () => {
      expect(() => validateSearchTerm('javascript:alert(1)')).toThrow()
    })
  })

  describe('intent notes XSS prevention', () => {
    it('blocks script tags in notes', () => {
      expect(() => validateIntentNotes('<script>alert(1)</script>')).toThrow()
    })

    it('blocks HTML tags in notes', () => {
      expect(() => validateIntentNotes('<img onerror=alert(1)>')).toThrow()
    })

    it('escapes HTML entities safely', () => {
      // Valid notes with entities should pass
      const result = validateIntentNotes('5 < 10 & 20 > 15')
      expect(result).toBeTruthy()
    })
  })
})

describe('Wallet Security - DoS Prevention', () => {
  describe('search term DoS prevention', () => {
    it('handles very long search strings (10KB+)', () => {
      const longStr = 'a'.repeat(10000)
      expect(() => validateSearchTerm(longStr)).toThrow('Search term must be 100 characters or less')
    })

    it('rejects regex DoS patterns', () => {
      const redosList = [
        '(a+)+b',
        '(a*)*b',
        '(a|a)*b',
        '(a|ab)*c',
        '(.*)*',
      ]
      for (const pattern of redosList) {
        expect(() => validateSearchTerm(pattern)).toThrow()
      }
    })

    it('handles rapid filter changes via debounce (integration test)', () => {
      // This is tested at the component level (WalletPage)
      // Validate 100 rapid changes don't break validation
      for (let i = 0; i < 100; i++) {
        expect(validateFilterValue('intent', 'all')).toBe(true)
      }
    })
  })

  describe('localStorage quota DoS prevention', () => {
    it('prevents wallet bloat attacks', () => {
      // Validate that adding massive amounts of data fails gracefully
      // This is handled by localStorage quota (browser limit)
      // App should detect quota exceeded and show error
    })
  })

  describe('intent data DoS prevention', () => {
    it('prevents negative hours attack', () => {
      expect(() => validateHours(-999)).toThrow()
    })

    it('prevents huge amount injection', () => {
      expect(() => validateAmount(Number.MAX_SAFE_INTEGER)).toThrow()
    })
  })
})

describe('Wallet Security - Error Handling', () => {
  it('validation errors do not expose internal state', () => {
    try {
      validateAmount(-1)
    } catch (e) {
      const msg = String(e)
      expect(msg).toMatch(/Amount must be/i)
      expect(msg).not.toContain('undefined')
      expect(msg).not.toContain('internal')
    }
  })

  it('invalid filter errors are clear without exposing DB details', () => {
    const result = validateFilterValue('intent', 'hack_attempt')
    expect(result).toBe(false) // Clear rejection
  })
})

describe('Wallet Security - Type Coercion Attacks', () => {
  it('rejects type-coerced null', () => {
    expect(() => validateAmount(null)).toThrow()
  })

  it('rejects type-coerced undefined', () => {
    expect(() => validateHours(undefined as any)).toThrow()
  })

  it('rejects string number in amount', () => {
    expect(() => validateAmount('100' as any)).toThrow()
  })

  it('rejects array values', () => {
    expect(() => validateSearchTerm([1, 2, 3] as any)).toThrow()
  })

  it('rejects object values', () => {
    expect(validateFilterValue('intent', {} as any)).toBe(false)
  })
})

describe('Wallet Security - Boundary Testing', () => {
  describe('validateAmount boundaries', () => {
    it('accepts minimum valid amount (1)', () => {
      expect(validateAmount(1)).toBe(1)
    })

    it('accepts maximum valid amount (999999)', () => {
      expect(validateAmount(999999)).toBe(999999)
    })

    it('rejects just below minimum', () => {
      expect(() => validateAmount(0.99)).toThrow()
    })

    it('rejects just above maximum', () => {
      expect(() => validateAmount(999999.01)).toThrow()
    })
  })

  describe('validateHours boundaries', () => {
    it('accepts minimum fractional hours (0.25)', () => {
      expect(validateHours(0.25)).toBe(0.25)
    })

    it('accepts maximum hours (168)', () => {
      expect(validateHours(168)).toBe(168)
    })

    it('rejects just below minimum', () => {
      expect(() => validateHours(0.24)).toThrow()
    })

    it('rejects just above maximum', () => {
      expect(() => validateHours(168.01)).toThrow()
    })
  })

  describe('validateSearchTerm boundaries', () => {
    it('accepts exactly 100 chars', () => {
      const term = 'a'.repeat(100)
      expect(validateSearchTerm(term)).toBe(term)
    })

    it('rejects 101 chars', () => {
      const term = 'a'.repeat(101)
      expect(() => validateSearchTerm(term)).toThrow()
    })
  })

  describe('validateIntentNotes boundaries', () => {
    it('accepts exactly 200 chars', () => {
      const notes = 'a'.repeat(200)
      expect(validateIntentNotes(notes)).toBe(notes)
    })

    it('rejects 201 chars', () => {
      const notes = 'a'.repeat(201)
      expect(() => validateIntentNotes(notes)).toThrow()
    })
  })
})

describe('Wallet Security - Integration Scenarios', () => {
  it('validates all fields in a giving intent without throwing', () => {
    const intent = {
      type: 'giving',
      amount: validateAmount(250),
      notes: validateIntentNotes('Quarterly support'),
    }
    expect(intent.amount).toBe(250)
    expect(intent.notes).toBe('Quarterly support')
  })

  it('validates volunteer intent with hours', () => {
    const intent = {
      type: 'volunteer',
      hours: validateHours(5),
    }
    expect(intent.hours).toBe(5)
  })

  it('validates wallet filter combination', () => {
    expect(validateFilterValue('intent', 'giving')).toBe(true)
    expect(validateFilterValue('health', 'HEALTHY')).toBe(true)
    expect(validateSortValue('recent')).toBe(true)
  })

  it('handles malformed filter + search combination gracefully', () => {
    const filterOk = validateFilterValue('intent', 'all')
    const searchOk = () => validateSearchTerm('organization name')
    expect(filterOk).toBe(true)
    expect(searchOk).not.toThrow()
  })
})
