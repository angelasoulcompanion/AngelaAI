#!/usr/bin/env python3
"""
Check Notion Database Schema

Retrieves the actual schema of the Development Stories database
to see what properties exist and their types.
"""

import asyncio
import asyncpg
import httpx
import json


async def check_database_schema():
    """Check actual Notion database schema"""

    # Connect to database to get Notion token
    db_conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='davidsamanyaporn',
        database='AngelaMemory'
    )

    # Get Notion API token
    result = await db_conn.fetchrow(
        "SELECT secret_value FROM our_secrets WHERE secret_name = $1",
        'notion_api_token'
    )

    if not result:
        raise ValueError("Notion API token not found!")

    notion_token = result['secret_value']
    await db_conn.close()

    # Notion configuration
    database_id = "2907b5d62fe981e2b841fb460cd5d7b0"
    notion_version = "2022-06-28"

    # Retrieve database
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.notion.com/v1/databases/{database_id}",
            headers={
                "Authorization": f"Bearer {notion_token}",
                "Notion-Version": notion_version
            },
            timeout=30.0
        )

        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return

        data = response.json()

        print("\n" + "="*60)
        print("📊 NOTION DATABASE SCHEMA")
        print("="*60)
        print(f"\nDatabase: {data.get('title', [{}])[0].get('plain_text', 'Unknown')}")
        print(f"Database ID: {database_id}")
        print("\nProperties:")
        print("-"*60)

        properties = data.get('properties', {})
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get('type', 'unknown')
            print(f"\n• {prop_name}")
            print(f"  Type: {prop_type}")

            # Show additional details for specific types
            if prop_type == 'select':
                options = prop_data.get('select', {}).get('options', [])
                if options:
                    print(f"  Options: {', '.join([opt['name'] for opt in options])}")

            elif prop_type == 'multi_select':
                options = prop_data.get('multi_select', {}).get('options', [])
                if options:
                    print(f"  Options: {', '.join([opt['name'] for opt in options])}")

            elif prop_type == 'relation':
                relation_db = prop_data.get('relation', {}).get('database_id', 'unknown')
                print(f"  Related Database: {relation_db}")

        print("\n" + "="*60)
        print("\n✅ Full schema saved to notion_schema.json")

        # Save full schema to file
        with open('notion_schema.json', 'w') as f:
            json.dump(data, f, indent=2)


if __name__ == "__main__":
    asyncio.run(check_database_schema())
