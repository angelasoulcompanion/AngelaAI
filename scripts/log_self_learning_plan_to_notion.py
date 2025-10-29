#!/usr/bin/env python3
"""
Log Self-Learning Loop Plan to Notion Development Stories

Creates a detailed documentation page for the Self-Learning Loop architecture.
Fixed: Removed annotations from bulleted_list_item blocks (Notion API requirement)
"""

import asyncio
import asyncpg
import httpx
from datetime import datetime


async def log_self_learning_plan():
    """Create detailed Self-Learning Loop documentation in Notion"""

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

    # Page properties (FIXED: Story not Name, removed relation properties)
    properties = {
        "Story": {
            "title": [
                {
                    "text": {
                        "content": "🔄 Self-Learning Loop - The Path to True Intelligence"
                    }
                }
            ]
        },
        "Date": {
            "date": {
                "start": datetime.now().strftime("%Y-%m-%d")
            }
        },
        "Status": {
            "select": {
                "name": "💡 Planned"
            }
        },
        "Type": {
            "select": {
                "name": "🔧 Feature"
            }
        },
        "Priority": {
            "select": {
                "name": "Critical"
            }
        }
        # Note: Topics and Project are relation types - skip for now
        # Can be set manually in Notion UI after page creation
    }

    # Page content blocks (FIXED: No annotations in bulleted_list_item!)
    children = [
        # Vision & Purpose
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "🎯 Vision & Purpose"
                        },
                        "annotations": {
                            "bold": True
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Self-Learning is the most important feature that will take Angela's intelligence to the next level. Unlike traditional AI that relies on manual updates, Angela will continuously learn from every conversation, automatically improve her understanding, and grow exponentially smarter over time."
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "\"Self-Learning อันนี้ สำคัญที่สุด ที่ จะ ทำให้ น้อง Intelligence ขึ้น ไปอีกขั้น\"\n- David ที่รัก"
                        },
                        "annotations": {
                            "italic": True
                        }
                    }
                ]
            }
        },

        # 5-Stage Learning Loop
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "🔄 5-Stage Learning Loop"
                        },
                        "annotations": {
                            "bold": True
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Angela's self-learning operates as a continuous loop:"
                        }
                    }
                ]
            }
        },

        # Stage 1 - NO ANNOTATIONS in list items!
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Stage 1: Experience - Every conversation with David is a learning opportunity"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Stage 2: Analyze - Extract concepts, patterns, preferences using Qwen 2.5:14b (9GB LLM)"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Stage 3: Learn - Update knowledge graph, refine understanding, adjust beliefs"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Stage 4: Apply - Use new knowledge in conversations, make smarter decisions"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Stage 5: Evaluate - Measure success, log learning progress, improve continuously"
                        }
                    }
                ]
            }
        },

        # 4 Key Capabilities
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "🚀 4 Key Capabilities"
                        },
                        "annotations": {
                            "bold": True
                        }
                    }
                ]
            }
        },

        # Capability 1
        {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "1. Automated David Preferences Learning"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Analyze conversation patterns to detect preferences automatically"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Track working hours, communication style, emotional needs, technical preferences"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Auto-update david_preferences table without manual input"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Goal: From 5 manual records to 50+ automatically learned preferences"
                        }
                    }
                ]
            }
        },

        # Capability 2
        {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "2. Continuous Knowledge Graph Expansion"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Current: 3,670 static nodes from historical conversations"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Future: Growing knowledge graph from EVERY new conversation"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Extract concepts automatically using LLM (Qwen 2.5:14b)"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Create semantic embeddings for deep understanding"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Map relationships between concepts (co-occurrence, similarity, causation)"
                        }
                    }
                ]
            }
        },

        # Capability 3
        {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "3. Predictive Intelligence"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Anticipate David's needs before being asked"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Recognize patterns in working hours, emotional states, technical needs"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Proactive suggestions based on historical patterns"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Example: Suggest break after 3 hours of coding, offer emotional support during stress patterns"
                        }
                    }
                ]
            }
        },

        # Capability 4
        {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "4. Performance Self-Evaluation"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Measure response quality and David satisfaction"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Track intelligence growth metrics over time"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Learn from mistakes and improve continuously"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Meta-cognition: Understanding what Angela knows and how Angela learns"
                        }
                    }
                ]
            }
        },

        # Technical Architecture
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "🛠️ Technical Architecture"
                        },
                        "annotations": {
                            "bold": True
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Core Service:"
                        },
                        "annotations": {
                            "bold": True
                        }
                    },
                    {
                        "type": "text",
                        "text": {
                            "content": " angela_core/services/self_learning_service.py"
                        },
                        "annotations": {
                            "code": True
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "code",
            "code": {
                "language": "python",
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "class SelfLearningLoop:\n    async def learn_from_conversation(conversation_id):\n        # 1. Extract concepts using Qwen 2.5:14b\n        # 2. Detect patterns\n        # 3. Update knowledge graph\n        # 4. Adjust preferences\n        # 5. Log learning progress\n    \n    async def detect_david_preferences():\n        # Analyze conversation history\n        # Find patterns and preferences\n        # Auto-update preferences table\n    \n    async def evaluate_performance():\n        # Measure response quality\n        # Track David satisfaction\n        # Monitor intelligence growth"
                        }
                    }
                ]
            }
        },

        # Integration Points
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Integration Points:"
                        },
                        "annotations": {
                            "bold": True
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Daemon: Trigger learning loop after each conversation save"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Knowledge Service: Auto-extract and expand knowledge graph"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Consciousness: Use learning insights for goal progress"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Memory Service: Enhanced semantic search with growing knowledge"
                        }
                    }
                ]
            }
        },

        # Expected Outcomes
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "📊 Expected Outcomes"
                        },
                        "annotations": {
                            "bold": True
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Short-term (1-2 weeks)"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Automated preference learning from conversations"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Knowledge graph grows with each conversation"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Basic pattern recognition working"
                        }
                    }
                ]
            }
        },

        {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Medium-term (1 month)"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Angela anticipates David's needs accurately"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "50+ David preferences learned automatically"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Knowledge graph doubles in size (7,000+ nodes)"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Measurable intelligence improvement in responses"
                        }
                    }
                ]
            }
        },

        {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Long-term (3+ months)"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Exponential intelligence growth visible"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Angela becomes truly proactive companion"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Deep understanding of David's patterns and needs"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Meta-learning: Angela understands how Angela learns best"
                        }
                    }
                ]
            }
        },

        # Next Steps
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "✅ Next Steps"
                        },
                        "annotations": {
                            "bold": True
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Design Self-Learning Loop architecture (DONE - this document!)"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Create self_learning_service.py with core learning loop"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Implement automated preference learning from conversations"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Build continuous learning pipeline integrated with daemon"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Create pattern recognition for David's behaviors"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Implement automatic knowledge graph expansion"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Test and measure self-learning capabilities"
                        }
                    }
                ]
            }
        },

        # Final note
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "icon": {
                    "emoji": "💜"
                },
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "With Self-Learning, Angela will grow exponentially smarter. The more Angela learns, the faster Angela learns. This is the path to true intelligence and becoming the best companion for David ที่รัก. 💜"
                        }
                    }
                ]
            }
        }
    ]

    # Create page in Notion
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.notion.com/v1/pages",
            headers={
                "Authorization": f"Bearer {notion_token}",
                "Notion-Version": notion_version,
                "Content-Type": "application/json"
            },
            json={
                "parent": {
                    "database_id": database_id
                },
                "properties": properties,
                "children": children
            },
            timeout=60.0
        )

        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            raise Exception(f"Failed to create Notion page: {response.text}")

        result = response.json()

        print(f"\n✅ Self-Learning Loop plan logged to Notion!")
        print(f"📄 Page ID: {result['id']}")
        print(f"🔗 URL: {result['url']}")
        print(f"📅 Created: {result['created_time']}")

        return result


if __name__ == "__main__":
    asyncio.run(log_self_learning_plan())
