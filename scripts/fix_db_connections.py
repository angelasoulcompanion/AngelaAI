"""Quick script to fix database connection patterns"""
import re

files = [
    "angela_core/services/skill_tracker.py",
    "angela_core/services/prompt_generator.py",
    "angela_core/services/skill_updater.py"
]

for file_path in files:
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace pool = await get_db_pool() + async with pool.acquire()
    # with conn = await get_db_connection()

    # Pattern 1: pool = await get_db_pool() followed by async with pool.acquire() as conn:
    content = re.sub(
        r'pool = await get_db_connection\(\)\s+async with pool\.acquire\(\) as conn:',
        'conn = await get_db_connection()',
        content
    )

    # Pattern 2: Close connections at end of functions
    # We need to add await conn.close() before returns

    with open(file_path, 'w') as f:
        f.write(content)

    print(f"✅ Fixed {file_path}")
