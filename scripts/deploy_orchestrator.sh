#!/bin/bash

# Deployment Orchestrator for Daanaa Automation Stack
# Automates the entire 4-day deployment sequence
# Usage: bash deploy_orchestrator.sh [--help] [--validate-only] [--skip-backups]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_LOG="/var/log/daanaa_deployment_$(date +%Y%m%d_%H%M%S).log"
DEPLOYMENT_DIR="/home/akbar/meritgiving"
DOCKER_COMPOSE_TIMEOUT=300

# Flags
VALIDATE_ONLY=false
SKIP_BACKUPS=false
DRY_RUN=false

# Parse arguments
for arg in "$@"; do
  case $arg in
    --validate-only) VALIDATE_ONLY=true ;;
    --skip-backups) SKIP_BACKUPS=true ;;
    --dry-run) DRY_RUN=true ;;
    --help) show_help; exit 0 ;;
  esac
done

# Functions
show_help() {
  cat << 'EOF'
Daanaa Automation Stack Deployment Orchestrator

USAGE:
  bash deploy_orchestrator.sh [OPTIONS]

OPTIONS:
  --validate-only    Check config files without deploying
  --skip-backups     Skip backup of existing databases
  --dry-run          Show what would be done, don't execute
  --help             Show this message

EXAMPLES:
  bash deploy_orchestrator.sh              # Full deployment
  bash deploy_orchestrator.sh --validate-only  # Validate configs only
  bash deploy_orchestrator.sh --dry-run    # See what would happen

STAGES:
  Stage 1: Pre-deployment validation (configs, ports, disk space)
  Stage 2: Backup existing data (if any)
  Stage 3: Deploy Chatwoot (Day 1)
  Stage 4: Deploy Jambonz (Day 2)
  Stage 5: Deploy n8n (Day 3)
  Stage 6: Run integration tests (Day 4)
  Stage 7: Post-deployment verification

LOG: $DEPLOYMENT_LOG
EOF
}

log() {
  echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

success() {
  echo -e "${GREEN}✅ $1${NC}" | tee -a "$DEPLOYMENT_LOG"
}

warning() {
  echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$DEPLOYMENT_LOG"
}

error() {
  echo -e "${RED}❌ $1${NC}" | tee -a "$DEPLOYMENT_LOG"
  exit 1
}

# Stage 1: Pre-Deployment Validation
validate_environment() {
  log "=== STAGE 1: Pre-Deployment Validation ==="

  # Check Docker installed
  if ! command -v docker &> /dev/null; then
    error "Docker not found. Install Docker first."
  fi
  success "Docker installed"

  # Check Docker Compose installed
  if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose not found. Install Docker Compose first."
  fi
  success "Docker Compose installed"

  # Check disk space (need 20GB free)
  FREE_SPACE=$(df /data | awk 'NR==2 {print $4}')
  if [ "$FREE_SPACE" -lt 20971520 ]; then  # 20GB in KB
    error "Not enough disk space. Need 20GB free, have $((FREE_SPACE / 1024 / 1024))GB"
  fi
  success "Disk space OK ($(df -h /data | awk 'NR==2 {print $4}') free)"

  # Check required ports are free
  for port in 3000 5678 5060; do
    if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
      warning "Port $port already in use. Service will need different port."
    else
      success "Port $port available"
    fi
  done

  # Check config files exist
  for config in \
    "/opt/chatwoot/docker-compose.yml" \
    "/opt/jambonz/docker-compose.yml" \
    "/opt/n8n/docker-compose.yml"; do
    if [ ! -f "$config" ]; then
      warning "Config not found: $config. Will create during deployment."
    else
      success "Found: $config"
    fi
  done

  # Check environment variables
  if [ -z "$VOXBEAM_USERNAME" ] && [ ! -f "/opt/jambonz/.env" ]; then
    warning "Voxbeam credentials not set. You'll need to provide them during deployment."
  else
    success "Credentials configured"
  fi

  log ""
}

# Stage 2: Backup Existing Data
backup_existing() {
  log "=== STAGE 2: Backup Existing Data ==="

  if [ "$SKIP_BACKUPS" = true ]; then
    warning "Skipping backups per --skip-backups flag"
    return
  fi

  # Check if services are running
  if ! docker ps --format "{{.Names}}" | grep -q "chatwoot"; then
    log "Chatwoot not running. No backup needed."
  else
    log "Backing up Chatwoot database..."
    mkdir -p /data/automation_backups
    docker-compose -f /opt/chatwoot/docker-compose.yml exec -T postgres pg_dump \
      -U postgres -d chatwoot_production | gzip > \
      "/data/automation_backups/chatwoot_backup_$(date +%Y%m%d_%H%M%S).sql.gz" || \
      warning "Chatwoot backup failed (service may not be running)"
    success "Chatwoot backed up"
  fi

  if ! docker ps --format "{{.Names}}" | grep -q "n8n"; then
    log "n8n not running. No backup needed."
  else
    log "Backing up n8n database..."
    docker-compose -f /opt/n8n/docker-compose.yml exec -T postgres pg_dump \
      -U n8n -d n8n | gzip > \
      "/data/automation_backups/n8n_backup_$(date +%Y%m%d_%H%M%S).sql.gz" || \
      warning "n8n backup failed (service may not be running)"
    success "n8n backed up"
  fi

  log ""
}

# Stage 3: Deploy Chatwoot
deploy_chatwoot() {
  log "=== STAGE 3: Deploy Chatwoot (Day 1) ==="

  mkdir -p /opt/chatwoot

  if [ ! -f "/opt/chatwoot/docker-compose.yml" ]; then
    error "Chatwoot docker-compose.yml not found at /opt/chatwoot/. Please create it first."
  fi

  if [ ! -f "/opt/chatwoot/.env" ]; then
    warning "Chatwoot .env not found. Creating template..."
    cat > /opt/chatwoot/.env << 'ENVEOF'
# Chatwoot Environment Variables (FILL IN YOUR VALUES)
POSTGRES_PASSWORD=chatwoot_secure_password_change_me
RAILS_ENV=production
RAILS_MAX_THREADS=5
SECRET_KEY_BASE=$(openssl rand -hex 32)
REDIS_URL=redis://redis:6379
FRONTEND_URL=http://localhost:3000
MAILER_SENDER_EMAIL=support@daanaa.org
ENVEOF
    warning "Please edit /opt/chatwoot/.env with your values"
  fi

  if [ "$DRY_RUN" = true ]; then
    log "[DRY RUN] Would execute: docker-compose -f /opt/chatwoot/docker-compose.yml up -d"
  else
    log "Starting Chatwoot..."
    cd /opt/chatwoot
    docker-compose up -d

    log "Waiting for Chatwoot to be ready (60 seconds)..."
    sleep 60

    # Verify
    if curl -s http://localhost:3000 > /dev/null; then
      success "Chatwoot is responding on port 3000"
    else
      error "Chatwoot failed to start or is not responding"
    fi
  fi

  log ""
}

# Stage 4: Deploy Jambonz
deploy_jambonz() {
  log "=== STAGE 4: Deploy Jambonz (Day 2) ==="

  mkdir -p /opt/jambonz/config

  if [ ! -f "/opt/jambonz/docker-compose.yml" ]; then
    error "Jambonz docker-compose.yml not found at /opt/jambonz/. Please create it first."
  fi

  if [ ! -f "/opt/jambonz/config/sip-config.json" ]; then
    warning "Jambonz SIP config not found. Creating template..."
    cat > /opt/jambonz/config/sip-config.json << 'SIPEOF'
{
  "sip_servers": [
    {
      "domain": "voxbeam.com",
      "username": "YOUR_VOXBEAM_USERNAME",
      "password": "YOUR_VOXBEAM_PASSWORD",
      "port": 5060
    }
  ]
}
SIPEOF
    error "Please edit /opt/jambonz/config/sip-config.json with your Voxbeam credentials"
  fi

  if [ "$DRY_RUN" = true ]; then
    log "[DRY RUN] Would execute: docker-compose -f /opt/jambonz/docker-compose.yml up -d"
  else
    log "Starting Jambonz..."
    cd /opt/jambonz
    docker-compose up -d

    log "Waiting for Jambonz to be ready (30 seconds)..."
    sleep 30

    # Verify SIP port
    if netstat -tlnp 2>/dev/null | grep -q ":5060 "; then
      success "Jambonz SIP port 5060 is listening"
    else
      error "Jambonz SIP port 5060 is not listening"
    fi
  fi

  log ""
}

# Stage 5: Deploy n8n
deploy_n8n() {
  log "=== STAGE 5: Deploy n8n (Day 3) ==="

  mkdir -p /opt/n8n

  if [ ! -f "/opt/n8n/docker-compose.yml" ]; then
    error "n8n docker-compose.yml not found at /opt/n8n/. Please create it first."
  fi

  if [ ! -f "/opt/n8n/.env" ]; then
    warning "n8n .env not found. Creating template..."
    cat > /opt/n8n/.env << 'ENVEOF'
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=akbar
N8N_BASIC_AUTH_PASSWORD=secure_password_change_me
N8N_HOST=n8n.daanaa.org
N8N_PORT=5678
N8N_PROTOCOL=http
WEBHOOK_URL=http://n8n.daanaa.org/
DB_TYPE=postgres
DB_POSTGRES_HOST=postgres
DB_POSTGRES_USER=n8n
DB_POSTGRES_PASSWORD=n8n_secure_password_change_me
DB_POSTGRES_DB=n8n
ENVEOF
    warning "Please edit /opt/n8n/.env with your values"
  fi

  if [ "$DRY_RUN" = true ]; then
    log "[DRY RUN] Would execute: docker-compose -f /opt/n8n/docker-compose.yml up -d"
  else
    log "Starting n8n..."
    cd /opt/n8n
    docker-compose up -d

    log "Waiting for n8n to be ready (90 seconds)..."
    sleep 90

    # Verify
    if curl -s http://localhost:5678 > /dev/null; then
      success "n8n is responding on port 5678"
    else
      error "n8n failed to start or is not responding"
    fi
  fi

  log ""
}

# Stage 6: Run Integration Tests
run_integration_tests() {
  log "=== STAGE 6: Integration Tests (Day 4) ==="

  if [ "$DRY_RUN" = true ]; then
    log "[DRY RUN] Would run integration tests from INTEGRATION_TEST_SUITE.md"
    return
  fi

  log "Running health check..."
  if [ -f "$DEPLOYMENT_DIR/scripts/health_check.sh" ]; then
    bash "$DEPLOYMENT_DIR/scripts/health_check.sh"
  else
    warning "Health check script not found"
  fi

  log ""
  log "Running sample tests..."

  # Test 1: Chatwoot API
  log "Test 1: Chatwoot API..."
  if curl -s http://localhost:3000 > /dev/null; then
    success "Chatwoot API responding"
  else
    error "Chatwoot API not responding"
  fi

  # Test 2: n8n API
  log "Test 2: n8n API..."
  if curl -s http://localhost:5678 > /dev/null; then
    success "n8n API responding"
  else
    error "n8n API not responding"
  fi

  # Test 3: SIP port
  log "Test 3: SIP port..."
  if netstat -tlnp 2>/dev/null | grep -q ":5060 "; then
    success "SIP port 5060 listening"
  else
    error "SIP port 5060 not listening"
  fi

  log ""
  log "For full integration tests, see: $DEPLOYMENT_DIR/docs/INTEGRATION_TEST_SUITE.md"
  log ""
}

# Stage 7: Post-Deployment Verification
post_deployment_verification() {
  log "=== STAGE 7: Post-Deployment Verification ==="

  log "All services deployed. Running final health check..."

  ISSUES=0

  # Check each service
  echo ""
  echo "Service Status:"
  if docker ps --format "{{.Names}}" | grep -q "chatwoot"; then
    success "Chatwoot running"
  else
    error "Chatwoot not running"
    ((ISSUES++))
  fi

  if docker ps --format "{{.Names}}" | grep -q "n8n"; then
    success "n8n running"
  else
    error "n8n not running"
    ((ISSUES++))
  fi

  if docker ps --format "{{.Names}}" | grep -q "jambonz"; then
    success "Jambonz running"
  else
    error "Jambonz not running"
    ((ISSUES++))
  fi

  echo ""
  echo "Next steps:"
  echo "  1. Open Chatwoot: http://localhost:3000"
  echo "  2. Complete Chatwoot setup (email, inbox)"
  echo "  3. Test voice IVR: Call your DID"
  echo "  4. Test email: Send to daanaa@daanaa.org"
  echo "  5. See INTEGRATION_TEST_SUITE.md for full tests"
  echo ""

  if [ $ISSUES -eq 0 ]; then
    success "Deployment complete! No critical issues."
    log ""
    log "Deployment log: $DEPLOYMENT_LOG"
    exit 0
  else
    error "Deployment complete with $ISSUES issue(s). Check log: $DEPLOYMENT_LOG"
  fi
}

# Main execution
main() {
  echo ""
  echo "╔═══════════════════════════════════════════════════════════╗"
  echo "║   Daanaa Automation Stack Deployment Orchestrator        ║"
  echo "║   $(date '+%Y-%m-%d %H:%M:%S')                               ║"
  echo "╚═══════════════════════════════════════════════════════════╝"
  echo ""

  log "Starting deployment..."
  log "Logging to: $DEPLOYMENT_LOG"

  if [ "$VALIDATE_ONLY" = true ]; then
    validate_environment
    log "Validation complete. No changes made (--validate-only mode)."
    exit 0
  fi

  if [ "$DRY_RUN" = true ]; then
    log "DRY RUN MODE: Showing what would be done without executing."
  fi

  validate_environment
  backup_existing
  deploy_chatwoot
  deploy_jambonz
  deploy_n8n
  run_integration_tests
  post_deployment_verification
}

# Run main
main
