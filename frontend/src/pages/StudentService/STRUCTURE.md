# Student Service Frontend Component Structure
**Status:** Design Phase (Week 1)  
**Framework:** React 19, TypeScript, Vite, Tailwind CSS + Radix UI  
**Privacy:** No student data exposed publicly; minimal data collection  

---

## Directory Structure

```
frontend/src/pages/StudentService/
├── index.tsx                           # Main export
├── STRUCTURE.md                        # This file
│
├── pages/
│   ├── DiscoverPage.tsx               # Student finds volunteer opportunities
│   ├── ServiceLogPage.tsx             # Student logs and views service hours
│   ├── CertificatePage.tsx            # Student views/downloads certificate
│   ├── ProfilePage.tsx                # Student profile & account settings
│   ├── DisputePage.tsx                # Student files disputes
│   └── DataManagementPage.tsx         # Export/delete data (GDPR/CCPA)
│
├── components/
│   ├── OpportunityCard.tsx            # Card showing one opportunity
│   ├── OpportunitySearch.tsx          # Search/filter opportunities
│   ├── OpportunityDetailModal.tsx     # Full opportunity details + enroll button
│   ├── ServiceLogForm.tsx             # Form to submit hours
│   ├── ServiceLogItem.tsx             # Displays one submitted log entry
│   ├── ServiceLogList.tsx             # Displays all logs with filtering
│   ├── ServiceLogStatus.tsx           # Visual indicator (submitted/approved/rejected)
│   ├── CertificateViewer.tsx          # Display certificate details
│   ├── CertificateDownloadButton.tsx  # PDF download
│   ├── DisputeForm.tsx                # Form to file dispute
│   ├── DisputeTimeline.tsx            # Shows dispute resolution progress
│   ├── StudentProfileForm.tsx         # Edit profile (limited fields)
│   ├── EnrollmentSummary.tsx          # Card showing student stats
│   ├── OrganizationListInline.tsx     # Shows orgs student has served
│   └── PrivacyNotice.tsx              # Explains data handling
│
├── hooks/
│   ├── useStudentProfile.ts           # Fetch/update student profile
│   ├── useServiceLog.ts               # Manage service log submissions
│   ├── useOpportunities.ts            # Fetch opportunities with filtering
│   ├── useCertificate.ts              # Fetch certificate data
│   ├── useDisputes.ts                 # Fetch disputes and mediation status
│   ├── useStudentAuth.ts              # Handle Firebase auth for students
│   └── useStudentData.ts              # Export/delete student data
│
├── contexts/
│   ├── StudentServiceContext.tsx      # Global student service state
│   ├── StudentAuthContext.tsx         # Global auth state (Firebase)
│   └── StudentNotificationContext.tsx # Toast/notification management
│
├── types/
│   ├── student.ts                     # Student account & profile types
│   ├── opportunity.ts                 # Opportunity & enrollment types
│   ├── service-log.ts                 # Service log & approval types
│   ├── certificate.ts                 # Certificate types
│   └── dispute.ts                     # Dispute & mediation types
│
├── utils/
│   ├── studentApi.ts                  # API client wrapper (all /api/student/* endpoints)
│   ├── hoursFormatter.ts              # Format hours (4.5 → "4 hours 30 minutes")
│   ├── certificateGenerator.ts        # Local certificate PDF generation
│   ├── privacyHelpers.ts              # Data minimization helpers
│   └── validation.ts                  # Form validation (hours, dates, etc)
│
└── styles/
    └── student-service.css             # Service-specific styles (if needed beyond Tailwind)
```

---

## Core Pages

### 1. DiscoverPage.tsx
**Purpose:** Student finds volunteer opportunities  
**Route:** `/student/discover` or `/volunteer/discover`  

**Features:**
- Search bar (keyword search)
- Filter by cause area (education, health, etc)
- Filter by location/type (in-person, hybrid, remote)
- Sort options (recent, popular, commitment hours)
- Pagination
- Opportunity cards with "Enroll" button

**Components Used:**
- `OpportunitySearch` (header with search/filter controls)
- `OpportunityCard` (repeating list items)
- `OpportunityDetailModal` (opens on click; shows full details + enroll button)

**State:**
- Opportunities list (from API)
- Filter/search state
- Current page
- Loading state
- Error state

**API Calls:**
- `GET /api/student/opportunities?cause=...&location=...&page=...`

---

### 2. ServiceLogPage.tsx
**Purpose:** Student logs hours and views submissions  
**Route:** `/student/service-log`  

**Features:**
- Form to submit new hours (date, org, hours, activity description)
- List of all submitted hours (filterable by status/org)
- Status badges (submitted, pending, approved, rejected)
- Edit unapproved entries (in-place edit form)
- Delete unapproved entries (with confirmation)
- Summary stats (total hours, pending hours, approved hours)

**Components Used:**
- `ServiceLogForm` (new submission form)
- `ServiceLogList` (all submissions)
- `ServiceLogItem` (individual entry with actions)
- `ServiceLogStatus` (visual indicator badge)
- `EnrollmentSummary` (stats card)

**State:**
- Service logs list
- Form state (new submission)
- Editing state (which log is being edited)
- Filters (status, org)
- Loading state

**API Calls:**
- `GET /api/student/service-log?status=...&nonprofit_ein=...`
- `POST /api/student/service-log/submit`
- `PUT /api/student/service-log/{id}`
- `DELETE /api/student/service-log/{id}`

---

### 3. CertificatePage.tsx
**Purpose:** Student views and downloads verified service certificate  
**Route:** `/student/certificate`  

**Features:**
- Certificate details (total hours, period, status)
- Organizations served (list with hours per org)
- Download PDF button
- Share verification link (copies to clipboard)
- View certificate expiration (if applicable)
- Message if no certificate yet (needs minimum hours)

**Components Used:**
- `CertificateViewer` (display certificate details)
- `CertificateDownloadButton` (PDF download)
- `OrganizationListInline` (shows orgs served)

**State:**
- Certificate data
- Download loading state
- Share copy state (confirmation toast)

**API Calls:**
- `GET /api/student/certificate`
- `GET /api/student/certificate/download` (triggers file download)

---

### 4. ProfilePage.tsx
**Purpose:** Student manages account and data  
**Route:** `/student/profile`  

**Features:**
- View profile (name, school, enrollment date)
- Edit email/phone (limited fields)
- View enrollment status
- View total hours submitted/approved
- Data management section (export/delete)
- Privacy notice explaining data handling

**Components Used:**
- `StudentProfileForm` (editable profile fields)
- `EnrollmentSummary` (stats)
- `PrivacyNotice` (explains data handling)
- Data export/delete buttons

**State:**
- Profile data
- Edit mode toggle
- Export/delete confirmation state
- Loading state

**API Calls:**
- `GET /api/student/profile`
- `PUT /api/student/profile`
- `POST /api/student/data-export`
- `DELETE /api/student/account` (with confirmation modal)

---

### 5. DisputePage.tsx
**Purpose:** Student files dispute if hours rejected or adjusted  
**Route:** `/student/disputes`  

**Features:**
- List of disputes filed
- File new dispute button (opens form modal)
- Dispute timeline showing resolution progress
- School admin's decision and notes
- Option to escalate if unresolved after X days

**Components Used:**
- `DisputeForm` (new dispute form)
- `DisputeTimeline` (shows resolution progress)

**State:**
- Disputes list
- Form state (new dispute)
- Selected dispute (for timeline view)
- Loading state

**API Calls:**
- `GET /api/student/disputes`
- `POST /api/student/disputes`

---

### 6. DataManagementPage.tsx
**Purpose:** GDPR/CCPA compliance — export or delete data  
**Route:** `/student/data-management`  

**Features:**
- Export all data as JSON/CSV
- Download confirmation + privacy statement
- Delete account option (with irreversibility warning)
- View data retention policy

**Components Used:**
- Export button
- Delete account modal
- Privacy policy link

**State:**
- Export status (processing/ready)
- Delete confirmation state

**API Calls:**
- `POST /api/student/data-export`
- `DELETE /api/student/account`

---

## Core Components

### OpportunityCard.tsx
**Props:**
```typescript
interface OpportunityCardProps {
  opportunity: {
    opportunity_id: string;
    nonprofit_name: string;
    title: string;
    cause_area: string;
    commitment_hours?: number;
    location_type: 'in-person' | 'hybrid' | 'remote';
  };
  enrollment_status?: 'interested' | 'committed' | 'in-progress';
  onEnroll: () => void;
  onViewDetails: () => void;
}
```

**Features:**
- Displays org logo/name
- Shows title and cause area
- Shows location type (in-person badge, etc)
- Shows commitment hours (if available)
- "Enroll" button (changes to "Enrolled ✓" if already enrolled)
- "View Details" link (opens full modal)

---

### ServiceLogForm.tsx
**Props:**
```typescript
interface ServiceLogFormProps {
  opportunity_id?: string;  // Pre-fill if from discover flow
  nonprofit_ein?: string;
  onSubmit: (data: ServiceLogSubmission) => Promise<void>;
  onCancel?: () => void;
  loading?: boolean;
}
```

**Features:**
- Org selector (searchable dropdown)
- Date picker (service date)
- Hours input (validates 0.5-24)
- Activity description (text area)
- Supervisor name (optional text input)
- Submit/Cancel buttons
- Error messages (inline validation)

---

### ServiceLogStatus.tsx
**Props:**
```typescript
interface ServiceLogStatusProps {
  status: 'submitted' | 'approved' | 'rejected' | 'flagged' | 'disputed';
  rejectionReason?: string;
  flags?: string[];
}
```

**Features:**
- Visual badge (color-coded: blue/green/red/yellow/orange)
- Status text
- Tooltip showing details if rejected or flagged

---

### CertificateViewer.tsx
**Props:**
```typescript
interface CertificateViewerProps {
  certificate: StudentCertificate;
  onDownload?: () => void;
}
```

**Features:**
- Certificate number (for public verification)
- Total hours verified
- Service period
- List of orgs served (with hours each)
- Issue date
- "Download PDF" button
- "Share verification link" button (copies daanaa.org/verify/{number})

---

## Hooks (Custom)

### useStudentProfile.ts
```typescript
const { profile, loading, error, updateProfile } = useStudentProfile();
```

**Features:**
- Fetches student profile on mount
- Handles update with API call
- Error handling
- Auto-refresh after update

---

### useServiceLog.ts
```typescript
const {
  logs,
  loading,
  error,
  submitLog,
  updateLog,
  deleteLog,
  fetchLogs
} = useServiceLog();
```

**Features:**
- Fetches service logs with filtering
- Handles submit/update/delete operations
- Error handling
- Optimistic updates

---

### useOpportunities.ts
```typescript
const {
  opportunities,
  loading,
  error,
  search,
  filter,
  sort,
  currentPage,
  totalPages
} = useOpportunities();
```

**Features:**
- Fetches opportunities with search/filter/sort
- Handles pagination
- Error handling
- Debounced search

---

## Types (TypeScript)

### student.ts
```typescript
export interface StudentAccount {
  student_id: string;
  first_name: string;
  last_name: string;
  email: string;
  school_ein: string;
  school_name: string;
  date_of_birth: Date;
  age_group: '13-17' | '18-24' | '25+';
  parental_consent_required: boolean;
  parental_consent_given: boolean;
  student_consent_given: boolean;
  enrollment_status: 'invited' | 'active' | 'completed' | 'paused' | 'withdrawn';
  enrolled_at: Date;
  total_hours_submitted: number;
  total_hours_approved: number;
}
```

### opportunity.ts
```typescript
export interface Opportunity {
  opportunity_id: string;
  nonprofit_ein: string;
  nonprofit_name: string;
  title: string;
  description: string;
  cause_area: string;
  location: string;
  location_type: 'in-person' | 'hybrid' | 'remote';
  commitment_hours: number;
  available_start: Date;
  available_end: Date;
  supervisor_name: string;
}

export interface OpportunityEnrollment {
  enrollment_id: string;
  student_id: string;
  opportunity_id: string;
  hours_committed: number;
  status: 'interested' | 'committed' | 'in-progress' | 'completed' | 'withdrawn';
}
```

### service-log.ts
```typescript
export interface ServiceLog {
  service_log_id: string;
  student_id: string;
  nonprofit_ein: string;
  nonprofit_name: string;
  service_date: Date;
  hours_claimed: number;
  activity_description: string;
  submission_status: 'submitted' | 'approved' | 'rejected' | 'flagged' | 'disputed';
  submitted_at: Date;
  approved_at?: Date;
  rejected_reason?: string;
}

export interface ServiceLogSubmission {
  nonprofit_ein: string;
  service_date: Date;
  hours_claimed: number;
  activity_description: string;
  supervisor_name?: string;
}
```

### certificate.ts
```typescript
export interface StudentCertificate {
  certificate_id: string;
  certificate_number: string;
  student_id: string;
  total_hours_verified: number;
  service_period_start: Date;
  service_period_end: Date;
  issued_at: Date;
  status: 'active' | 'revoked' | 'disputed';
  organizations_served: {
    nonprofit_ein: string;
    nonprofit_name: string;
    hours_verified: number;
  }[];
}
```

---

## API Client (studentApi.ts)

```typescript
export const studentApi = {
  // Opportunities
  getOpportunities: (filters: OpportunityFilters) => GET /api/student/opportunities
  enrollOpportunity: (opportunityId: string) => POST /api/student/opportunities/{id}/enroll

  // Service Log
  getServiceLogs: (filters: ServiceLogFilters) => GET /api/student/service-log
  submitServiceLog: (data: ServiceLogSubmission) => POST /api/student/service-log/submit
  updateServiceLog: (id: string, data: Partial<ServiceLogSubmission>) => PUT /api/student/service-log/{id}
  deleteServiceLog: (id: string) => DELETE /api/student/service-log/{id}

  // Certificate
  getCertificate: () => GET /api/student/certificate
  downloadCertificate: () => GET /api/student/certificate/download

  // Profile
  getProfile: () => GET /api/student/profile
  updateProfile: (data: Partial<StudentAccount>) => PUT /api/student/profile

  // Disputes
  getDisputes: () => GET /api/student/disputes
  fileDispute: (data: DisputeSubmission) => POST /api/student/disputes

  // Data management
  exportData: () => POST /api/student/data-export
  deleteAccount: () => DELETE /api/student/account
};
```

---

## Privacy & Security

### Data Minimization
- Only collect: name, email, school, DOB, service records
- Never collect: address, phone (optional), social media, browsing history

### No Public Profiles
- Students can't view each other
- Students can't message each other
- Supervisors only see student name during verification (school context)

### No IP Persistence
- Log IP for fraud detection only
- Hash IP in audit trail
- Delete raw IP after 7 days

### Consent Management
- Clear consent forms before enrollment
- Parental consent if required by age
- Student can withdraw at any time
- Right to deletion (GDPR/CCPA)

### Audit Trail
- All actions logged with actor, action, timestamp
- Student data accessible for audit
- No access logs shown to students

---

## Testing Strategy

### Unit Tests
- Component rendering (mocked API)
- Form validation (hours, dates)
- Data formatting (hours → human readable)

### Integration Tests
- Discover → Enroll flow
- Log → Approve → Certificate flow
- Dispute filing and resolution

### Privacy Tests
- Verify no student data in public API
- Verify no student-to-student messaging
- Verify IP hashing in audit logs

### Manual QA
- Login flow (Firebase)
- Search/filter opportunities
- Submit hours (various inputs)
- Download certificate
- File dispute
- Export/delete data

---

## Accessibility (WCAG 2.2 AA)

- Semantic HTML (buttons, links, forms)
- Form labels and error messages
- Keyboard navigation (Tab, Enter, Escape)
- Color contrast (Radix UI components)
- Screen reader compatibility (aria-labels)
- Mobile viewport (responsive, touch-friendly)

---

## Implementation Order

**Week 2-3:**
1. Setup StudentService directory & structure
2. Create context + hooks (auth, profile, opportunities)
3. Implement DiscoverPage + components
4. Implement ServiceLogPage + components
5. Implement CertificatePage + components

**Week 4-5:**
1. Implement ProfilePage + data management
2. Implement DisputePage
3. Add Firebase authentication for students
4. Add form validation & error handling
5. Mobile testing & responsive fixes

**Week 6:**
1. Security review (IP hashing, audit trail)
2. Accessibility audit (WCAG 2.2 AA)
3. Performance optimization
4. QA & bug fixes
