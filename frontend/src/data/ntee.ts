export interface NteeSub {
  code: string
  name: string
}

export interface NteeMajor {
  id: string
  name: string
  emoji: string
  gradient: [string, string]
  count?: number
  subs: NteeSub[]
}

export const NTEE_CATEGORIES: NteeMajor[] = [
  {
    id: 'E', name: 'Health', emoji: '❤️',
    gradient: ['#FF416C', '#FF4B2B'],
    subs: [
      { code: 'E20', name: 'Health Care (General)' },
      { code: 'E21', name: 'Community Health Centers' },
      { code: 'E22', name: 'General Hospitals' },
      { code: 'E32', name: 'Family Planning' },
      { code: 'E40', name: 'Reproductive Health' },
      { code: 'E50', name: 'Rehabilitative Care' },
      { code: 'E60', name: 'Health Support' },
      { code: 'E70', name: 'Public Health Programs' },
      { code: 'E80', name: 'Health (NEC)' },
    ],
  },
  {
    id: 'B', name: 'Education', emoji: '📚',
    gradient: ['#4776E6', '#8E54E9'],
    subs: [
      { code: 'B20', name: 'Elementary & Secondary Schools' },
      { code: 'B24', name: 'Primary Schools' },
      { code: 'B25', name: 'High Schools' },
      { code: 'B30', name: 'Higher Education' },
      { code: 'B40', name: 'Libraries' },
      { code: 'B50', name: 'Graduate & Professional Schools' },
      { code: 'B60', name: 'Adult Education' },
      { code: 'B82', name: 'Scholarships & Financial Aid' },
      { code: 'B83', name: 'Alumni Associations' },
      { code: 'B94', name: 'Parent-Teacher Groups' },
    ],
  },
  {
    id: 'P', name: 'Human Services', emoji: '🤝',
    gradient: ['#00C6FF', '#0072FF'],
    subs: [
      { code: 'P20', name: 'Food Banks & Pantries' },
      { code: 'P30', name: 'Youth Services' },
      { code: 'P33', name: 'Child Day Care' },
      { code: 'P40', name: 'Family Services' },
      { code: 'P50', name: 'Personal Social Services' },
      { code: 'P60', name: 'Emergency Assistance' },
      { code: 'P70', name: 'Residential & Custodial Care' },
      { code: 'P80', name: 'Services for Specific Populations' },
      { code: 'P81', name: 'Services for Homeless People' },
      { code: 'P82', name: 'Senior Centers' },
    ],
  },
  {
    id: 'C', name: 'Environment', emoji: '🌿',
    gradient: ['#134E5E', '#71B280'],
    subs: [
      { code: 'C20', name: 'Pollution Abatement' },
      { code: 'C27', name: 'Recycling' },
      { code: 'C30', name: 'Natural Resources Conservation' },
      { code: 'C32', name: 'Water Resources' },
      { code: 'C34', name: 'Land Resources' },
      { code: 'C36', name: 'Forest Conservation' },
      { code: 'C40', name: 'Botanical & Horticultural' },
      { code: 'C60', name: 'Wildlife Preservation' },
      { code: 'C61', name: 'Wildlife Sanctuaries' },
    ],
  },
  {
    id: 'A', name: 'Arts & Culture', emoji: '🎨',
    gradient: ['#F953C6', '#B91D73'],
    subs: [
      { code: 'A20', name: 'Arts & Culture (General)' },
      { code: 'A23', name: 'Cultural & Ethnic Awareness' },
      { code: 'A25', name: 'Arts Centers' },
      { code: 'A35', name: 'Music' },
      { code: 'A50', name: 'Museums' },
      { code: 'A60', name: 'Performing Arts' },
      { code: 'A61', name: 'Theater' },
      { code: 'A65', name: 'Singing & Choral Groups' },
      { code: 'A68', name: 'Music Schools' },
      { code: 'A80', name: 'Historical Societies' },
    ],
  },
  {
    id: 'D', name: 'Animals', emoji: '🐾',
    gradient: ['#F6D365', '#FDA085'],
    subs: [
      { code: 'D20', name: 'Animal Protection & Welfare' },
      { code: 'D30', name: 'Wildlife Preservation' },
      { code: 'D40', name: 'Veterinary Services' },
      { code: 'D50', name: 'Zoos & Aquariums' },
      { code: 'D60', name: 'Fishing & Hunting Clubs' },
    ],
  },
  {
    id: 'K', name: 'Food & Nutrition', emoji: '🌾',
    gradient: ['#56CCF2', '#2F80ED'],
    subs: [
      { code: 'K20', name: 'Agricultural Programs' },
      { code: 'K25', name: 'Farmland Preservation' },
      { code: 'K30', name: 'Food Programs' },
      { code: 'K31', name: 'Food Banks & Pantries' },
      { code: 'K34', name: 'Congregate Meals' },
      { code: 'K35', name: 'Meals on Wheels' },
      { code: 'K36', name: 'Summer Meals' },
      { code: 'K40', name: 'Nutrition' },
    ],
  },
  {
    id: 'S', name: 'Community', emoji: '🏘️',
    gradient: ['#11998E', '#38EF7D'],
    subs: [
      { code: 'S20', name: 'Community & Neighbourhood Development' },
      { code: 'S21', name: 'Community Coalitions' },
      { code: 'S22', name: 'Neighborhood Associations' },
      { code: 'S30', name: 'Economic Development' },
      { code: 'S40', name: 'Business & Industry' },
      { code: 'S50', name: 'Community Service Clubs' },
    ],
  },
  {
    id: 'Q', name: 'International', emoji: '🌍',
    gradient: ['#667EEA', '#764BA2'],
    subs: [
      { code: 'Q20', name: 'International Understanding' },
      { code: 'Q21', name: 'Cultural Exchange' },
      { code: 'Q22', name: 'Student Exchange' },
      { code: 'Q30', name: 'International Development' },
      { code: 'Q33', name: 'International Relief' },
      { code: 'Q40', name: 'International Peace & Security' },
      { code: 'Q70', name: 'International Human Rights' },
    ],
  },
  {
    id: 'X', name: 'Faith', emoji: '✨',
    gradient: ['#F7971E', '#FFD200'],
    subs: [
      { code: 'X20', name: 'Christian' },
      { code: 'X22', name: 'Protestant' },
      { code: 'X30', name: 'Jewish' },
      { code: 'X40', name: 'Islamic' },
      { code: 'X41', name: 'Buddhist' },
      { code: 'X50', name: 'Hindu' },
      { code: 'X70', name: 'Protestant (Community)' },
      { code: 'X80', name: 'Religious Media & Communications' },
    ],
  },
  {
    id: 'O', name: 'Youth Development', emoji: '🌟',
    gradient: ['#FA709A', '#FEE140'],
    subs: [
      { code: 'O20', name: 'Youth Centers & Clubs' },
      { code: 'O21', name: 'Boys Clubs' },
      { code: 'O22', name: 'Girls Clubs' },
      { code: 'O23', name: 'Boys & Girls Clubs' },
      { code: 'O30', name: 'Scouting Organizations' },
      { code: 'O40', name: 'Big Brothers / Big Sisters' },
      { code: 'O50', name: 'Youth Development Programs' },
    ],
  },
  {
    id: 'F', name: 'Mental Health', emoji: '🧠',
    gradient: ['#BC4E9C', '#F80759'],
    subs: [
      { code: 'F20', name: 'Substance Abuse Prevention' },
      { code: 'F22', name: 'Substance Abuse Treatment' },
      { code: 'F30', name: 'Mental Health Treatment' },
      { code: 'F31', name: 'Psychiatric Hospitals' },
      { code: 'F32', name: 'Community Mental Health Centers' },
      { code: 'F40', name: 'Crisis Intervention' },
      { code: 'F42', name: 'Rape Crisis Services' },
      { code: 'F50', name: 'Addictive Disorders' },
      { code: 'F60', name: 'Counseling' },
    ],
  },
  {
    id: 'G', name: 'Disease Research', emoji: '🔬',
    gradient: ['#2193B0', '#6DD5ED'],
    subs: [
      { code: 'G20', name: 'Cancer' },
      { code: 'G30', name: 'Heart & Circulatory Disease' },
      { code: 'G40', name: 'Respiratory Disease' },
      { code: 'G50', name: 'Kidney Disease' },
      { code: 'G60', name: 'Diabetes' },
      { code: 'G70', name: 'Eye Diseases' },
      { code: 'G80', name: 'Specific Named Diseases' },
      { code: 'G84', name: 'AIDS / HIV' },
    ],
  },
  {
    id: 'H', name: 'Medical Research', emoji: '🧬',
    gradient: ['#4facfe', '#00f2fe'],
    subs: [
      { code: 'H20', name: 'Cancer Research' },
      { code: 'H30', name: 'Heart & Circulatory Research' },
      { code: 'H60', name: 'Diabetes Research' },
      { code: 'H80', name: 'Medical Research (General)' },
      { code: 'H90', name: 'Biomedical Research' },
    ],
  },
  {
    id: 'I', name: 'Crime & Legal', emoji: '🔒',
    gradient: ['#373B44', '#4286f4'],
    subs: [
      { code: 'I20', name: 'Crime Prevention' },
      { code: 'I23', name: 'Drunk Driving Prevention' },
      { code: 'I30', name: 'Correctional Facilities' },
      { code: 'I40', name: 'Rehabilitation Services' },
      { code: 'I43', name: 'Prisoner Support & Advocacy' },
      { code: 'I51', name: 'Legal Aid & Services' },
      { code: 'I70', name: 'Protection Against Abuse' },
      { code: 'I80', name: 'Victim Support' },
    ],
  },
  {
    id: 'J', name: 'Employment', emoji: '💼',
    gradient: ['#1B6B43', '#52c234'],
    subs: [
      { code: 'J20', name: 'Employment Training' },
      { code: 'J22', name: 'Vocational Training' },
      { code: 'J30', name: 'Job Placement' },
      { code: 'J40', name: 'Labor Organizations' },
      { code: 'J60', name: "Workers' Rights" },
    ],
  },
  {
    id: 'L', name: 'Housing & Shelter', emoji: '🏠',
    gradient: ['#F09819', '#EDDE5D'],
    subs: [
      { code: 'L20', name: 'Housing Development' },
      { code: 'L21', name: 'Low-Income Housing' },
      { code: 'L25', name: 'Housing Rehabilitation' },
      { code: 'L30', name: 'Housing Search Assistance' },
      { code: 'L41', name: 'Homeless Shelters' },
      { code: 'L80', name: 'Housing Support Services' },
    ],
  },
  {
    id: 'M', name: 'Public Safety', emoji: '🚒',
    gradient: ['#CB2D3E', '#EF473A'],
    subs: [
      { code: 'M20', name: 'Disaster Preparedness' },
      { code: 'M23', name: 'Search & Rescue' },
      { code: 'M24', name: 'Emergency Assistance (Disaster)' },
      { code: 'M40', name: 'Safety Education' },
      { code: 'M41', name: 'First Aid' },
      { code: 'M60', name: 'Disaster Relief' },
    ],
  },
  {
    id: 'N', name: 'Sports & Recreation', emoji: '⚽',
    gradient: ['#0ba360', '#3cba92'],
    subs: [
      { code: 'N30', name: 'Physical Fitness & Recreation' },
      { code: 'N40', name: 'Sports Training' },
      { code: 'N50', name: 'Recreational Clubs' },
      { code: 'N60', name: 'Amateur Sports' },
      { code: 'N61', name: 'Olympic Sports' },
      { code: 'N65', name: 'Athletic Competitions' },
      { code: 'N70', name: 'Fishing & Hunting' },
    ],
  },
  {
    id: 'R', name: 'Civil Rights', emoji: '⚖️',
    gradient: ['#2B5876', '#4E4376'],
    subs: [
      { code: 'R20', name: 'Civil Rights' },
      { code: 'R22', name: 'Racial Equity & Justice' },
      { code: 'R23', name: 'Disability Rights' },
      { code: 'R24', name: 'LGBTQ Rights' },
      { code: 'R25', name: 'Voter Rights & Education' },
      { code: 'R30', name: 'Advocacy & Organizing' },
    ],
  },
  {
    id: 'T', name: 'Philanthropy', emoji: '🤲',
    gradient: ['#b993d6', '#8ca6db'],
    subs: [
      { code: 'T20', name: 'Private Foundations' },
      { code: 'T21', name: 'Corporate Foundations' },
      { code: 'T22', name: 'Operating Foundations' },
      { code: 'T30', name: 'Public Foundations' },
      { code: 'T31', name: 'Community Foundations' },
      { code: 'T40', name: 'Voluntarism Promotion' },
      { code: 'T70', name: 'Federated Giving Programs' },
    ],
  },
  {
    id: 'U', name: 'Science & Technology', emoji: '🔭',
    gradient: ['#005BEA', '#00C6FB'],
    subs: [
      { code: 'U20', name: 'Science & Technology Research' },
      { code: 'U30', name: 'Physical & Earth Sciences' },
      { code: 'U33', name: 'Astronomy' },
      { code: 'U40', name: 'Engineering & Technology' },
      { code: 'U50', name: 'Computer Science' },
    ],
  },
  {
    id: 'V', name: 'Social Science', emoji: '📊',
    gradient: ['#654EA3', '#EAAFC8'],
    subs: [
      { code: 'V20', name: 'Social Science Research' },
      { code: 'V25', name: 'Urban Studies' },
      { code: 'V30', name: 'Economics & Policy Research' },
      { code: 'V55', name: 'Media & Communications Research' },
    ],
  },
  {
    id: 'W', name: 'Public Benefit', emoji: '🏛️',
    gradient: ['#243949', '#517fa4'],
    subs: [
      { code: 'W05', name: 'Government & Public Administration' },
      { code: 'W20', name: 'Military & Veterans Organizations' },
      { code: 'W22', name: "Veterans' Rights" },
      { code: 'W30', name: 'Military / Law Enforcement Support' },
      { code: 'W40', name: 'Public Transportation' },
      { code: 'W50', name: 'Telecommunications' },
    ],
  },
]

// Lookup by id
export function getNteeCategory(id: string): NteeMajor | undefined {
  return NTEE_CATEGORIES.find(c => c.id === id)
}

// Friendly cause-area label for an NTEE code. Accepts a full subcategory code
// ("S21") or a broad major id ("S"). Prefers the specific subcategory name,
// falls back to the major category name, then to the raw code.
export function getNteeLabel(code: string | null | undefined): string {
  if (!code) return 'this cause area'
  const major = NTEE_CATEGORIES.find(c => c.id === code[0])
  if (!major) return 'this cause area'
  const sub = major.subs.find(s => s.code === code)
  return sub ? sub.name : major.name
}
