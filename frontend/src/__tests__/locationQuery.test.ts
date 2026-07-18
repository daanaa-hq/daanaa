import { parseLocationQuery } from '../utils/locationQuery'

describe('parseLocationQuery', () => {
  it('recognizes a 5-digit zip', () => {
    expect(parseLocationQuery('78701')).toBe('78701')
  })

  it('recognizes a zip+4', () => {
    expect(parseLocationQuery('78701-2912')).toBe('78701-2912')
  })

  it('recognizes "City, ST"', () => {
    expect(parseLocationQuery('Austin, TX')).toBe('Austin, TX')
  })

  it('recognizes "City,ST" with no space', () => {
    expect(parseLocationQuery('Austin,TX')).toBe('Austin,TX')
  })

  it('recognizes multi-word city names', () => {
    expect(parseLocationQuery('San Marcos, TX')).toBe('San Marcos, TX')
    expect(parseLocationQuery("O'Fallon, MO")).toBe("O'Fallon, MO")
  })

  it('trims surrounding whitespace', () => {
    expect(parseLocationQuery('  78701  ')).toBe('78701')
  })

  it('does NOT treat an org name as a location', () => {
    expect(parseLocationQuery('American Red Cross')).toBeNull()
  })

  it('does NOT treat a cause keyword as a location', () => {
    expect(parseLocationQuery('food bank')).toBeNull()
    expect(parseLocationQuery('education')).toBeNull()
  })

  it('does NOT treat an EIN as a location', () => {
    expect(parseLocationQuery('264837170')).toBeNull()
    expect(parseLocationQuery('46-3120432')).toBeNull()
  })

  it('does NOT treat a bare city (no state) as a location', () => {
    expect(parseLocationQuery('Austin')).toBeNull()
  })

  it('does NOT treat a 4 or 6-digit number as a zip', () => {
    expect(parseLocationQuery('7870')).toBeNull()
    expect(parseLocationQuery('787011')).toBeNull()
  })

  it('rejects empty and whitespace-only input', () => {
    expect(parseLocationQuery('')).toBeNull()
    expect(parseLocationQuery('   ')).toBeNull()
  })
})
