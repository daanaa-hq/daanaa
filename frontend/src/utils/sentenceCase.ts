/**
 * Sentence-case text that arrived from an IRS filing in ALL CAPS.
 *
 * 286,644 of the 387,896 mission statements harvested from Form 990 Part I are
 * upper case, because that is how the filings are typed. All caps removes the
 * word shapes fluent readers rely on, measurably slows reading, hits dyslexic
 * readers hardest, and reads as shouting — so the organization's own words end
 * up harder to read than the AI text they replaced.
 *
 * The filing is stored verbatim; this only changes presentation. Mixed-case
 * text is returned untouched, so anything an organization wrote itself through
 * the claim flow is never reformatted.
 */

/**
 * Tokens that stay upper case. Restricted to abbreviations that are genuinely
 * ambiguous or unreadable when lowered — not a general vocabulary. An acronym
 * missing here degrades to "Usa", which is untidy but still readable; a wrong
 * entry here shouts at the reader, so the list stays short on purpose.
 */
const KEEP_UPPER = new Set([
  'USA', 'U.S.', 'U.S.A.', 'UK', 'DC', 'NYC',
  'YMCA', 'YWCA', 'PTA', 'PTO', 'VFW', 'AA', 'ROTC', 'FFA', 'FCA',
  'HIV', 'AIDS', 'STEM', 'STEAM', 'GED', 'CPR', 'EMS', 'EMT', 'ICU',
  'LGBTQ', 'LGBTQ+', 'LGBT', 'BIPOC',
  'IRS', 'FEMA', 'HUD', 'USDA', 'NASA', 'CDC', 'NATO',
  'GPA', 'ESL', 'IEP',
  'ADA', 'PPE', 'PTSD', 'ASD', 'ADHD',
  'CEO', 'CFO', 'COO', 'CIO', 'DBA', 'LLC',
])
// Deliberately excluded: WHO, US, ACT, SAT, NA, CAN, IT, IN, INC. Each is a
// common English word far more often than the acronym in mission prose, and a
// false keep shouts mid-sentence ("serving WHO in need"), which is the exact
// defect this module exists to remove.

/** Roman numerals up to a plausible chapter/section number (I, II, III, IV…). */
const ROMAN = /^(?:I{1,3}|IV|VI{0,3}|IX|XI{0,3}|XIV|XV|XVI{0,3}|XIX|XX)$/

function casedWord(word: string): string {
  if (!word) return word

  // Split leading/trailing punctuation so "(YMCA)," still matches the set.
  const m = word.match(/^([^\p{L}\p{N}]*)(.*?)([^\p{L}\p{N}]*)$/u)
  if (!m) return word.toLowerCase()
  const [, lead, core, trail] = m
  if (!core) return word

  if (KEEP_UPPER.has(core) || ROMAN.test(core)) return lead + core + trail

  // A token carrying digits is usually an identifier or a code (501C3, 24/7).
  if (/\d/.test(core)) return lead + core + trail

  // Single letters are initials far more often than words: "J. SMITH".
  if (core.length === 1) return lead + core + trail

  // Lower the whole word. Sentence starts are re-capitalised afterwards, once
  // punctuation shows where the sentences actually begin.
  return lead + core.toLowerCase() + trail
}

/**
 * Returns text with sentence casing applied. Non-upper-case input is returned
 * unchanged, so this is safe to call on every mission regardless of source.
 */
export function sentenceCase(text: string | null | undefined): string {
  if (!text) return ''
  const trimmed = text.trim()
  if (!trimmed) return ''

  // Only reformat text that is actually shouting. Requires at least one letter,
  // so digit-only strings are left alone.
  if (!/\p{Lu}/u.test(trimmed) || trimmed !== trimmed.toUpperCase()) return trimmed

  const lowered = trimmed.split(/(\s+)/).map((tok) =>
    /^\s+$/.test(tok) ? tok : casedWord(tok)
  ).join('')

  // Capitalise the first letter of the string and of each new sentence.
  return lowered.replace(
    /(^\s*|[.!?]["')\]]?\s+)(\p{Ll})/gu,
    (_all, prefix: string, ch: string) => prefix + ch.toUpperCase()
  )
}
