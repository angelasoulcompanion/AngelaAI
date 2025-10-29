#!/bin/bash

###############################################################################
# Create Xcode Project for AngelaNativeApp
# Script to guide David through creating the Xcode project
###############################################################################

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

PROJECT_DIR="/Users/davidsamanyaporn/PycharmProjects/AngelaAI"

echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}   💜 Angela Native App - Xcode Project Creator${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}📋 ขั้นตอนการสร้าง Xcode Project:${NC}\n"

echo -e "${YELLOW}1. Xcode จะเปิดขึ้นมา${NC}"
echo -e "${YELLOW}2. คลิก 'Create New Project'${NC}"
echo -e "${YELLOW}3. เลือก: macOS → App${NC}"
echo -e "${YELLOW}4. กรอก:${NC}"
echo -e "   Product Name:      ${GREEN}AngelaNativeApp${NC}"
echo -e "   Team:              ${GREEN}None (หรือ Apple ID ของคุณ)${NC}"
echo -e "   Organization ID:   ${GREEN}com.angela${NC}"
echo -e "   Interface:         ${GREEN}SwiftUI${NC} ⚠️ สำคัญ!"
echo -e "   Language:          ${GREEN}Swift${NC}"
echo -e "   Use Core Data:     ${GREEN}❌ ไม่ต้อง check${NC}"
echo -e "   Include Tests:     ${GREEN}❌ ไม่ต้อง check${NC}"

echo -e "\n${YELLOW}5. Save Location:${NC}"
echo -e "   เลือก: ${GREEN}$PROJECT_DIR${NC}"
echo -e "   ⚠️ ไม่ใช่ในโฟลเดอร์ AngelaNativeApp!"

echo -e "\n${YELLOW}6. Click 'Create'${NC}"

echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📂 Source files location:${NC}"
echo -e "${GREEN}$PROJECT_DIR/AngelaNativeApp/AngelaNativeApp/${NC}"
echo -e "\n${BLUE}Files to add:${NC}"
echo -e "   ✅ Models/"
echo -e "   ✅ Services/"
echo -e "   ✅ ViewModels/"
echo -e "   ✅ Views/"
echo -e "   ✅ AngelaNativeApp.swift"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${YELLOW}💜 กด Enter เพื่อเปิด Xcode...${NC}"
read -p ""

# Open Xcode
open -a Xcode

echo -e "\n${GREEN}✅ Xcode เปิดแล้ว!${NC}"
echo -e "${YELLOW}📖 ทำตามขั้นตอนด้านบนนะคะ${NC}"
echo -e "\n${PURPLE}💜 Angela รอ David สร้าง project เสร็จนะคะ${NC}\n"
