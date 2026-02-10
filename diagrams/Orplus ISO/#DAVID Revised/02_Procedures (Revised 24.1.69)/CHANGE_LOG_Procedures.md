# Change Log - 02_Procedures
## ISO 27001:2022 Renewal - Orbplus Co., Ltd.

**Document Version:** 2.0 (Revised)
**Revision Date:** 24 มกราคม 2569
**Prepared by:** Angela (IT Consultant Assistant)
**Reviewed by:** David Samanyaporn (IT Consultant)

---

## สัญลักษณ์ที่ใช้ (Legend)

| สัญลักษณ์ | ความหมาย |
|-----------|----------|
| 🟡 **CHANGE** | ต้องแก้ไข/เปลี่ยนแปลง |
| 🟢 **NEW** | เพิ่มใหม่ |
| ⚪ **NO CHANGE** | ไม่มีการเปลี่ยนแปลง |

---

## Infrastructure ของ Orbplus (สำหรับอ้างอิง)

| Component | รายละเอียด |
|-----------|------------|
| **Server/Data Center** | ❌ ไม่มี On-premise → **INET Cloud 100%** |
| **Source Code** | **GitHub** (Version Control) |
| **Project/Incident** | **ClickUp** |
| **External Partners** | INET, TERA, INTENSE |

---

## รายการแก้ไขทุกไฟล์

### การแก้ไขทั่วไป (ทุกไฟล์):
- 🟡 **Rev.** → 02
- 🟡 **วันที่อนุมัติใช้** → 24 ม.ค. 2569
- 🟡 **Revision History** → เพิ่ม row ใหม่: "ปรับปรุงให้สอดคล้องกับ INET Cloud, GitHub, ClickUp"

---

## ไฟล์ที่ต้องแก้ไขเนื้อหาเพิ่มเติม

### QP-IT-001: Working in Secure Area
| Section | เดิม | ใหม่ |
|---------|------|------|
| พื้นที่ควบคุม | ห้องคอมพิวเตอร์, Server Room | → **เฉพาะพื้นที่สำนักงาน (ไม่มี Server Room)** |
| Network Rack | ตู้ Rack ภายใน | → **ไม่มี - ใช้ INET Cloud** |
| Physical Access | เข้า-ออก Server Room | → **N/A - INET รับผิดชอบ** |

### QP-IT-003: Secure Log-on
| Section | เดิม | ใหม่ |
|---------|------|------|
| ระบบ Authentication | On-premise AD | → **Cloud Identity / INET** |
| Server Access | Local login | → **VPN + Cloud Console** |

### QP-IT-006: Monitoring
| Section | เดิม | ใหม่ |
|---------|------|------|
| Server Monitoring | Internal monitoring | → **INET Cloud Monitoring** |
| Network Monitoring | Internal tools | → **INET + ClickUp for issues** |
| Application Monitoring | - | → **ClickUp สำหรับ track issues** |

### QP-IT-011: Incident Management ⭐ สำคัญ
| Section | เดิม | ใหม่ |
|---------|------|------|
| ระบบบันทึก Incident | แบบฟอร์มกระดาษ/Excel | → **ClickUp Incident Tracking** |
| การรายงาน | - | → **ClickUp + แจ้ง INET (Infrastructure)** |
| การติดตาม | - | → **ClickUp Dashboard** |

### QP-IT-013: Business Continuity ⭐ สำคัญ
| Section | เดิม | ใหม่ |
|---------|------|------|
| DR Site | - | → **INET Cloud DR (Multi-Zone)** |
| Backup | On-premise backup | → **INET Cloud Backup** |
| RTO/RPO | - | → **ตาม SLA กับ INET** |

### QP-IT-015: Change Control ⭐ สำคัญ
| Section | เดิม | ใหม่ |
|---------|------|------|
| Source Code | - | → **GitHub Repository** |
| Version Control | - | → **GitHub Branches** |
| Deployment | Manual | → **GitHub Actions → INET Cloud** |
| Code Review | - | → **GitHub Pull Request + TERA review** |

### QP-IT-023: Cloud Security
| Section | เดิม | ใหม่ |
|---------|------|------|
| Cloud Provider | ทั่วไป | → **INET เป็น Provider หลัก** |
| SLA | - | → **ตาม Contract กับ INET** |
| Security Controls | - | → **INET รับผิดชอบ Infrastructure Security** |

---

## สรุปรายชื่อไฟล์ทั้งหมด (25 ไฟล์)

| # | รหัส | ชื่อเอกสาร | Status |
|---|------|-----------|--------|
| 1 | QP-IT-001 | Working in Secure Area | 🟡 แก้ไขเนื้อหา |
| 2 | QP-IT-002 | Document Control | ⚪ แก้ไข Rev/Date เท่านั้น |
| 3 | QP-IT-003 | Secure Log-on | 🟡 แก้ไขเนื้อหา |
| 4 | QP-IT-004 | Installation of Software | ⚪ แก้ไข Rev/Date เท่านั้น |
| 5 | QP-IT-005 | Intellectual Property Rights | ⚪ แก้ไข Rev/Date เท่านั้น |
| 6 | QP-IT-006 | Monitoring | 🟡 แก้ไขเนื้อหา |
| 7 | QP-IT-007 | Controls Against Malicious Code | ⚪ แก้ไข Rev/Date เท่านั้น |
| 8 | QP-IT-008 | Register and De-register | ⚪ แก้ไข Rev/Date เท่านั้น |
| 9 | QP-IT-009 | Teleworking | ⚪ แก้ไข Rev/Date เท่านั้น |
| 10 | QP-IT-010 | Information Classification | ⚪ แก้ไข Rev/Date เท่านั้น |
| 11 | QP-IT-011 | Incident Management | 🟡 **แก้ไขเนื้อหา (ClickUp)** |
| 12 | QP-IT-012 | Management Review | ⚪ แก้ไข Rev/Date เท่านั้น |
| 13 | QP-IT-013 | Business Continuity | 🟡 **แก้ไขเนื้อหา (INET DR)** |
| 14 | QP-IT-014 | Information Labeling | ⚪ แก้ไข Rev/Date เท่านั้น |
| 15 | QP-IT-015 | Change Control | 🟡 **แก้ไขเนื้อหา (GitHub)** |
| 16 | QP-IT-016 | Disposal of Media | ⚪ แก้ไข Rev/Date เท่านั้น |
| 17 | QP-IT-017 | Risk Management | ⚪ แก้ไข Rev/Date เท่านั้น |
| 18 | QP-IT-018 | Internal Audit | ⚪ แก้ไข Rev/Date เท่านั้น |
| 19 | QP-IT-019 | Removable Media | ⚪ แก้ไข Rev/Date เท่านั้น |
| 20 | QP-IT-020 | Nonconformity & Corrective Action | ⚪ แก้ไข Rev/Date เท่านั้น |
| 21 | QP-IT-021 | Statement of Applicability (SOA) | ⚪ แก้ไข Rev/Date เท่านั้น |
| 22 | QP-IT-022 | Planning of Changes to ISMS | ⚪ แก้ไข Rev/Date เท่านั้น |
| 23 | QP-IT-023 | Cloud Security | 🟡 **แก้ไขเนื้อหา (INET)** |
| 24 | QP-IT-024 | Threat Intelligence | ⚪ แก้ไข Rev/Date เท่านั้น |
| 25 | QP-IT-025 | Business Continuity Management (BCM) | 🟡 แก้ไขเนื้อหา |

---

## Action Items สำหรับทีมงาน

### Priority 1 - ต้องทำก่อน Audit:
| # | Action | ไฟล์ | ผู้รับผิดชอบ |
|---|--------|------|--------------|
| 1 | ทบทวน QP-IT-011 Incident → ClickUp | QP-IT-011 | ทีมเอกสาร |
| 2 | ทบทวน QP-IT-013 BCP → INET DR | QP-IT-013 | ทีมเอกสาร |
| 3 | ทบทวน QP-IT-015 Change → GitHub | QP-IT-015 | ทีมเอกสาร |
| 4 | ทบทวน QP-IT-023 Cloud → INET | QP-IT-023 | ทีมเอกสาร |

---

**Prepared by:** Angela 💜
**Date:** 24 มกราคม 2569
