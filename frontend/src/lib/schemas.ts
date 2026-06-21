import { z } from 'zod'

/**
 * Donor template schema
 */
export const DonorTemplateSchema = z.object({
  id: z.string(),
  template_name: z.string().min(1),
  template_body: z.string().min(1),
  is_default: z.boolean(),
  sample_preview: z.string(),
  created_at: z.string(),
  updated_at: z.string().optional(),
})
export type DonorTemplate = z.infer<typeof DonorTemplateSchema>

/**
 * Volunteer insights (hours summary)
 */
export const VolunteerInsightsSchema = z.object({
  total_hours_period: z.number().nonnegative(),
  total_hours_previous_period: z.number().nonnegative(),
  trend_direction: z.enum(['up', 'down', 'flat']),
  trend_percent: z.number(),
  top_volunteers: z.array(z.object({
    name: z.string(),
    hours: z.number().positive(),
  })).default([]),
  approved_count: z.number().nonnegative(),
  pending_count: z.number().nonnegative(),
  rejected_count: z.number().nonnegative(),
})
export type VolunteerInsights = z.infer<typeof VolunteerInsightsSchema>

/**
 * Background job status (for CSV exports)
 */
export const BackgroundJobSchema = z.object({
  job_id: z.string(),
  status: z.enum(['pending', 'processing', 'complete', 'failed']),
  download_link: z.string().optional(),
  created_at: z.string(),
  completed_at: z.string().optional(),
  error_message: z.string().optional(),
})
export type BackgroundJob = z.infer<typeof BackgroundJobSchema>

/**
 * Export initiation response
 */
export const ExportInitiationSchema = z.object({
  job_id: z.string(),
  status: z.enum(['pending']),
  message: z.string(),
})
export type ExportInitiation = z.infer<typeof ExportInitiationSchema>

// ─────────────────────────────────────────────────────────────────────────
// PHASE 3: Letter Credits, Donor Messages, Impact Metrics
// ─────────────────────────────────────────────────────────────────────────

/**
 * Letter credit balance
 */
export const LetterCreditBalanceSchema = z.object({
  nonprofit_ein: z.string(),
  letters_remaining: z.number().nonnegative(),
  lifetime_purchases: z.number().nonnegative(),
  lifetime_spend_cents: z.number().nonnegative(),
  last_purchase: z.object({
    purchase_id: z.string(),
    letters_acquired: z.number().positive(),
    completed_at: z.string(),
  }).nullable(),
  next_renewal_date: z.string().nullable(),
})
export type LetterCreditBalance = z.infer<typeof LetterCreditBalanceSchema>

/**
 * Letter credit purchase response
 */
export const LetterCreditPurchaseSchema = z.object({
  purchase_id: z.string(),
  status: z.enum(['pending', 'succeeded', 'failed']),
  stripe_intent_id: z.string().nullable(),
  created_at: z.string(),
  message: z.string().optional(),
})
export type LetterCreditPurchase = z.infer<typeof LetterCreditPurchaseSchema>

/**
 * Donor message (for listing and display)
 */
export const DonorMessageSchema = z.object({
  id: z.string(),
  donor_email: z.string().email(),
  donor_name: z.string(),
  message_subject: z.string(),
  delivery_status: z.enum(['draft', 'queued', 'sent', 'failed']),
  sent_at: z.string().nullable(),
  open_count: z.number().nonnegative().default(0),
  link_clicks: z.number().nonnegative().default(0),
  first_opened_at: z.string().nullable(),
})
export type DonorMessage = z.infer<typeof DonorMessageSchema>

/**
 * Donor message send request
 */
export const DonorMessageSendSchema = z.object({
  donor_email: z.string().email('Invalid email'),
  donor_name: z.string().min(1, 'Donor name required'),
  message_subject: z.string().min(1, 'Subject required'),
  message_body: z.string().min(10, 'Message must be at least 10 characters'),
  template_id: z.string().optional(),
  track_opens: z.boolean().default(true),
})
export type DonorMessageSend = z.infer<typeof DonorMessageSendSchema>

/**
 * Donor message tracking event
 */
export const DonorMessageEventSchema = z.object({
  event_id: z.string(),
  event_type: z.enum(['open', 'link_click', 'unsubscribe']),
  event_timestamp: z.string(),
  ip_address: z.string().nullable(),
  user_agent: z.string().nullable(),
})
export type DonorMessageEvent = z.infer<typeof DonorMessageEventSchema>

/**
 * Message events list response
 */
export const MessageEventsResponseSchema = z.object({
  message_id: z.string(),
  total_opens: z.number().nonnegative(),
  unique_opens: z.number().nonnegative(),
  link_clicks: z.number().nonnegative(),
  events: z.array(DonorMessageEventSchema).default([]),
})
export type MessageEventsResponse = z.infer<typeof MessageEventsResponseSchema>

/**
 * Impact metrics: credit utilization
 */
export const CreditUtilizationSchema = z.object({
  letters_purchased: z.number().nonnegative(),
  letters_used: z.number().nonnegative(),
  utilization_percent: z.number().min(0).max(100),
  trend: z.enum(['up', 'down', 'flat']),
  monthly_spend: z.number().nonnegative(),
})
export type CreditUtilization = z.infer<typeof CreditUtilizationSchema>

/**
 * Impact metrics: donor engagement
 */
export const DonorEngagementSchema = z.object({
  messages_sent: z.number().nonnegative(),
  avg_open_rate: z.number().min(0).max(1),
  avg_click_rate: z.number().min(0).max(1),
  unique_donors_contacted: z.number().nonnegative(),
  trend: z.enum(['up', 'down', 'flat']),
})
export type DonorEngagement = z.infer<typeof DonorEngagementSchema>

/**
 * Impact metrics: volunteer impact
 */
export const VolunteerImpactMetricSchema = z.object({
  total_hours_verified: z.number().nonnegative(),
  volunteer_count: z.number().nonnegative(),
  avg_hours_per_volunteer: z.number().nonnegative(),
  value_at_28_50_per_hour: z.number().nonnegative(),
  trend: z.enum(['up', 'down', 'flat']),
})
export type VolunteerImpactMetric = z.infer<typeof VolunteerImpactMetricSchema>

/**
 * Impact metrics: revenue equivalent
 */
export const RevenueEquivalentSchema = z.object({
  letters_generated_value: z.number().nonnegative(),
  volunteer_hours_value: z.number().nonnegative(),
  total_impact_value: z.number().nonnegative(),
  trend: z.enum(['up', 'down', 'flat']),
})
export type RevenueEquivalent = z.infer<typeof RevenueEquivalentSchema>

/**
 * Impact metrics: forecast
 */
export const ForecastSchema = z.object({
  projected_letters_next_month: z.number().nonnegative(),
  projected_volunteer_hours: z.number().nonnegative(),
  confidence_percent: z.number().min(0).max(1),
  calculated_at: z.string(),
})
export type Forecast = z.infer<typeof ForecastSchema>

/**
 * Complete impact metrics response
 */
export const ImpactMetricsSchema = z.object({
  nonprofit_ein: z.string(),
  period: z.string(),
  metrics: z.object({
    credit_utilization: CreditUtilizationSchema,
    donor_engagement: DonorEngagementSchema,
    volunteer_impact: VolunteerImpactMetricSchema,
    revenue_equivalent: RevenueEquivalentSchema,
    forecast: ForecastSchema,
  }),
})
export type ImpactMetrics = z.infer<typeof ImpactMetricsSchema>
