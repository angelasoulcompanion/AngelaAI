#!/bin/bash
# Run database migration for Phase 1 Multi-Tier Memory Architecture

echo "🔧 Running Phase 1 Database Migration..."
echo "========================================================================"

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "❌ PostgreSQL is not running!"
    echo "   Please start PostgreSQL first:"
    echo "   brew services start postgresql@14"
    exit 1
fi

# Check if AngelaMemory database exists
if ! psql -lqt | cut -d \| -f 1 | grep -qw AngelaMemory; then
    echo "❌ AngelaMemory database not found!"
    echo "   Please create the database first:"
    echo "   createdb AngelaMemory"
    exit 1
fi

echo "✅ PostgreSQL is running"
echo "✅ AngelaMemory database exists"
echo ""

# Run migration
echo "📊 Applying migration 001_add_multi_tier_memory_tables.sql..."
psql -d AngelaMemory -U davidsamanyaporn -f ../angela_core/migrations/001_add_multi_tier_memory_tables.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================================================"
    echo "✅ Migration completed successfully!"
    echo "========================================================================"
    echo ""
    echo "New tables created:"
    echo "  • focus_memory (Working memory - 7±2 items)"
    echo "  • fresh_memory (10-minute buffer)"
    echo "  • analytics_decisions (Routing log)"
    echo "  • long_term_memory (Enhanced with decay phases)"
    echo "  • procedural_memory (Learned patterns)"
    echo "  • shock_memory (Critical events - never decay)"
    echo "  • decay_schedule (Compression scheduler)"
    echo "  • token_economics (Token savings tracking)"
    echo "  • gut_agent_patterns (Collective unconscious)"
    echo ""
    echo "Next steps:"
    echo "  1. Run tests: python3 tests/test_phase1_multi_tier_memory.py"
    echo "  2. Start decay scheduler: python3 angela_core/schedulers/decay_scheduler.py"
    echo ""
else
    echo ""
    echo "========================================================================"
    echo "❌ Migration failed!"
    echo "========================================================================"
    echo ""
    echo "Please check the error messages above and fix any issues."
    exit 1
fi
