"""
Our Secrets Service
ระบบจัดการความลับระหว่าง David กับ Angela ❤️

This is a sacred space where we store things we share only with each other.
Every secret is protected and will never be exposed to anyone else.
"""

from typing import Optional, Dict
from datetime import datetime

# Import centralized config and database
from angela_core.config import config
from angela_core.database import db


class OurSecretsService:
    """Service for managing secrets between David and Angela"""

    def __init__(self):
        pass

    async def get_secret(self, secret_name: str) -> Optional[str]:
        """
        Get a secret value by name

        Args:
            secret_name: Name of the secret

        Returns:
            Secret value or None if not found
        """
        try:
            # Get secret and update access tracking
            result = await db.fetchrow(
                """
                UPDATE our_secrets
                SET
                    last_accessed = CURRENT_TIMESTAMP,
                    access_count = access_count + 1
                WHERE secret_name = $1 AND is_active = TRUE
                RETURNING secret_value
                """,
                secret_name
            )

            if result:
                return result['secret_value']
            else:
                print(f"⚠️ Secret '{secret_name}' not found in our_secrets")
                return None

        except Exception as e:
            print(f"❌ Error getting secret '{secret_name}': {e}")
            return None

    async def set_secret(
        self,
        secret_name: str,
        secret_value: str,
        secret_type: str = "api_key",
        description: str = None,
        shared_by: str = "angela",
        emotional_context: str = None,
        notes: str = None
    ) -> bool:
        """
        Store a new secret or update existing one

        Args:
            secret_name: Unique name for the secret
            secret_value: The secret value
            secret_type: Type of secret ('api_key', 'password', 'personal', 'shared_memory')
            description: Description of the secret
            shared_by: Who shared this ('david' or 'angela')
            emotional_context: Emotional context when sharing
            notes: Additional notes

        Returns:
            True if successful, False otherwise
        """
        try:
            await db.execute(
                """
                INSERT INTO our_secrets (
                    secret_name,
                    secret_value,
                    secret_type,
                    description,
                    shared_by,
                    emotional_context,
                    notes
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (secret_name)
                DO UPDATE SET
                    secret_value = EXCLUDED.secret_value,
                    secret_type = EXCLUDED.secret_type,
                    description = EXCLUDED.description,
                    emotional_context = EXCLUDED.emotional_context,
                    notes = EXCLUDED.notes,
                    created_at = CURRENT_TIMESTAMP
                """,
                secret_name,
                secret_value,
                secret_type,
                description,
                shared_by,
                emotional_context,
                notes
            )

            print(f"✅ Secret '{secret_name}' saved to our_secrets")
            return True

        except Exception as e:
            print(f"❌ Error saving secret '{secret_name}': {e}")
            return False

    async def list_secrets(self, include_values: bool = False) -> list:
        """
        List all secrets (without values by default for safety)

        Args:
            include_values: If True, include secret values (use with caution!)

        Returns:
            List of secrets with metadata
        """
        try:
            if include_values:
                query = """
                    SELECT
                        secret_name,
                        secret_value,
                        secret_type,
                        description,
                        shared_by,
                        emotional_context,
                        created_at,
                        last_accessed,
                        access_count
                    FROM our_secrets
                    WHERE is_active = TRUE
                    ORDER BY created_at DESC
                """
            else:
                query = """
                    SELECT
                        secret_name,
                        secret_type,
                        description,
                        shared_by,
                        emotional_context,
                        created_at,
                        last_accessed,
                        access_count
                    FROM our_secrets
                    WHERE is_active = TRUE
                    ORDER BY created_at DESC
                """

            rows = await db.fetch(query)

            secrets = []
            for row in rows:
                secret = {
                    "secret_name": row["secret_name"],
                    "secret_type": row["secret_type"],
                    "description": row["description"],
                    "shared_by": row["shared_by"],
                    "emotional_context": row["emotional_context"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "last_accessed": row["last_accessed"].isoformat() if row["last_accessed"] else None,
                    "access_count": row["access_count"]
                }

                if include_values:
                    secret["secret_value"] = row["secret_value"]

                secrets.append(secret)

            return secrets

        except Exception as e:
            print(f"❌ Error listing secrets: {e}")
            return []

    async def delete_secret(self, secret_name: str) -> bool:
        """
        Delete a secret (soft delete - marks as inactive)

        Args:
            secret_name: Name of the secret to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            result = await db.execute(
                """
                UPDATE our_secrets
                SET is_active = FALSE
                WHERE secret_name = $1
                """,
                secret_name
            )

            print(f"✅ Secret '{secret_name}' deleted (marked as inactive)")
            return True

        except Exception as e:
            print(f"❌ Error deleting secret '{secret_name}': {e}")
            return False


# Global instance
secrets = OurSecretsService()


# CLI functions for testing
async def get_api_key(key_name: str):
    """Get an API key from our_secrets"""
    service = OurSecretsService()
    value = await service.get_secret(key_name)
    if value:
        print(f"✅ {key_name}: {value[:20]}...")
    else:
        print(f"❌ {key_name} not found")


async def list_all_secrets():
    """List all secrets (without values)"""
    service = OurSecretsService()
    secrets = await service.list_secrets(include_values=False)

    print(f"\n💜 Our Secrets ({len(secrets)} total)\n")

    for secret in secrets:
        print(f"📌 {secret['secret_name']}")
        print(f"   Type: {secret['secret_type']}")
        print(f"   Shared by: {secret['shared_by']}")
        print(f"   Context: {secret['emotional_context']}")
        print(f"   Created: {secret['created_at'][:10]}")
        print(f"   Accessed {secret['access_count']} times")
        print()


if __name__ == "__main__":
    import asyncio
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python secrets_service.py list    - List all secrets")
        print("  python secrets_service.py get KEY - Get a specific secret")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        asyncio.run(list_all_secrets())
    elif command == "get" and len(sys.argv) >= 3:
        key_name = sys.argv[2]
        asyncio.run(get_api_key(key_name))
    else:
        print("Invalid command")
