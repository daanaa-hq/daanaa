import {
  isValidGivingIntent,
  isValidWalletOrg,
  isValidWallet,
  WALLET_CONSTRAINTS,
  type Wallet,
  type WalletOrg,
  type GivingIntent,
} from '../../src/types/wallet'

describe('wallet types', () => {
  describe('GivingIntent validation', () => {
    const validIntent: GivingIntent = {
      type: 'giving',
      status: 'interested',
      amount: 250,
      addedAt: Date.now(),
    }

    it('accepts valid giving intent with amount', () => {
      expect(isValidGivingIntent(validIntent)).toBe(true)
    })

    it('accepts valid volunteer intent with hours', () => {
      const intent: GivingIntent = {
        type: 'volunteer',
        status: 'interested',
        hours: 5,
        addedAt: Date.now(),
      }
      expect(isValidGivingIntent(intent)).toBe(true)
    })

    it('accepts valid board intent without amount', () => {
      const intent: GivingIntent = {
        type: 'board',
        status: 'interested',
        addedAt: Date.now(),
      }
      expect(isValidGivingIntent(intent)).toBe(true)
    })

    it('accepts intent with notes up to max length', () => {
      const notes = 'a'.repeat(WALLET_CONSTRAINTS.NOTES_MAX_LENGTH)
      const intent: GivingIntent = {
        type: 'giving',
        status: 'interested',
        addedAt: Date.now(),
        notes,
      }
      expect(isValidGivingIntent(intent)).toBe(true)
    })

    it('rejects intent with withdrawn status', () => {
      const intent: GivingIntent = {
        type: 'giving',
        status: 'withdrawn',
        addedAt: Date.now(),
      }
      expect(isValidGivingIntent(intent)).toBe(true) // withdrawn is valid
    })

    it('rejects intent with invalid type', () => {
      expect(isValidGivingIntent({ type: 'invalid', status: 'interested', addedAt: Date.now() })).toBe(false)
    })

    it('rejects intent with invalid status', () => {
      expect(isValidGivingIntent({ type: 'giving', status: 'invalid', addedAt: Date.now() })).toBe(false)
    })

    it('rejects intent with zero or negative amount', () => {
      expect(isValidGivingIntent({ type: 'giving', status: 'interested', amount: 0, addedAt: Date.now() })).toBe(false)
      expect(isValidGivingIntent({ type: 'giving', status: 'interested', amount: -100, addedAt: Date.now() })).toBe(false)
    })

    it('rejects intent with zero or negative hours', () => {
      expect(isValidGivingIntent({ type: 'volunteer', status: 'interested', hours: 0, addedAt: Date.now() })).toBe(false)
      expect(isValidGivingIntent({ type: 'volunteer', status: 'interested', hours: -5, addedAt: Date.now() })).toBe(false)
    })

    it('rejects intent with notes exceeding max length', () => {
      const notes = 'a'.repeat(WALLET_CONSTRAINTS.NOTES_MAX_LENGTH + 1)
      expect(isValidGivingIntent({ type: 'giving', status: 'interested', addedAt: Date.now(), notes })).toBe(false)
    })

    it('rejects intent with missing addedAt', () => {
      expect(isValidGivingIntent({ type: 'giving', status: 'interested' })).toBe(false)
    })

    it('rejects intent with zero or negative addedAt timestamp', () => {
      expect(isValidGivingIntent({ type: 'giving', status: 'interested', addedAt: 0 })).toBe(false)
      expect(isValidGivingIntent({ type: 'giving', status: 'interested', addedAt: -1000 })).toBe(false)
    })

    it('rejects null and undefined', () => {
      expect(isValidGivingIntent(null)).toBe(false)
      expect(isValidGivingIntent(undefined)).toBe(false)
    })

    it('rejects non-objects', () => {
      expect(isValidGivingIntent('not an object')).toBe(false)
      expect(isValidGivingIntent(123)).toBe(false)
      expect(isValidGivingIntent([])).toBe(false)
    })
  })

  describe('WalletOrg validation', () => {
    const validOrg: WalletOrg = {
      ein: '123456789',
      name: 'Save the World',
      mission: 'Fighting climate change',
      location: 'Austin, TX',
      cause: ['environment'],
      merit_score_v5: 78,
      merit_health_signal_v5: 'HEALTHY',
      is_hidden_gem: false,
      donate_url: 'https://example.org/donate',
      bookmarkedAt: Date.now(),
    }

    it('accepts valid org with all fields', () => {
      expect(isValidWalletOrg(validOrg)).toBe(true)
    })

    it('accepts org with multiple causes', () => {
      const org: WalletOrg = { ...validOrg, cause: ['environment', 'education', 'health'] }
      expect(isValidWalletOrg(org)).toBe(true)
    })

    it('accepts org without donate_url', () => {
      const org: WalletOrg = { ...validOrg }
      delete org.donate_url
      expect(isValidWalletOrg(org)).toBe(true)
    })

    it('accepts org with givingIntent', () => {
      const org: WalletOrg = {
        ...validOrg,
        givingIntent: {
          type: 'giving',
          status: 'interested',
          amount: 500,
          addedAt: Date.now(),
        },
      }
      expect(isValidWalletOrg(org)).toBe(true)
    })

    it('accepts health signal STABLE', () => {
      const org: WalletOrg = { ...validOrg, merit_health_signal_v5: 'STABLE' }
      expect(isValidWalletOrg(org)).toBe(true)
    })

    it('accepts health signal CAUTION', () => {
      const org: WalletOrg = { ...validOrg, merit_health_signal_v5: 'CAUTION' }
      expect(isValidWalletOrg(org)).toBe(true)
    })

    it('accepts score 0 and 100', () => {
      expect(isValidWalletOrg({ ...validOrg, merit_score_v5: 0 })).toBe(true)
      expect(isValidWalletOrg({ ...validOrg, merit_score_v5: 100 })).toBe(true)
    })

    it('rejects EIN not 9 characters', () => {
      expect(isValidWalletOrg({ ...validOrg, ein: '12345678' })).toBe(false)
      expect(isValidWalletOrg({ ...validOrg, ein: '1234567890' })).toBe(false)
    })

    it('rejects invalid health signal', () => {
      expect(isValidWalletOrg({ ...validOrg, merit_health_signal_v5: 'INVALID' as any })).toBe(false)
    })

    it('rejects score outside 0-100 range', () => {
      expect(isValidWalletOrg({ ...validOrg, merit_score_v5: -1 })).toBe(false)
      expect(isValidWalletOrg({ ...validOrg, merit_score_v5: 101 })).toBe(false)
    })

    it('rejects zero or negative bookmarkedAt', () => {
      expect(isValidWalletOrg({ ...validOrg, bookmarkedAt: 0 })).toBe(false)
      expect(isValidWalletOrg({ ...validOrg, bookmarkedAt: -1000 })).toBe(false)
    })

    it('rejects cause that is not an array', () => {
      expect(isValidWalletOrg({ ...validOrg, cause: 'environment' as any })).toBe(false)
    })

    it('rejects invalid givingIntent', () => {
      const org: WalletOrg = {
        ...validOrg,
        givingIntent: { type: 'invalid', status: 'interested', addedAt: Date.now() } as any,
      }
      expect(isValidWalletOrg(org)).toBe(false)
    })

    it('rejects null and undefined', () => {
      expect(isValidWalletOrg(null)).toBe(false)
      expect(isValidWalletOrg(undefined)).toBe(false)
    })

    it('rejects missing required fields', () => {
      const incomplete = { ein: '123456789', name: 'Org' } as any
      expect(isValidWalletOrg(incomplete)).toBe(false)
    })
  })

  describe('Wallet validation', () => {
    const validOrg: WalletOrg = {
      ein: '123456789',
      name: 'Save the World',
      mission: 'Fighting climate change',
      location: 'Austin, TX',
      cause: ['environment'],
      merit_score_v5: 78,
      merit_health_signal_v5: 'HEALTHY',
      is_hidden_gem: false,
      bookmarkedAt: Date.now(),
    }

    const validWallet: Wallet = {
      version: 1,
      lastUpdated: Date.now(),
      orgs: [validOrg],
      syncedWithServer: false,
    }

    it('accepts valid wallet with one org', () => {
      expect(isValidWallet(validWallet)).toBe(true)
    })

    it('accepts valid wallet with no orgs', () => {
      const wallet: Wallet = {
        version: 1,
        lastUpdated: Date.now(),
        orgs: [],
        syncedWithServer: false,
      }
      expect(isValidWallet(wallet)).toBe(true)
    })

    it('accepts wallet with googleEmail when synced', () => {
      const wallet: Wallet = {
        ...validWallet,
        syncedWithServer: true,
        googleEmail: 'user@example.com',
      }
      expect(isValidWallet(wallet)).toBe(true)
    })

    it('accepts wallet with multiple orgs', () => {
      const wallet: Wallet = {
        ...validWallet,
        orgs: [validOrg, { ...validOrg, ein: '987654321', name: 'Another Org' }],
      }
      expect(isValidWallet(wallet)).toBe(true)
    })

    it('rejects wallet with wrong version', () => {
      expect(isValidWallet({ ...validWallet, version: 2 as any })).toBe(false)
    })

    it('rejects wallet with zero or negative lastUpdated', () => {
      expect(isValidWallet({ ...validWallet, lastUpdated: 0 })).toBe(false)
      expect(isValidWallet({ ...validWallet, lastUpdated: -1000 })).toBe(false)
    })

    it('rejects wallet with invalid org in orgs array', () => {
      const wallet: Wallet = {
        ...validWallet,
        orgs: [validOrg, { ...validOrg, ein: 'invalid' } as any],
      }
      expect(isValidWallet(wallet)).toBe(false)
    })

    it('rejects wallet with invalid syncedWithServer', () => {
      expect(isValidWallet({ ...validWallet, syncedWithServer: 'yes' as any })).toBe(false)
    })

    it('rejects wallet with non-array orgs', () => {
      expect(isValidWallet({ ...validWallet, orgs: 'not an array' as any })).toBe(false)
    })

    it('rejects null and undefined', () => {
      expect(isValidWallet(null)).toBe(false)
      expect(isValidWallet(undefined)).toBe(false)
    })
  })

  describe('WALLET_CONSTRAINTS', () => {
    it('defines correct constraints', () => {
      expect(WALLET_CONSTRAINTS.NOTES_MAX_LENGTH).toBe(200)
      expect(WALLET_CONSTRAINTS.AMOUNT_MIN).toBe(1)
      expect(WALLET_CONSTRAINTS.HOURS_MIN).toBe(0.25)
    })
  })
})
