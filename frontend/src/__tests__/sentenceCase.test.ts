import { sentenceCase } from '../utils/sentenceCase'

describe('sentenceCase', () => {
  it('leaves mixed-case text untouched', () => {
    // Anything an org wrote itself through the claim flow must never be reformatted.
    const claimed = 'We run a food pantry in Dane County. Everyone eats.'
    expect(sentenceCase(claimed)).toBe(claimed)
  })

  it('sentence-cases an all-caps filing', () => {
    expect(
      sentenceCase('TO IMPLEMENT AND ADMINISTER VARIOUS COMMUNITY ACTION PROGRAMS.')
    ).toBe('To implement and administer various community action programs.')
  })

  it('capitalises each new sentence', () => {
    expect(sentenceCase('WE FEED PEOPLE. WE ALSO TEACH COOKING.')).toBe(
      'We feed people. We also teach cooking.'
    )
  })

  it('keeps acronyms upper case', () => {
    expect(sentenceCase('PROVIDING HIV AND AIDS SERVICES IN THE USA')).toBe(
      'Providing HIV and AIDS services in the USA'
    )
  })

  it('keeps acronyms upper case inside punctuation', () => {
    expect(sentenceCase('SUPPORTING THE LOCAL (YMCA), AND OTHERS')).toBe(
      'Supporting the local (YMCA), and others'
    )
  })

  it('leaves tokens containing digits alone', () => {
    expect(sentenceCase('A 501C3 SERVING K-12 STUDENTS')).toBe(
      'A 501C3 serving K-12 students'
    )
  })

  it('preserves single letters as initials', () => {
    // Proper nouns cannot be recovered from all-caps text without a named-entity
    // model, so "SMITH" and "OHIO" lower. That is the accepted trade: readable
    // prose beats shouting, and we never invent casing we cannot derive.
    expect(sentenceCase('FOUNDED BY J SMITH IN OHIO')).toBe(
      'Founded by J smith in ohio'
    )
  })

  it('handles empty and nullish input', () => {
    expect(sentenceCase('')).toBe('')
    expect(sentenceCase(null)).toBe('')
    expect(sentenceCase(undefined)).toBe('')
  })

  it('does not alter text with no letters', () => {
    expect(sentenceCase('1234 5678')).toBe('1234 5678')
  })

  it('capitalises after a question or exclamation mark', () => {
    expect(sentenceCase('WHO DO WE SERVE? EVERYONE WHO ASKS.')).toBe(
      'Who do we serve? Everyone who asks.'
    )
  })
})
