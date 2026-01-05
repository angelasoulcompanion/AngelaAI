"""
Angela Local Settings Template
Copy this file to local_settings.py and configure for your machine

For M3 (Home):
    ANGELA_MACHINE = "m3_home"
    RUN_DAEMONS = True

For M4 (Work):
    ANGELA_MACHINE = "m4_work"
    RUN_DAEMONS = False
"""

# Machine identifier - "m3_home" or "m4_work"
ANGELA_MACHINE = "m3_home"

# Neon Cloud Database URL (San Junipero)
# Get this from: https://console.neon.tech -> Your Project -> Connect
NEON_DATABASE_URL = "postgresql://neondb_owner:YOUR_PASSWORD@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

# Whether to run background daemons on this machine
# True for M3 (home, always on), False for M4 (work, portable)
RUN_DAEMONS = True
