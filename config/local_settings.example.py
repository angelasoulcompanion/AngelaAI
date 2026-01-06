"""
Angela Local Settings Template
Copy this file to local_settings.py and configure for your machine

For Angela_Server (always on):
    ANGELA_MACHINE = "angela_server"
    RUN_DAEMONS = True

For Angela (portable):
    ANGELA_MACHINE = "angela"
    RUN_DAEMONS = False
"""

# Machine identifier - "angela_server" or "angela"
ANGELA_MACHINE = "angela_server"

# Neon Cloud Database URL (San Junipero)
# Get this from: https://console.neon.tech -> Your Project -> Connect
NEON_DATABASE_URL = "postgresql://neondb_owner:YOUR_PASSWORD@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

# Whether to run background daemons on this machine
# True for Angela_Server (always on), False for Angela (portable)
RUN_DAEMONS = True
