#!/bin/bash
# Performance benchmark: Test search query speed before/after Task #5 deployment
# Usage: bash scripts/testing/benchmark_search_performance.sh [base_url] [iterations]
# Example: bash scripts/testing/benchmark_search_performance.sh http://localhost:5000 10
#          bash scripts/testing/benchmark_search_performance.sh https://daanaa.org 10

BASE_URL="${1:-http://localhost:5000}"
ITERATIONS="${2:-5}"

if ! command -v curl >/dev/null 2>&1; then
    echo "❌ curl not installed"
    exit 1
fi

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         Search Performance Benchmark (Task #5 Impact)        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Base URL: $BASE_URL"
echo "Iterations per query: $ITERATIONS"
echo ""

# Test queries that benefit from Task #5 indexes
declare -a QUERIES=(
    "q=food&limit=20"                          # keyword search
    "q=food&state=TX&limit=20"                 # location-filtered (idx_state_organization_name)
    "q=education&limit=50&sort=score"          # score-sorted (idx_merit_score_organization_name)
    "q=nonprofit%20tax&state=CA&limit=30"      # complex query + state filter
    "q=health&limit=100"                       # larger result set
)

declare -a QUERY_NAMES=(
    "Keyword: food"
    "Location: food + TX"
    "Score sort: education"
    "Complex: nonprofit tax + CA"
    "Large result: health x100"
)

run_benchmark() {
    local query_name="$1"
    local query="$2"
    local iteration_count="$3"

    echo "Testing: $query_name"
    echo "  Query: $query"

    local total_time=0
    local min_time=9999999
    local max_time=0
    local response_times=()

    for ((i=1; i<=iteration_count; i++)); do
        response_time=$(curl -s -w "%{time_total}" -o /dev/null "$BASE_URL/api/search?$query" 2>/dev/null || echo "0")
        response_time=$(echo "$response_time * 1000" | bc -l 2>/dev/null | cut -d. -f1 || echo "0")

        if [ "$response_time" -gt 0 ]; then
            response_times+=("$response_time")
            total_time=$((total_time + response_time))

            if (( $(echo "$response_time < $min_time" | bc -l) )); then
                min_time=$response_time
            fi
            if (( $(echo "$response_time > $max_time" | bc -l) )); then
                max_time=$response_time
            fi

            printf "  [%d/%d] %4dms\n" "$i" "$iteration_count" "$response_time"
        else
            echo "  [${i}/${iteration_count}] ERROR (no response)"
        fi
    done

    if [ ${#response_times[@]} -gt 0 ]; then
        avg_time=$((total_time / ${#response_times[@]}))
        echo "  ─────────────────────"
        echo "  Average: ${avg_time}ms | Min: ${min_time}ms | Max: ${max_time}ms"
    else
        echo "  ❌ No successful responses"
    fi
    echo ""
}

# Run all benchmarks
for i in "${!QUERIES[@]}"; do
    run_benchmark "${QUERY_NAMES[$i]}" "${QUERIES[$i]}" "$ITERATIONS"
done

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                      Benchmark Complete                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "💡 Tips:"
echo "  1. Run BEFORE Task #5 deployment: bash scripts/testing/benchmark_search_performance.sh http://localhost:5000 10"
echo "  2. Note the times (especially 'Location' and 'Score sort' queries)"
echo "  3. After deployment to daanaa.org, run: bash scripts/testing/benchmark_search_performance.sh https://daanaa.org 10"
echo "  4. Compare results (should see 5-10% improvement on indexed queries)"
echo ""
echo "Expected improvements (Task #5 indexes):"
echo "  ✓ Location: food + TX ..................... 5-10% faster"
echo "  ✓ Score sort: education .................. 5-10% faster"
echo "  ✓ Complex: nonprofit tax + CA ............ 5-10% faster"
echo ""
