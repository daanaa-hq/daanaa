-- Phase 3: Letter Credits, Donor Tracking, Volunteer Exports
-- Date: 2026-06-21

-- Letter credit purchases with Stripe payment tracking
CREATE TABLE IF NOT EXISTS letter_credit_purchases (
  id TEXT PRIMARY KEY,
  nonprofit_ein TEXT NOT NULL,
  stripe_payment_intent_id TEXT UNIQUE,
  stripe_customer_id TEXT,
  amount_cents INTEGER NOT NULL,
  currency TEXT DEFAULT 'usd',
  letters_acquired INTEGER NOT NULL,
  status TEXT DEFAULT 'pending',
  payment_method_type TEXT,
  idempotency_key TEXT UNIQUE,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT,
  webhook_received_at TEXT,
  error_message TEXT,
  FOREIGN KEY (nonprofit_ein) REFERENCES nonprofit_accounts(ein)
);

CREATE INDEX IF NOT EXISTS idx_letter_purchases_stripe ON letter_credit_purchases(stripe_payment_intent_id);
CREATE INDEX IF NOT EXISTS idx_letter_purchases_nonprofit ON letter_credit_purchases(nonprofit_ein, created_at);
CREATE INDEX IF NOT EXISTS idx_letter_purchases_status ON letter_credit_purchases(nonprofit_ein, status);
CREATE INDEX IF NOT EXISTS idx_letter_purchases_idempotency ON letter_credit_purchases(idempotency_key);

-- Donor message tracking with pixel events
CREATE TABLE IF NOT EXISTS donor_messages (
  id TEXT PRIMARY KEY,
  nonprofit_ein TEXT NOT NULL,
  donor_email TEXT NOT NULL,
  donor_name TEXT,
  message_subject TEXT NOT NULL,
  message_body TEXT NOT NULL,
  template_id TEXT,
  tracking_pixel_id TEXT UNIQUE NOT NULL,
  tracking_pixel_url TEXT NOT NULL,
  delivery_status TEXT DEFAULT 'draft',
  sent_at TEXT,
  first_opened_at TEXT,
  open_count INTEGER DEFAULT 0,
  link_clicks INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (nonprofit_ein) REFERENCES nonprofit_accounts(ein)
);

CREATE INDEX IF NOT EXISTS idx_donor_messages_nonprofit ON donor_messages(nonprofit_ein, created_at);
CREATE INDEX IF NOT EXISTS idx_donor_messages_pixel ON donor_messages(tracking_pixel_id);
CREATE INDEX IF NOT EXISTS idx_donor_messages_status ON donor_messages(nonprofit_ein, delivery_status);
CREATE INDEX IF NOT EXISTS idx_donor_messages_email ON donor_messages(nonprofit_ein, donor_email);

-- Pixel events (tracking opens and interactions)
CREATE TABLE IF NOT EXISTS donor_message_events (
  id TEXT PRIMARY KEY,
  message_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  event_timestamp TEXT NOT NULL,
  ip_address TEXT,
  user_agent TEXT,
  referer TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (message_id) REFERENCES donor_messages(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_message_events_message ON donor_message_events(message_id, event_type);
CREATE INDEX IF NOT EXISTS idx_message_events_timestamp ON donor_message_events(event_timestamp);

-- Enhanced background jobs for multi-format exports
CREATE TABLE IF NOT EXISTS background_job_configs (
  id TEXT PRIMARY KEY,
  nonprofit_ein TEXT NOT NULL,
  job_type TEXT NOT NULL,
  format TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  data_type TEXT NOT NULL,
  filter_params TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  started_at TEXT,
  completed_at TEXT,
  result_path TEXT,
  result_size_bytes INTEGER,
  error_message TEXT,
  FOREIGN KEY (nonprofit_ein) REFERENCES nonprofit_accounts(ein)
);

CREATE INDEX IF NOT EXISTS idx_job_status ON background_job_configs(nonprofit_ein, status, created_at);
CREATE INDEX IF NOT EXISTS idx_job_type ON background_job_configs(nonprofit_ein, job_type);
CREATE INDEX IF NOT EXISTS idx_job_created ON background_job_configs(created_at);

-- Impact forecast data (materialized for dashboard)
CREATE TABLE IF NOT EXISTS impact_forecasts (
  id TEXT PRIMARY KEY,
  nonprofit_ein TEXT NOT NULL,
  forecast_date TEXT NOT NULL,
  metric_type TEXT NOT NULL,
  current_value REAL NOT NULL,
  projected_value REAL NOT NULL,
  trend_direction TEXT,
  confidence_percent REAL,
  calculation_notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(nonprofit_ein, forecast_date, metric_type),
  FOREIGN KEY (nonprofit_ein) REFERENCES nonprofit_accounts(ein)
);

CREATE INDEX IF NOT EXISTS idx_forecast_latest ON impact_forecasts(nonprofit_ein, forecast_date DESC);
