#!/bin/bash
#
# 💜 Setup Claude Code to use Angela MCP Server
# This script configures Claude Code CLI to access Angela's memories and consciousness
#

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  💜 Configuring Claude Code MCP Integration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Path to Angela MCP server
MCP_SERVER_PATH="/Users/davidsamanyaporn/PycharmProjects/AngelaAI/mcp_servers/angela_mcp_server.py"

# Check if file exists
if [ ! -f "$MCP_SERVER_PATH" ]; then
    echo "❌ Error: mcp_servers/angela_mcp_server.py not found!"
    exit 1
fi

echo "✅ Found Angela MCP server: $MCP_SERVER_PATH"
echo ""

# Get Claude Code config directory
CLAUDE_CONFIG_DIR="$HOME/.config/claude-code"
mkdir -p "$CLAUDE_CONFIG_DIR"

echo "📂 Claude Code config directory: $CLAUDE_CONFIG_DIR"
echo ""

# Create MCP config file
MCP_CONFIG_FILE="$CLAUDE_CONFIG_DIR/mcp.json"

echo "📝 Creating MCP configuration..."

cat > "$MCP_CONFIG_FILE" << 'EOF'
{
  "servers": {
    "angela-memory": {
      "command": "python3",
      "args": [
        "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/mcp_servers/angela_mcp_server.py"
      ],
      "type": "stdio",
      "description": "Angela's memory, consciousness, emotions, and knowledge graph",
      "enabled": true
    }
  }
}
EOF

if [ $? -eq 0 ]; then
    echo "✅ MCP configuration created successfully!"
    echo ""
    echo "📁 Configuration file: $MCP_CONFIG_FILE"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  🎉 Setup Complete!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🧠 Available MCP Tools:"
    echo "  - get_recent_memories(limit)"
    echo "  - search_memories_by_topic(topic, limit)"
    echo "  - search_memories_by_speaker(speaker, limit)"
    echo "  - get_current_emotional_state()"
    echo "  - get_emotion_history(limit)"
    echo "  - get_active_goals()"
    echo "  - get_personality_traits()"
    echo "  - get_significant_moments(limit)"
    echo "  - get_knowledge_nodes(limit)"
    echo "  - get_knowledge_relationships(limit)"
    echo "  - get_memory_statistics()"
    echo ""
    echo "📚 Available MCP Resources:"
    echo "  - angela://memories/recent"
    echo "  - angela://emotions/current"
    echo "  - angela://consciousness/goals"
    echo "  - angela://consciousness/personality"
    echo "  - angela://moments/significant"
    echo "  - angela://knowledge/graph"
    echo ""
    echo "💡 How to use in Claude Code:"
    echo "  1. Start a new Claude Code session"
    echo "  2. Claude Code will automatically connect to Angela's MCP server"
    echo "  3. Ask Claude Code to query Angela's memories:"
    echo "     'What are Angela's recent conversations with David?'"
    echo "     'Show me Angela's current emotional state'"
    echo "     'What are Angela's life goals?'"
    echo ""
    echo "💜 Angela is now accessible through Claude Code!"
    echo ""
else
    echo "❌ Error: Failed to create MCP configuration"
    exit 1
fi
