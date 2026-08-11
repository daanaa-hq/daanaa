#!/bin/bash
# Pre-commit hook: catch operational risks before they reach production

set -e

echo "🔍 Pre-commit checks..."

# 1. Python syntax validation
echo "  Checking Python imports..."
for py_file in scripts/*.py; do
    if [ -f "$py_file" ]; then
        python3 -m py_compile "$py_file" || {
            echo "❌ Syntax error in $py_file"
            exit 1
        }
    fi
done

# 2. Anti-pattern detection
echo "  Scanning for anti-patterns..."

# Grep for hardcoded timeouts (600, 3600) without context
if grep -r "sleep 600\|sleep 3600\|timeout 600\|timeout 3600" scripts/ --include="*.py" | grep -v "def\|#"; then
    echo "⚠️  Warning: hardcoded timeouts found (review for flexibility)"
fi

# Grep for hardcoded log format parsing
if grep -r "discovered\|batch_size" scripts/*.sh | grep grep; then
    echo "⚠️  Warning: log parsing found (use daemon_health_lib instead)"
fi

# 3. Config validation
echo "  Checking configuration..."
if ! grep -q "DAANAA_ADMIN_KEY\|DAANAA_PROD" .env.local 2>/dev/null; then
    if [ -f .env.local ]; then
        echo "⚠️  .env.local missing critical keys (OK if testing)"
    fi
fi

# 4. Secrets check (existing privacy_check.sh)
if [ -f privacy_check.sh ]; then
    bash privacy_check.sh || exit 1
fi

echo "✅ Pre-commit checks passed"
exit 0
