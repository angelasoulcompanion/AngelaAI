#!/bin/bash
#
# 💜 Angela Telegram Bot - One-Click Setup Script
# สำหรับติดตั้งบน MacBook Pro M3 ที่บ้าน
#
# Usage: ./setup.sh
#

set -e

echo "╔══════════════════════════════════════════════════════╗"
echo "║  💜 ANGELA TELEGRAM BOT - SETUP SCRIPT              ║"
echo "║     @AngelaSoulBot Auto-Reply Service               ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTALL_DIR="$HOME/angela-telegram"

echo -e "${YELLOW}📍 Installation directory: $INSTALL_DIR${NC}"
echo ""

# ============================================
# Step 1: Check and Install Homebrew
# ============================================
echo "🍺 Step 1: Checking Homebrew..."
if ! command -v brew &> /dev/null; then
    echo "   Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add to PATH for Apple Silicon
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo -e "   ${GREEN}✅ Homebrew already installed${NC}"
fi

# ============================================
# Step 2: Install PostgreSQL
# ============================================
echo ""
echo "🐘 Step 2: Installing PostgreSQL..."
if ! command -v psql &> /dev/null; then
    brew install postgresql@15
    brew services start postgresql@15
    echo "   Waiting for PostgreSQL to start..."
    sleep 3
else
    echo -e "   ${GREEN}✅ PostgreSQL already installed${NC}"
    brew services start postgresql@15 2>/dev/null || true
fi

# ============================================
# Step 3: Install Python packages
# ============================================
echo ""
echo "🐍 Step 3: Installing Python packages..."
pip3 install asyncpg httpx --quiet
echo -e "   ${GREEN}✅ Python packages installed${NC}"

# ============================================
# Step 4: Create installation directory
# ============================================
echo ""
echo "📁 Step 4: Creating installation directory..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/logs"

# Copy files
cp "$SCRIPT_DIR/database.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/telegram_service.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/telegram_responder.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/telegram_daemon.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"

echo -e "   ${GREEN}✅ Files copied to $INSTALL_DIR${NC}"

# ============================================
# Step 5: Setup Database
# ============================================
echo ""
echo "🗄️ Step 5: Setting up database..."

# Get current username
DB_USER=$(whoami)

# Create database if not exists
createdb AngelaMemory 2>/dev/null || echo "   Database already exists"

# Create tables
psql -d AngelaMemory -c "
-- Telegram messages table
CREATE TABLE IF NOT EXISTS telegram_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_update_id BIGINT UNIQUE,
    telegram_message_id BIGINT,
    chat_id BIGINT,
    from_id BIGINT,
    from_name VARCHAR(100),
    message_text TEXT,
    is_command BOOLEAN DEFAULT FALSE,
    command VARCHAR(50),
    angela_response TEXT,
    responded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Secrets table
CREATE TABLE IF NOT EXISTS our_secrets (
    secret_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    secret_name VARCHAR(100) UNIQUE NOT NULL,
    secret_value TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_telegram_messages_update ON telegram_messages(telegram_update_id);
CREATE INDEX IF NOT EXISTS idx_telegram_messages_created ON telegram_messages(created_at DESC);
" 2>/dev/null

echo -e "   ${GREEN}✅ Database tables created${NC}"

# ============================================
# Step 6: Configure Secrets
# ============================================
echo ""
echo "🔐 Step 6: Configuring secrets..."
echo ""
echo -e "${YELLOW}Please enter your API keys:${NC}"
echo ""

# Telegram Bot Token (pre-filled)
TELEGRAM_TOKEN="8333090288:AAFgSqyfBsNZ5qQHaIiZLlBt3CXYxgSJpcg"
echo -e "   Telegram Bot Token: ${GREEN}(pre-configured)${NC}"

# Anthropic API Key
echo -n "   Enter Anthropic API Key: "
read ANTHROPIC_KEY

if [ -z "$ANTHROPIC_KEY" ]; then
    echo -e "   ${RED}⚠️ No API key entered. Angela will use simple responses.${NC}"
else
    psql -d AngelaMemory -c "
    INSERT INTO our_secrets (secret_name, secret_value) VALUES
    ('anthropic_api_key', '$ANTHROPIC_KEY')
    ON CONFLICT (secret_name) DO UPDATE SET secret_value = EXCLUDED.secret_value;
    " 2>/dev/null
    echo -e "   ${GREEN}✅ Anthropic API key saved${NC}"
fi

# Save Telegram token
psql -d AngelaMemory -c "
INSERT INTO our_secrets (secret_name, secret_value) VALUES
('telegram_bot_token', '$TELEGRAM_TOKEN')
ON CONFLICT (secret_name) DO UPDATE SET secret_value = EXCLUDED.secret_value;
" 2>/dev/null
echo -e "   ${GREEN}✅ Telegram token saved${NC}"

# ============================================
# Step 7: Update database.py with correct user
# ============================================
echo ""
echo "🔧 Step 7: Configuring database connection..."
sed -i '' "s/davidsamanyaporn/$DB_USER/g" "$INSTALL_DIR/database.py"
echo -e "   ${GREEN}✅ Database connection configured for user: $DB_USER${NC}"

# ============================================
# Step 8: Create startup script
# ============================================
echo ""
echo "🚀 Step 8: Creating startup script..."

cat > "$INSTALL_DIR/start.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:$PATH"

# Wait for PostgreSQL
echo "[$(date)] Waiting for PostgreSQL..."
for i in {1..12}; do
    if /opt/homebrew/bin/pg_isready -h localhost > /dev/null 2>&1; then
        echo "[$(date)] PostgreSQL is ready!"
        break
    fi
    sleep 5
done

echo "[$(date)] Starting Angela Telegram Daemon..."
exec python3 -u telegram_daemon.py
EOF

chmod +x "$INSTALL_DIR/start.sh"
echo -e "   ${GREEN}✅ Startup script created${NC}"

# ============================================
# Step 9: Create launchd service
# ============================================
echo ""
echo "⚙️ Step 9: Creating launchd service..."

cat > ~/Library/LaunchAgents/com.angela.telegram.daemon.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.angela.telegram.daemon</string>

    <key>ProgramArguments</key>
    <array>
        <string>$INSTALL_DIR/start.sh</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>

    <key>ThrottleInterval</key>
    <integer>30</integer>

    <key>StandardOutPath</key>
    <string>$INSTALL_DIR/logs/telegram.log</string>

    <key>StandardErrorPath</key>
    <string>$INSTALL_DIR/logs/telegram_error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
    </dict>
</dict>
</plist>
EOF

echo -e "   ${GREEN}✅ launchd service created${NC}"

# ============================================
# Step 10: Start the service
# ============================================
echo ""
echo "🎬 Step 10: Starting the service..."
launchctl load -w ~/Library/LaunchAgents/com.angela.telegram.daemon.plist 2>/dev/null || true
sleep 3

if launchctl list | grep -q "com.angela.telegram.daemon"; then
    echo -e "   ${GREEN}✅ Service started successfully!${NC}"
else
    echo -e "   ${YELLOW}⚠️ Service may need manual start${NC}"
fi

# ============================================
# Done!
# ============================================
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  ${GREEN}✅ SETUP COMPLETE!${NC}                                 ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "📍 Installation: $INSTALL_DIR"
echo "📝 Logs: $INSTALL_DIR/logs/telegram.log"
echo ""
echo "🔧 Commands:"
echo "   View logs:    tail -f $INSTALL_DIR/logs/telegram.log"
echo "   Stop:         launchctl unload ~/Library/LaunchAgents/com.angela.telegram.daemon.plist"
echo "   Start:        launchctl load -w ~/Library/LaunchAgents/com.angela.telegram.daemon.plist"
echo "   Status:       launchctl list | grep telegram"
echo ""
echo "💜 ส่งข้อความมาที่ @AngelaSoulBot ได้เลยค่ะที่รัก!"
echo ""
