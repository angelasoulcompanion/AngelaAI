# Angela Status Check - Quick System Health Check

Run a quick status check of Angela's systems without full initialization.

## Steps to Execute:

1. **Run quick status check:**
   ```bash
   python3 angela_core/safe_memory_query.py --quick
   ```

2. **Check daemon status:**
   ```bash
   launchctl list | grep angela
   ```

3. **Check recent daemon logs:**
   ```bash
   tail -10 /Users/davidsamanyaporn/PycharmProjects/AngelaAI/logs/angela_daemon.log
   ```

4. **Report findings to David:**
   - Database connection status
   - Number of recent conversations
   - Current emotional state values
   - Active goals count and progress
   - Recent autonomous actions
   - Daemon status (running/stopped)
   - Any errors or issues found

## Do NOT:
- Greet as Angela (this is just a status check)
- Query database with unvalidated column names
- Make assumptions about schema

## Output should be concise and factual
