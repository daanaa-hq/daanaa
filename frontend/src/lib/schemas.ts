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
