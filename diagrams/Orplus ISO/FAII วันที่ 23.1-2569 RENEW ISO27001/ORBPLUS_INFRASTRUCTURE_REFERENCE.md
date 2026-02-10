# Orbplus Infrastructure Reference
## สำหรับใช้อ้างอิงในการแก้ไขเอกสาร ISO 27001

**Last Updated:** 24 มกราคม 2569
**Prepared by:** David Samanyaporn (IT Consultant)

---

## 1. IT Infrastructure Overview

| หัวข้อ | รายละเอียด |
|--------|------------|
| **Server/Data Center** | ❌ **ไม่มี On-premise** |
| **Cloud Provider** | **INET** (Outsource ทั้งหมด) |
| **Physical Office** | มีเฉพาะ Workstation/Laptop ของพนักงาน |

---

## 2. Systems & Tools ที่ใช้งาน

| ระบบ | ผู้ให้บริการ | วัตถุประสงค์ | ผู้ดูแล |
|------|-------------|--------------|---------|
| **Cloud Infrastructure** | INET | Server, Network, Backup, Security | INET (Outsource) |
| **GitHub** | GitHub Inc. | Source Code Management, Version Control | คุณณัฐวุฒิ, TERA, INTENSE |
| **ClickUp** | ClickUp Inc. | Project Management, Incident Tracking, Team Communication | คุณณัฐวุฒิ, คุณอรสา |
| **SaaS Platform** | Orbplus (บน INET Cloud) | ผลิตภัณฑ์หลักของบริษัท | คุณณัฐวุฒิ |

---

## 3. External Partners (Outsource)

| Partner | บทบาท | ขอบเขตงาน | ระบบที่เข้าถึง |
|---------|--------|-----------|----------------|
| **INET** | Cloud Provider | Infrastructure ทั้งหมด: Server, Network, Backup, DR | Cloud Console, Server Admin |
| **TERA** | Tech Lead/Architect | System Design, Code Review | GitHub, ClickUp |
| **INTENSE** | Backend Developer | API Development | GitHub, ClickUp |

---

## 4. สิ่งที่ไม่มี / ไม่เกี่ยวข้อง

เนื่องจาก Orbplus ใช้ Cloud 100% จึง **ไม่มี** สิ่งต่อไปนี้:

| รายการ | สถานะ | หมายเหตุ |
|--------|--------|----------|
| Data Center / Server Room | ❌ ไม่มี | ใช้ INET Cloud |
| Physical Server | ❌ ไม่มี | ใช้ INET Cloud |
| Network Equipment (Core) | ❌ ไม่มี | ใช้ INET Cloud |
| UPS / Generator | ❌ ไม่มี | ใช้ INET Cloud |
| Physical Access Control (Server) | ❌ ไม่มี | ใช้ INET Cloud |
| CCTV (Server Room) | ❌ ไม่มี | ใช้ INET Cloud |

**สิ่งที่มีในออฟฟิศ:**
- Workstation / Laptop ของพนักงาน
- WiFi Router
- Physical Access Control (ออฟฟิศ) - ถ้ามี

---

## 5. Security Controls ที่ต้องเน้น

เนื่องจากใช้ Cloud และ SaaS ทั้งหมด ต้องเน้น controls เหล่านี้:

### 5.1 Cloud Security (INET)
- [ ] SLA/Contract กับ INET
- [ ] Data Backup & Recovery
- [ ] Network Security (Firewall, VPN)
- [ ] Access Control (Cloud Console)
- [ ] Audit Logs

### 5.2 Source Code Security (GitHub)
- [ ] Repository Access Control
- [ ] Branch Protection
- [ ] Code Review Process
- [ ] Secret Management (ไม่ commit credentials)
- [ ] Audit Logs

### 5.3 Project & Incident Management (ClickUp)
- [ ] User Access Control
- [ ] Incident Tracking Process
- [ ] Task Assignment & Monitoring
- [ ] Audit Trail

### 5.4 Endpoint Security (Workstation/Laptop)
- [ ] Antivirus / EDR
- [ ] Disk Encryption
- [ ] Password Policy
- [ ] Software Updates

---

## 6. Incident Management Flow

```
เหตุการณ์เกิดขึ้น
      ↓
บันทึกใน ClickUp (Incident Ticket)
      ↓
แจ้ง คุณณัฐวุฒิ (ISMS Manager)
      ↓
วิเคราะห์ & แก้ไข
      ↓
├── Infrastructure Issue → INET
├── Code Issue → TERA / INTENSE
└── Application Issue → Internal Team
      ↓
บันทึกผลใน ClickUp
      ↓
ปิด Incident
```

---

## 7. Contact Information

| Role | ชื่อ | ความรับผิดชอบ |
|------|------|---------------|
| **ISMS Director** | คุณเคิร์ก (CEO) | อนุมัติ Policy, ตัดสินใจระดับสูง |
| **ISMS Manager** | คุณณัฐวุฒิ | ดูแล ISMS, ประสานงาน INET/TERA/INTENSE |
| **Document Controller** | คุณอรสา | ควบคุมเอกสาร, บันทึกการประชุม |
| **Cloud Support** | INET | Infrastructure Issues |
| **Dev Support** | TERA, INTENSE | Application/Code Issues |

---

## 8. เอกสารที่ต้องปรับปรุงตาม Infrastructure นี้

| เอกสาร | สิ่งที่ต้องแก้ |
|--------|---------------|
| **QM-001** | ระบุว่าใช้ Cloud (ไม่มี on-prem) |
| **QM-002** | ระบุ tools: GitHub, ClickUp, INET |
| **QP-001 (Working in Secure Area)** | ปรับให้เป็น Cloud Access Control |
| **QP-006 (Monitoring)** | ใช้ INET monitoring + ClickUp |
| **FM-004 (Daily Check)** | ปรับเป็น Cloud monitoring checklist |
| **BCP** | DR Site = INET DR |

---

*Reference document for ISO 27001 revision*
*Orbplus Co., Ltd. © 2569*
