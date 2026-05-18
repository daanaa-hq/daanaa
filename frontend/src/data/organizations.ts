export type OrgTier = 'full' | 'strong' | 'financial' | 'listed'

export function getOrgTier(org: {
  hasMission?: boolean | null;
  hasWebsite?: boolean | null;
  mission?: string | null;
  website?: string | null;
  revenue: number;
  meritScore: number;
  hasScore?: boolean;
}): OrgTier {
  const hasMission = org.hasMission ?? !!(org.mission && org.mission.length > 0)
  const hasWebsite = org.hasWebsite ?? !!(org.website && org.website.length > 0)
  const hasRevenue = org.revenue > 0
  const hasScore = org.hasScore !== false && org.meritScore > 0
  if (hasMission && hasWebsite && hasRevenue && hasScore) return 'full'
  if (hasMission && hasRevenue && hasScore) return 'strong'
  if (hasRevenue || hasScore) return 'financial'
  return 'listed'
}

export interface Organization {
  id: string;
  name: string;
  ein: string;
  city: string;
  state: string;
  category: string;
  subcategory: string;
  meritScore: number;
  hasScore?: boolean;        // false = show "IRS Verified · Active" instead of score
  hasMission?: boolean | null;
  hasWebsite?: boolean | null;
  revenueBand?: string | null;
  dataSource?: string | null;
  latestTaxYear?: number | null;
  ntee1TotalOrgs?: number | null;
  website?: string | null;
  revenue: number;
  assets: number;
  employees: number;
  founded: number;
  mission: string;
  programs: string[];
  leadership: { name: string; title: string; initials: string }[];
  boardSize: number;
  revenueTrend: { year: number; amount: number }[];
  programEfficiency: number;
  fundraisingRatio: number;
  operatingReserve: number;
  transparencyScore: number;
}

export const NTEE1_NAMES: Record<string, string> = {
  A: 'Arts & Culture', B: 'Education', C: 'Environment', D: 'Health',
  E: 'Hospitals', F: 'Mental Health', G: 'Disease Research', H: 'Medical Research',
  I: 'Crime & Legal', J: 'Employment', K: 'Food & Agriculture', L: 'Housing',
  M: 'Public Safety', N: 'Recreation', O: 'Youth Development', P: 'Human Services',
  Q: 'International', R: 'Civil Rights', S: 'Community Development', T: 'Philanthropy',
  U: 'Science', V: 'Social Science', W: 'Public Affairs', X: 'Religion',
  Y: 'Mutual Benefit', Z: 'Unknown',
}

export const categories = [
  { id: 'education', name: 'Education', icon: 'graduation-cap', count: 2847 },
  { id: 'health', name: 'Health & Research', icon: 'heart-pulse', count: 3124 },
  { id: 'human-services', name: 'Human Services', icon: 'hands-helping', count: 4521 },
  { id: 'arts', name: 'Arts & Culture', icon: 'palette', count: 1982 },
  { id: 'environment', name: 'Environment', icon: 'leaf', count: 1456 },
  { id: 'community', name: 'Community Development', icon: 'users', count: 2341 },
  { id: 'animals', name: 'Animal-Related', icon: 'paw', count: 876 },
  { id: 'international', name: 'International Affairs', icon: 'globe', count: 654 },
  { id: 'religion', name: 'Religion-Related', icon: 'church', count: 3421 },
  { id: 'civil-rights', name: 'Civil Rights & Advocacy', icon: 'scale', count: 543 },
];

export const organizations: Organization[] = [
  {
    id: '1',
    name: 'United Way Worldwide',
    ein: '13-1635294',
    city: 'Alexandria',
    state: 'VA',
    category: 'human-services',
    subcategory: 'Human Services',
    meritScore: 94,
    revenue: 4800000000,
    assets: 4200000000,
    employees: 3200,
    founded: 1887,
    mission: 'To improve lives by mobilizing the caring power of communities around the world to advance the common good.',
    programs: ['Education', 'Financial Stability', 'Health', 'Disaster Response'],
    leadership: [{ name: 'Angela F. Williams', title: 'President & CEO', initials: 'AW' }],
    boardSize: 18,
    revenueTrend: [
      { year: 2020, amount: 4100000000 },
      { year: 2021, amount: 4500000000 },
      { year: 2022, amount: 4700000000 },
      { year: 2023, amount: 4800000000 },
      { year: 2024, amount: 4900000000 },
    ],
    programEfficiency: 91,
    fundraisingRatio: 8,
    operatingReserve: 11.2,
    transparencyScore: 96,
  },
  {
    id: '2',
    name: 'Teach For America',
    ein: '13-1624016',
    city: 'New York',
    state: 'NY',
    category: 'education',
    subcategory: 'Education',
    meritScore: 92,
    revenue: 350000000,
    assets: 450000000,
    employees: 2500,
    founded: 1989,
    mission: 'Teach For America finds, develops, and supports a diverse network of leaders who expand opportunity for children from classrooms, schools, and every sector that shapes the broader systems in which schools operate.',
    programs: ['Teacher Corps', 'Alumni Leadership', 'Policy & Advocacy'],
    leadership: [{ name: 'Elisa Villanueva Beard', title: 'CEO', initials: 'EV' }],
    boardSize: 22,
    revenueTrend: [
      { year: 2020, amount: 310000000 },
      { year: 2021, amount: 330000000 },
      { year: 2022, amount: 340000000 },
      { year: 2023, amount: 350000000 },
      { year: 2024, amount: 355000000 },
    ],
    programEfficiency: 88,
    fundraisingRatio: 10,
    operatingReserve: 9.8,
    transparencyScore: 94,
  },
  {
    id: '3',
    name: 'The Nature Conservancy',
    ein: '23-7923164',
    city: 'Arlington',
    state: 'VA',
    category: 'environment',
    subcategory: 'Environment',
    meritScore: 95,
    revenue: 1200000000,
    assets: 8900000000,
    employees: 4800,
    founded: 1951,
    mission: 'To conserve the lands and waters on which all life depends.',
    programs: ['Climate Change', 'Water Conservation', 'Land Protection', 'Ocean Health'],
    leadership: [{ name: 'Jennifer Morris', title: 'CEO', initials: 'JM' }],
    boardSize: 19,
    revenueTrend: [
      { year: 2020, amount: 950000000 },
      { year: 2021, amount: 1050000000 },
      { year: 2022, amount: 1120000000 },
      { year: 2023, amount: 1200000000 },
      { year: 2024, amount: 1250000000 },
    ],
    programEfficiency: 87,
    fundraisingRatio: 9,
    operatingReserve: 14.6,
    transparencyScore: 95,
  },
  {
    id: '4',
    name: 'Metropolitan Museum of Art',
    ein: '13-1624082',
    city: 'New York',
    state: 'NY',
    category: 'arts',
    subcategory: 'Arts & Culture',
    meritScore: 89,
    revenue: 420000000,
    assets: 3100000000,
    employees: 2200,
    founded: 1870,
    mission: 'To connect people to creativity, knowledge, and ideas.',
    programs: ['Exhibitions', 'Education', 'Conservation', 'Digital Initiatives'],
    leadership: [{ name: 'Max Hollein', title: 'Director & CEO', initials: 'MH' }],
    boardSize: 41,
    revenueTrend: [
      { year: 2020, amount: 280000000 },
      { year: 2021, amount: 340000000 },
      { year: 2022, amount: 380000000 },
      { year: 2023, amount: 420000000 },
      { year: 2024, amount: 445000000 },
    ],
    programEfficiency: 82,
    fundraisingRatio: 14,
    operatingReserve: 18.3,
    transparencyScore: 91,
  },
  {
    id: '5',
    name: 'Doctors Without Borders',
    ein: '13-1623456',
    city: 'New York',
    state: 'NY',
    category: 'health',
    subcategory: 'Health & Research',
    meritScore: 97,
    revenue: 580000000,
    assets: 320000000,
    employees: 45000,
    founded: 1971,
    mission: 'To provide impartial medical relief to the victims of war, disease, and natural or man-made disaster, without regard to race, religion, or political affiliation.',
    programs: ['Emergency Response', 'Vaccination Campaigns', 'Mental Health', 'Surgery'],
    leadership: [{ name: 'Avril Benoit', title: 'Executive Director', initials: 'AB' }],
    boardSize: 12,
    revenueTrend: [
      { year: 2020, amount: 420000000 },
      { year: 2021, amount: 510000000 },
      { year: 2022, amount: 540000000 },
      { year: 2023, amount: 580000000 },
      { year: 2024, amount: 600000000 },
    ],
    programEfficiency: 94,
    fundraisingRatio: 6,
    operatingReserve: 7.4,
    transparencyScore: 98,
  },
  {
    id: '6',
    name: 'Habitat for Humanity International',
    ein: '13-1625491',
    city: 'Atlanta',
    state: 'GA',
    category: 'community',
    subcategory: 'Community Development',
    meritScore: 91,
    revenue: 380000000,
    assets: 520000000,
    employees: 1800,
    founded: 1976,
    mission: 'Seeking to put God\'s love into action, Habitat for Humanity brings people together to build homes, communities, and hope.',
    programs: ['Home Building', 'Disaster Response', 'Advocacy', 'ReStore'],
    leadership: [{ name: 'Jonathan Reckford', title: 'CEO', initials: 'JR' }],
    boardSize: 15,
    revenueTrend: [
      { year: 2020, amount: 310000000 },
      { year: 2021, amount: 340000000 },
      { year: 2022, amount: 360000000 },
      { year: 2023, amount: 380000000 },
      { year: 2024, amount: 395000000 },
    ],
    programEfficiency: 86,
    fundraisingRatio: 11,
    operatingReserve: 10.2,
    transparencyScore: 93,
  },
  {
    id: '7',
    name: 'Salvation Army',
    ein: '13-1625533',
    city: 'Alexandria',
    state: 'VA',
    category: 'human-services',
    subcategory: 'Human Services',
    meritScore: 88,
    revenue: 5200000000,
    assets: 6800000000,
    employees: 96000,
    founded: 1865,
    mission: 'To preach the gospel of Jesus Christ and to meet human needs in His name without discrimination.',
    programs: ['Disaster Relief', 'Shelter & Housing', 'Youth Programs', 'Addiction Recovery'],
    leadership: [{ name: 'Kenneth Hodder', title: 'National Commander', initials: 'KH' }],
    boardSize: 14,
    revenueTrend: [
      { year: 2020, amount: 4800000000 },
      { year: 2021, amount: 5000000000 },
      { year: 2022, amount: 5100000000 },
      { year: 2023, amount: 5200000000 },
      { year: 2024, amount: 5300000000 },
    ],
    programEfficiency: 83,
    fundraisingRatio: 12,
    operatingReserve: 8.9,
    transparencyScore: 89,
  },
  {
    id: '8',
    name: 'St. Jude Children\'s Research Hospital',
    ein: '13-1625469',
    city: 'Memphis',
    state: 'TN',
    category: 'health',
    subcategory: 'Health & Research',
    meritScore: 98,
    revenue: 2100000000,
    assets: 6500000000,
    employees: 4800,
    founded: 1962,
    mission: 'Finding cures. Saving children.',
    programs: ['Pediatric Cancer Research', 'Patient Care', 'Global Outreach', 'Research Publications'],
    leadership: [{ name: 'James R. Downing', title: 'President & CEO', initials: 'JD' }],
    boardSize: 23,
    revenueTrend: [
      { year: 2020, amount: 1800000000 },
      { year: 2021, amount: 1950000000 },
      { year: 2022, amount: 2050000000 },
      { year: 2023, amount: 2100000000 },
      { year: 2024, amount: 2200000000 },
    ],
    programEfficiency: 92,
    fundraisingRatio: 7,
    operatingReserve: 22.1,
    transparencyScore: 99,
  },
  {
    id: '9',
    name: 'Khan Academy',
    ein: '26-1544963',
    city: 'Mountain View',
    state: 'CA',
    category: 'education',
    subcategory: 'Education',
    meritScore: 96,
    revenue: 85000000,
    assets: 120000000,
    employees: 180,
    founded: 2006,
    mission: 'To provide a free, world-class education for anyone, anywhere.',
    programs: ['K-12 Curriculum', 'Test Preparation', 'Computer Science', 'Language Learning'],
    leadership: [{ name: 'Sal Khan', title: 'Founder & CEO', initials: 'SK' }],
    boardSize: 9,
    revenueTrend: [
      { year: 2020, amount: 52000000 },
      { year: 2021, amount: 68000000 },
      { year: 2022, amount: 75000000 },
      { year: 2023, amount: 85000000 },
      { year: 2024, amount: 92000000 },
    ],
    programEfficiency: 96,
    fundraisingRatio: 4,
    operatingReserve: 16.8,
    transparencyScore: 97,
  },
  {
    id: '10',
    name: 'Sierra Club Foundation',
    ein: '13-1625501',
    city: 'Oakland',
    state: 'CA',
    category: 'environment',
    subcategory: 'Environment',
    meritScore: 87,
    revenue: 180000000,
    assets: 340000000,
    employees: 800,
    founded: 1960,
    mission: 'To advance the preservation and protection of the natural environment by empowering the citizenry, especially democratically elected officials, to adopt environmentally sound policies.',
    programs: ['Climate Justice', 'Wilderness Protection', 'Clean Energy', 'Environmental Education'],
    leadership: [{ name: 'Ben Jealous', title: 'Executive Director', initials: 'BJ' }],
    boardSize: 16,
    revenueTrend: [
      { year: 2020, amount: 140000000 },
      { year: 2021, amount: 160000000 },
      { year: 2022, amount: 170000000 },
      { year: 2023, amount: 180000000 },
      { year: 2024, amount: 185000000 },
    ],
    programEfficiency: 84,
    fundraisingRatio: 13,
    operatingReserve: 12.4,
    transparencyScore: 90,
  },
  {
    id: '11',
    name: 'Lincoln Center for the Performing Arts',
    ein: '13-1624089',
    city: 'New York',
    state: 'NY',
    category: 'arts',
    subcategory: 'Arts & Culture',
    meritScore: 85,
    revenue: 195000000,
    assets: 780000000,
    employees: 1200,
    founded: 1955,
    mission: 'To present the very best of the performing arts to the widest possible audience.',
    programs: ['Performances', 'Education', 'Community Engagement', 'Artist Development'],
    leadership: [{ name: 'Henry Timms', title: 'President & CEO', initials: 'HT' }],
    boardSize: 35,
    revenueTrend: [
      { year: 2020, amount: 85000000 },
      { year: 2021, amount: 130000000 },
      { year: 2022, amount: 165000000 },
      { year: 2023, amount: 195000000 },
      { year: 2024, amount: 210000000 },
    ],
    programEfficiency: 79,
    fundraisingRatio: 16,
    operatingReserve: 15.7,
    transparencyScore: 88,
  },
  {
    id: '12',
    name: 'Feeding America',
    ein: '13-1625537',
    city: 'Chicago',
    state: 'IL',
    category: 'human-services',
    subcategory: 'Human Services',
    meritScore: 93,
    revenue: 4200000000,
    assets: 280000000,
    employees: 350,
    founded: 1979,
    mission: 'To feed America\'s hungry through a nationwide network of member food banks and engage our country in the fight to end hunger.',
    programs: ['Food Distribution', 'Advocacy', 'Research', 'Disaster Response'],
    leadership: [{ name: 'Claire Babineaux-Fontenot', title: 'CEO', initials: 'CB' }],
    boardSize: 17,
    revenueTrend: [
      { year: 2020, amount: 3800000000 },
      { year: 2021, amount: 4100000000 },
      { year: 2022, amount: 4200000000 },
      { year: 2023, amount: 4200000000 },
      { year: 2024, amount: 4300000000 },
    ],
    programEfficiency: 98,
    fundraisingRatio: 3,
    operatingReserve: 3.2,
    transparencyScore: 95,
  },
  {
    id: '13',
    name: 'American Red Cross',
    ein: '53-0196605',
    city: 'Washington',
    state: 'DC',
    category: 'human-services',
    subcategory: 'Human Services',
    meritScore: 90,
    revenue: 3800000000,
    assets: 4600000000,
    employees: 22000,
    founded: 1881,
    mission: 'To prevent and alleviate human suffering in the face of emergencies by mobilizing the power of volunteers and the generosity of donors.',
    programs: ['Disaster Relief', 'Blood Services', 'Training & Certification', 'International Services'],
    leadership: [{ name: 'Gail J. McGovern', title: 'President & CEO', initials: 'GM' }],
    boardSize: 25,
    revenueTrend: [
      { year: 2020, amount: 3200000000 },
      { year: 2021, amount: 3500000000 },
      { year: 2022, amount: 3600000000 },
      { year: 2023, amount: 3800000000 },
      { year: 2024, amount: 3900000000 },
    ],
    programEfficiency: 89,
    fundraisingRatio: 9,
    operatingReserve: 10.5,
    transparencyScore: 92,
  },
  {
    id: '14',
    name: 'World Wildlife Fund',
    ein: '52-1693388',
    city: 'Washington',
    state: 'DC',
    category: 'environment',
    subcategory: 'Environment',
    meritScore: 88,
    revenue: 380000000,
    assets: 420000000,
    employees: 2400,
    founded: 1961,
    mission: 'To conserve nature and reduce the most pressing threats to the diversity of life on Earth.',
    programs: ['Wildlife Conservation', 'Climate & Energy', 'Food', 'Freshwater'],
    leadership: [{ name: 'Carter Roberts', title: 'President & CEO', initials: 'CR' }],
    boardSize: 20,
    revenueTrend: [
      { year: 2020, amount: 310000000 },
      { year: 2021, amount: 340000000 },
      { year: 2022, amount: 360000000 },
      { year: 2023, amount: 380000000 },
      { year: 2024, amount: 390000000 },
    ],
    programEfficiency: 85,
    fundraisingRatio: 11,
    operatingReserve: 9.6,
    transparencyScore: 91,
  },
  {
    id: '15',
    name: 'Memorial Sloan Kettering Cancer Center',
    ein: '13-1624074',
    city: 'New York',
    state: 'NY',
    category: 'health',
    subcategory: 'Health & Research',
    meritScore: 96,
    revenue: 5600000000,
    assets: 4200000000,
    employees: 21000,
    founded: 1884,
    mission: 'To lead the fight against cancer through patient care, research, and education.',
    programs: ['Cancer Research', 'Patient Care', 'Education', 'Early Detection'],
    leadership: [{ name: 'Selwyn M. Vickers', title: 'President & CEO', initials: 'SV' }],
    boardSize: 28,
    revenueTrend: [
      { year: 2020, amount: 4800000000 },
      { year: 2021, amount: 5100000000 },
      { year: 2022, amount: 5350000000 },
      { year: 2023, amount: 5600000000 },
      { year: 2024, amount: 5800000000 },
    ],
    programEfficiency: 90,
    fundraisingRatio: 8,
    operatingReserve: 6.8,
    transparencyScore: 94,
  },
  {
    id: '16',
    name: 'Goodwill Industries International',
    ein: '13-1625550',
    city: 'Rockville',
    state: 'MD',
    category: 'community',
    subcategory: 'Community Development',
    meritScore: 86,
    revenue: 6500000000,
    assets: 5200000000,
    employees: 140000,
    founded: 1902,
    mission: 'To enhance the dignity and quality of life of individuals and families by strengthening communities, eliminating barriers to opportunity, and helping people in need reach their full potential through learning and the power of work.',
    programs: ['Job Training', 'Employment Placement', 'Retail Operations', 'Youth Services'],
    leadership: [{ name: 'Steven C. Preston', title: 'President & CEO', initials: 'SP' }],
    boardSize: 13,
    revenueTrend: [
      { year: 2020, amount: 5800000000 },
      { year: 2021, amount: 6200000000 },
      { year: 2022, amount: 6400000000 },
      { year: 2023, amount: 6500000000 },
      { year: 2024, amount: 6600000000 },
    ],
    programEfficiency: 81,
    fundraisingRatio: 15,
    operatingReserve: 7.2,
    transparencyScore: 88,
  },
  {
    id: '17',
    name: 'Smithsonian Institution',
    ein: '53-0206027',
    city: 'Washington',
    state: 'DC',
    category: 'arts',
    subcategory: 'Arts & Culture',
    meritScore: 91,
    revenue: 1400000000,
    assets: 2800000000,
    employees: 6400,
    founded: 1846,
    mission: 'The increase and diffusion of knowledge.',
    programs: ['Museums', 'Research', 'Education', 'Cultural Heritage'],
    leadership: [{ name: 'Lonnie G. Bunch III', title: 'Secretary', initials: 'LB' }],
    boardSize: 20,
    revenueTrend: [
      { year: 2020, amount: 1100000000 },
      { year: 2021, amount: 1250000000 },
      { year: 2022, amount: 1320000000 },
      { year: 2023, amount: 1400000000 },
      { year: 2024, amount: 1450000000 },
    ],
    programEfficiency: 78,
    fundraisingRatio: 5,
    operatingReserve: 8.4,
    transparencyScore: 93,
  },
  {
    id: '18',
    name: 'Boys & Girls Clubs of America',
    ein: '13-1625540',
    city: 'Atlanta',
    state: 'GA',
    category: 'community',
    subcategory: 'Community Development',
    meritScore: 89,
    revenue: 1200000000,
    assets: 1800000000,
    employees: 2800,
    founded: 1906,
    mission: 'To enable all young people, especially those who need us most, to reach their full potential as productive, caring, responsible citizens.',
    programs: ['After School Programs', 'Sports & Recreation', 'Education', 'Career Development'],
    leadership: [{ name: 'Jim Clark', title: 'President & CEO', initials: 'JC' }],
    boardSize: 24,
    revenueTrend: [
      { year: 2020, amount: 950000000 },
      { year: 2021, amount: 1080000000 },
      { year: 2022, amount: 1150000000 },
      { year: 2023, amount: 1200000000 },
      { year: 2024, amount: 1250000000 },
    ],
    programEfficiency: 87,
    fundraisingRatio: 10,
    operatingReserve: 13.5,
    transparencyScore: 90,
  },
];

export default organizations;

export function getOrganizationById(id: string): Organization | undefined {
  return organizations.find((o: Organization) => o.id === id);
}

export function getOrganizationsByCategory(categoryId: string): Organization[] {
  return organizations.filter((o: Organization) => o.category === categoryId);
}

export function searchOrganizations(query: string): Organization[] {
  const q = query.toLowerCase();
  return organizations.filter((o: Organization) =>
    o.name.toLowerCase().includes(q) ||
    o.city.toLowerCase().includes(q) ||
    o.ein.includes(q) ||
    o.category.toLowerCase().includes(q) ||
    o.subcategory.toLowerCase().includes(q)
  );
}

export function formatCurrency(value: number): string {
  const trim = (n: number, unit: string) => {
    const s = n.toFixed(1)
    return `$${s.endsWith('.0') ? s.slice(0, -2) : s}${unit}`
  }
  if (value >= 1e9) return trim(value / 1e9, 'B')
  if (value >= 1e6) return trim(value / 1e6, 'M')
  if (value >= 100_000) return trim(value / 1_000, 'K')
  return `$${value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
}

export function formatNumber(value: number): string {
  return value.toLocaleString('en-US');
}

export function getScoreColor(score: number): string {
  if (score >= 80) return 'bg-success-green';
  if (score >= 60) return 'bg-soft-gold';
  return 'bg-cool-grey';
}

// How big this organization is financially next to others doing similar work.
// Plain human language. Never about impact, quality, or worth.
export function getScoreLabel(score: number): string {
  if (score >= 90) return 'Among the largest like it';
  if (score >= 75) return 'Larger than most like it';
  if (score >= 60) return 'A bit larger than most';
  if (score >= 40) return 'About average in size';
  return 'Smaller than most like it';
}
