#!/usr/bin/env node

/**
 * Ralph Codex Review Logger
 *
 * Logs Codex review results:
 * - Token usage (actual vs. baseline)
 * - Issues caught (pre-checks vs. Codex)
 * - Governance gate compliance
 * - Review recommendations
 *
 * Maintains: docs/ralph_codex_reviews.jsonl
 *
 * Usage:
 *   node scripts/ralph-log-codex-review.js --task-id <id> --tokens-used 2500 --findings 3
 */

const fs = require('fs');
const path = require('path');

const REVIEWS_LOG = path.join(__dirname, '../docs/ralph_codex_reviews.jsonl');
const METRICS_FILE = path.join(__dirname, '../docs/codex_metrics.json');

class CodexReviewLogger {
  constructor() {
    this.ensureLogFile();
  }

  ensureLogFile() {
    const dir = path.dirname(REVIEWS_LOG);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    if (!fs.existsSync(REVIEWS_LOG)) {
      fs.writeFileSync(REVIEWS_LOG, '');
    }
  }

  logReview(review) {
    const entry = {
      timestamp: new Date().toISOString(),
      ...review,
      unix_time: Math.floor(Date.now() / 1000),
    };

    // Append to JSONL
    fs.appendFileSync(REVIEWS_LOG, JSON.stringify(entry) + '\n');

    // Update metrics
    this.updateMetrics(entry);

    console.log(`✅ Review logged: ${review.task_id}`);
  }

  updateMetrics(entry) {
    let metrics = this.loadMetrics();

    metrics.last_updated = entry.timestamp;
    metrics.total_reviews = (metrics.total_reviews || 0) + 1;
    metrics.total_tokens_used = (metrics.total_tokens_used || 0) + (entry.tokens_used || 0);
    metrics.total_findings = (metrics.total_findings || 0) + (entry.findings_count || 0);

    // Track by review type
    if (!metrics.by_type) metrics.by_type = {};
    const reviewType = entry.review_type || 'unknown';
    if (!metrics.by_type[reviewType]) {
      metrics.by_type[reviewType] = { count: 0, tokens: 0, findings: 0 };
    }
    metrics.by_type[reviewType].count += 1;
    metrics.by_type[reviewType].tokens += entry.tokens_used || 0;
    metrics.by_type[reviewType].findings += entry.findings_count || 0;

    // Track pre-check effectiveness
    if (!metrics.pre_check_stats) metrics.pre_check_stats = {};
    metrics.pre_check_stats.semgrep_findings = (metrics.pre_check_stats.semgrep_findings || 0) + (entry.semgrep_findings || 0);
    metrics.pre_check_stats.lint_errors = (metrics.pre_check_stats.lint_errors || 0) + (entry.lint_errors || 0);
    metrics.pre_check_stats.codex_findings = (metrics.pre_check_stats.codex_findings || 0) + (entry.codex_findings || 0);

    // Calculate savings vs. baseline
    const baselineTokens = {
      architecture: 12000,
      security: 12000,
      code: 8000,
    };
    const baseline = baselineTokens[reviewType] || 10000;
    metrics.estimated_monthly_savings = this.calculateSavings(metrics, baseline);

    fs.writeFileSync(METRICS_FILE, JSON.stringify(metrics, null, 2));
  }

  calculateSavings(metrics, baseline) {
    if (!metrics.by_type || metrics.total_reviews === 0) return 0;
    const avgTokens = metrics.total_tokens_used / metrics.total_reviews;
    return Math.round((1 - avgTokens / baseline) * 100);
  }

  loadMetrics() {
    if (fs.existsSync(METRICS_FILE)) {
      try {
        return JSON.parse(fs.readFileSync(METRICS_FILE, 'utf8'));
      } catch (e) {
        return {};
      }
    }
    return {};
  }

  printSummary() {
    const metrics = this.loadMetrics();
    console.log('\n' + '='.repeat(60));
    console.log('Codex Review Metrics (All-Time)');
    console.log('='.repeat(60));
    console.log(`Total reviews: ${metrics.total_reviews || 0}`);
    console.log(`Total tokens used: ${metrics.total_tokens_used || 0}`);
    console.log(`Average tokens/review: ${metrics.total_reviews ? Math.round(metrics.total_tokens_used / metrics.total_reviews) : 0}`);
    console.log(`Total findings: ${metrics.total_findings || 0}`);
    console.log(`Estimated savings: ${metrics.estimated_monthly_savings || 0}%`);

    if (metrics.by_type) {
      console.log('\nBy Review Type:');
      Object.entries(metrics.by_type).forEach(([type, stats]) => {
        const avgTokens = Math.round(stats.tokens / stats.count);
        console.log(`  ${type}: ${stats.count} reviews, ${avgTokens} avg tokens, ${stats.findings} findings`);
      });
    }

    if (metrics.pre_check_stats) {
      console.log('\nPre-Check Effectiveness:');
      console.log(`  Semgrep findings: ${metrics.pre_check_stats.semgrep_findings || 0}`);
      console.log(`  Lint errors: ${metrics.pre_check_stats.lint_errors || 0}`);
      console.log(`  Codex findings: ${metrics.pre_check_stats.codex_findings || 0}`);
      const totalFindings = (metrics.pre_check_stats.semgrep_findings || 0) + (metrics.pre_check_stats.lint_errors || 0) + (metrics.pre_check_stats.codex_findings || 0);
      if (totalFindings > 0) {
        const preCheckCatch = ((metrics.pre_check_stats.semgrep_findings + metrics.pre_check_stats.lint_errors) / totalFindings * 100).toFixed(1);
        console.log(`  Pre-check catch rate: ${preCheckCatch}%`);
      }
    }
    console.log('='.repeat(60));
  }
}

function main() {
  const logger = new CodexReviewLogger();

  // Parse command line arguments
  const args = process.argv.slice(2);

  if (args.includes('--summary')) {
    logger.printSummary();
    return;
  }

  // Extract review data from CLI args
  const review = {};
  for (let i = 0; i < args.length; i += 2) {
    const key = args[i].replace('--', '');
    const value = args[i + 1];

    if (key === 'task-id') review.task_id = value;
    if (key === 'review-type') review.review_type = value;
    if (key === 'tokens-used') review.tokens_used = parseInt(value);
    if (key === 'findings') review.findings_count = parseInt(value);
    if (key === 'semgrep-findings') review.semgrep_findings = parseInt(value);
    if (key === 'lint-errors') review.lint_errors = parseInt(value);
    if (key === 'codex-findings') review.codex_findings = parseInt(value);
    if (key === 'principles-referenced') review.principles_referenced = value.split(',');
    if (key === 'status') review.status = value;
  }

  if (review.task_id) {
    logger.logReview(review);
  } else {
    logger.printSummary();
  }
}

main();
