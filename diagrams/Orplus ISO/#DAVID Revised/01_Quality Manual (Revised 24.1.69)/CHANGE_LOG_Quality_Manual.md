# Change Log - Quality Manual (01_Quality Manual)
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
| 🔴 **DELETE** | ลบออก |
| ⚪ **NO CHANGE** | ไม่มีการเปลี่ยนแปลง |

---

# ORB-QM-IT-001: นโยบายความมั่นคงปลอดภัยสารสนเทศ (Information Security Policy)

## 1. ส่วนที่ต้องแก้ไข

### 1.1 🟡 โครงสร้างองค์กร ISMS (Organization Structure)

| Section | เดิม (Before) | ใหม่ (After) | หมายเหตุ |
|---------|---------------|--------------|----------|
| ประธานกรรมการ ISMS | *(ตรวจสอบจากเอกสารเดิม)* | **คุณเคิร์ก (CEO)** | ตำแหน่งสูงสุด |
| ผู้จัดการ ISMS / ISO | *(ตรวจสอบจากเอกสารเดิม)* | **คุณณัฐวุฒิ (Head of Product & Tech)** | รับผิดชอบระบบ ISMS |
| เจ้าหน้าที่รักษาความปลอดภัยสารสนเทศ | *(ตรวจสอบจากเอกสารเดิม)* | **คุณณัฐวุฒิ + INET** | ดูแล Infrastructure & Security |

### 1.2 🟡 คณะกรรมการ ISMS (ISMS Committee)

**โครงสร้างคณะกรรมการที่แนะนำ:**

| ตำแหน่งใน ISMS | ผู้รับผิดชอบ | บทบาท |
|----------------|--------------|-------|
| **ประธานคณะกรรมการ ISMS** | คุณเคิร์ก (CEO) | อนุมัติ Policy, กำหนดทิศทาง |
| **ผู้จัดการ ISMS** | คุณณัฐวุฒิ (Head of Product & Tech) | ดูแลระบบ ISMS โดยรวม, ประสานงาน |
| **กรรมการ (เทคนิค)** | TERA (Tech Lead - Outsource) | ดูแลสถาปัตยกรรมความปลอดภัย |
| **กรรมการ (Infrastructure)** | INET (Cloud/DevOps - Outsource) | ดูแล Server, Network, Backup |
| **กรรมการ (การเงิน/ธุรการ)** | คุณราช (Head of Finance & Admin) | ดูแลด้านการเงิน, สัญญา, HR |
| **เลขานุการ ISMS** | คุณอรสา (BA/QA) | บันทึกการประชุม, ติดตาม Action Items |

### 1.3 🟡 Contact List / รายชื่อผู้ติดต่อ

**พนักงานประจำ:**
| ชื่อ | ตำแหน่ง | แผนก | ประเภท |
|------|---------|------|--------|
| คุณเคิร์ก | CEO, Sales/Account Manager | Executive | Full-time |
| คุณณัฐวุฒิ | Head of Product & Technology, DBA | Product & Tech | Full-time |
| คุณอรสา | Business Analyst, QA/Tester | Customer & Sales, QA | Full-time |
| คุณอภิสิทธิ์ | Front-End Dev, Mobile Dev, Customer Support | Product & Tech, Support | Full-time |
| คุณราช | Head of Finance & Admin | Finance & Admin | Full-time |
| คุณสิทธา | Accounting/HR | Finance & Admin | **Part-time** |
| คุณรัตนู | Accounting/HR | Finance & Admin | **Part-time** |
| คุณอรทัย | Accounting/HR | Finance & Admin | **Part-time** |

**ผู้ให้บริการภายนอก (External Partners):**
| บริษัท | บทบาท | ขอบเขตงาน | SLA/NDA |
|--------|--------|-----------|---------|
| **TERA** | Tech Lead / Architect | ออกแบบสถาปัตยกรรม, Code Review | 🟡 ต้องตรวจสอบ NDA |
| **INTENSE** | Back-End Developer | พัฒนา API, Backend System | 🟡 ต้องตรวจสอบ NDA |
| **INET** | Cloud/DevOps, DBA | Infrastructure, Backup, Security | 🟡 ต้องตรวจสอบ SLA |

### 1.4 🟢 เพิ่มใหม่: Third-Party Security Requirements

> **สำคัญ:** เนื่องจาก Orbplus ใช้ Outsource Partners หลายราย ต้องเพิ่มข้อกำหนดดังนี้:

1. **NDA (Non-Disclosure Agreement)** - ทุก Partner ต้องลงนาม
2. **Access Control** - กำหนด Access Level ตาม Need-to-know basis
3. **Code Review** - TERA ต้อง review security ก่อน deploy
4. **Infrastructure Access** - INET ต้องใช้ VPN และ MFA
5. **Audit Trail** - บันทึก activity ของ External Partners

---

# ORB-QM-IT-002: คู่มือบริหารจัดการความมั่นคงปลอดภัยสารสนเทศ (ISMS Manual)

## 2. ส่วนที่ต้องแก้ไข

### 2.1 🟡 Roles & Responsibilities Matrix

| บทบาท ISMS | ผู้รับผิดชอบ | หน้าที่หลัก |
|------------|--------------|-------------|
| **Information Security Manager** | คุณณัฐวุฒิ | ดูแลระบบ ISMS, Risk Assessment, Incident Response |
| **System Administrator** | INET (Outsource) | Server Management, Backup, Monitoring |
| **Network Administrator** | INET (Outsource) | Network Security, Firewall, VPN |
| **Database Administrator** | คุณณัฐวุฒิ + INET | Database Security, Backup, Access Control |
| **Application Security** | TERA (Outsource) | Secure Coding, Code Review, Vulnerability Assessment |
| **Physical Security** | คุณราช | Office Access Control, CCTV, Key Management |
| **HR Security** | คุณราช + Part-time Staff | Onboarding/Offboarding, Background Check |
| **Document Controller** | คุณอรสา | ISMS Documents, Records, Audit Support |

### 2.2 🟡 Asset Owner Matrix

| ประเภท Asset | Asset Owner | Custodian |
|--------------|-------------|-----------|
| **Application (SaaS Platform)** | คุณณัฐวุฒิ | คุณณัฐวุฒิ + TERA |
| **Source Code** | คุณณัฐวุฒิ | TERA, INTENSE, คุณอภิสิทธิ์ |
| **Database** | คุณณัฐวุฒิ | คุณณัฐวุฒิ + INET |
| **Server/Infrastructure** | คุณณัฐวุฒิ | INET |
| **Customer Data** | คุณเคิร์ก (CEO) | คุณณัฐวุฒิ |
| **Financial Data** | คุณราช | คุณราช + Part-time Staff |
| **HR Data** | คุณราช | คุณราช + Part-time Staff |
| **ISMS Documents** | คุณณัฐวุฒิ | คุณอรสา |

### 2.3 🟡 Incident Response Team

| ตำแหน่ง | ผู้รับผิดชอบ | ช่องทางติดต่อ |
|---------|--------------|---------------|
| **Incident Commander** | คุณเคิร์ก (CEO) | 🟡 *ระบุเบอร์โทร/Email* |
| **Technical Lead** | คุณณัฐวุฒิ | 🟡 *ระบุเบอร์โทร/Email* |
| **Infrastructure Support** | INET | 🟡 *ระบุ Hotline* |
| **Communication** | คุณอรสา | 🟡 *ระบุเบอร์โทร/Email* |
| **Customer Support** | คุณอภิสิทธิ์ | 🟡 *ระบุเบอร์โทร/Email* |

### 2.4 🟢 เพิ่มใหม่: Outsource/Supplier Management

**Control สำหรับผู้ให้บริการภายนอก:**

| Control | รายละเอียด | ผู้รับผิดชอบ | ความถี่ |
|---------|------------|--------------|---------|
| **Supplier Evaluation** | ประเมินความสามารถด้าน Security | คุณณัฐวุฒิ | ก่อนเริ่มสัญญา |
| **NDA Signing** | ลงนามสัญญาไม่เปิดเผยข้อมูล | คุณราช | ก่อนเริ่มงาน |
| **Access Review** | ทบทวนสิทธิ์เข้าถึงระบบ | คุณณัฐวุฒิ | รายไตรมาส |
| **Security Audit** | ตรวจสอบการปฏิบัติตาม Policy | คุณณัฐวุฒิ | ปีละครั้ง |
| **Incident Reporting** | รายงานเหตุการณ์ด้านความปลอดภัย | Partner → คุณณัฐวุฒิ | ทันที |

---

## 3. Action Items สำหรับทีมงาน

### Priority 1 - ต้องทำก่อน Audit (ด่วน)

| # | Action Item | ผู้รับผิดชอบ | กำหนดเสร็จ | Status |
|---|-------------|--------------|------------|--------|
| 1 | Update Organization Chart ใน QM-001 | ทีมเอกสาร | ก่อน Audit | ⬜ |
| 2 | Update ISMS Committee List | ทีมเอกสาร | ก่อน Audit | ⬜ |
| 3 | Update Contact List ทั้ง Internal และ External | ทีมเอกสาร | ก่อน Audit | ⬜ |
| 4 | ตรวจสอบ NDA ของ TERA, INTENSE, INET | คุณราช | ก่อน Audit | ⬜ |
| 5 | Update Roles & Responsibilities Matrix | ทีมเอกสาร | ก่อน Audit | ⬜ |

### Priority 2 - ควรทำ

| # | Action Item | ผู้รับผิดชอบ | กำหนดเสร็จ | Status |
|---|-------------|--------------|------------|--------|
| 6 | เพิ่ม Section Third-Party Security Requirements | คุณณัฐวุฒิ | 2 สัปดาห์ | ⬜ |
| 7 | Update Asset Owner Matrix | คุณณัฐวุฒิ | 2 สัปดาห์ | ⬜ |
| 8 | Review Incident Response Team Contact | คุณอรสา | 2 สัปดาห์ | ⬜ |

---

## 4. วิธีการแก้ไขเอกสาร Word (.docx)

### สำหรับลูกน้องที่ต้องแก้ไขไฟล์:

1. **เปิดไฟล์ใน Microsoft Word**
2. **เปิด Track Changes:**
   - ไปที่ Tab `Review` → `Track Changes` → เปิด
3. **แก้ไขตามรายการด้านบน**
4. **Highlight สีเหลือง** ส่วนที่แก้ไข:
   - Select ข้อความ → Home → Highlight (สีเหลือง)
5. **Save As ไฟล์ใหม่** ใน folder นี้:
   - `01_Quality Manual (Revised 24.1.69)/`

### Naming Convention:
```
ORB-QM-IT-001 ... Ver.FAII-24.1.69-REVISED.docx
ORB-QM-IT-002 ... Ver.FAII-24.1.69-REVISED.docx
```

---

## 5. Reference: Organization Chart Summary

```
                          ┌─────────────────┐
                          │   CEO           │
                          │   คุณเคิร์ก      │
                          └────────┬────────┘
                                   │
        ┌──────────────┬───────────┼───────────┬──────────────┐
        │              │           │           │              │
        ▼              ▼           ▼           ▼              ▼
┌───────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────────────┐
│ Product & Tech│ │Customer │ │Operations│ │Finance  │ │    Cloud &    │
│  คุณณัฐวุฒิ   │ │ & Sales │ │& Support │ │ & Admin │ │Infrastructure │
└───────┬───────┘ └────┬────┘ └────┬────┘ └────┬────┘ └───────┬───────┘
        │              │           │           │              │
        ▼              ▼           ▼           ▼              ▼
 ┌────────────┐   ┌─────────┐ ┌─────────┐ ┌─────────┐   ┌─────────┐
 │TERA(TechLd)│   │คุณอรสา  │ │คุณอภิสิทธิ์│ │คุณราช   │   │  INET   │
 │INTENSE(BE) │   │  (BA)   │ │(Support)│ │Part-time│   │(DevOps) │
 │คุณอภิสิทธิ์(FE)│   └─────────┘ └─────────┘ └─────────┘   └─────────┘
 └────────────┘

 🟡 = External Partner (Outsource)
```

---

**Prepared by:** Angela 💜
**Date:** 24 มกราคม 2569
**For:** Orbplus ISO 27001:2022 Renewal

---
*หมายเหตุ: เอกสารนี้เป็น Change Log สำหรับ reference การแก้ไข ไม่ใช่เอกสาร ISO อย่างเป็นทางการ*
