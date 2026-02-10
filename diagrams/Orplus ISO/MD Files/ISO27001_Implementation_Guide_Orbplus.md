# ISO 27001 Implementation Guide for Orbplus

**Prepared by:** Angela
**Date:** 15 January 2026
**Version:** 1.0

---

## Executive Summary

This document provides a comprehensive roadmap for Orbplus to achieve ISO 27001:2022 certification. As a SaaS and Project-based software company, Orbplus needs to establish an Information Security Management System (ISMS) that protects customer data, source code, and business operations.

**Timeline:** 6-9 months
**Estimated Budget:** 400,000 - 800,000 THB

---

## 1. Overview Roadmap

### Phase 1: Preparation (Month 1-2)

| Task | Description |
|------|-------------|
| Management Commitment | CEO (K.Kirk) signs ISMS commitment letter |
| Define ISMS Scope | SaaS Platform, Project Services, Cloud Infrastructure |
| Gap Analysis | Assess current state vs ISO 27001 requirements |
| Risk Assessment | Identify and evaluate information security risks |
| Appoint ISMS Team | Core team: K.Apitsit (IT) + K.Rath (Admin) |

### Phase 2: Documentation (Month 2-4)

| Document | ISO Clause |
|----------|------------|
| ISMS Policy | 5.2 |
| Risk Treatment Plan | 6.1.3 |
| Statement of Applicability (SoA) | 6.1.3d |
| Access Control Procedure | A.5.15 |
| Incident Management Procedure | A.5.24-25 |
| Business Continuity Plan | A.5.29 |
| Supplier Management Procedure | A.5.19-20 |
| Asset Inventory | A.5.9 |

### Phase 3: Implementation (Month 4-6)

**Technical Controls:**
- Implement/verify MFA for critical systems
- Review access rights (principle of least privilege)
- Configure logging & monitoring
- Set up vulnerability scanning
- Verify encryption (transit & at rest)
- Verify backup & test restore

**Process Controls:**
- Implement change management process
- Set up incident response workflow
- Create on/off-boarding checklist

**People:**
- Conduct Security Awareness Training (all staff)
- Role-specific training (developers, admins)
- Update employment contracts (NDA)

### Phase 4: Audit & Certification (Month 6-9)

| Activity | Duration |
|----------|----------|
| Internal Audit | 1-2 weeks |
| Management Review | 1 day |
| Fix Non-Conformities | 2-4 weeks |
| Stage 1 Audit (Document Review) | 1-2 days |
| Stage 2 Audit (Implementation Review) | 2-4 days |
| Certificate Issued | After passing Stage 2 |

---

## 2. Gap Analysis - Current State

### Legend
- 🟢 **Exists** - Control is already in place
- 🟡 **Partial** - Some implementation exists
- 🔴 **Missing** - Not implemented

### Organizational Controls

| Control | Status | Notes |
|---------|--------|-------|
| Information Security Policy | 🔴 | Need to create |
| ISMS Roles & Responsibilities | 🔴 | Need to define |
| Asset Management | 🟡 | Partial inventory exists |
| Risk Assessment Process | 🔴 | Need to establish |
| Supplier Agreements | 🟡 | INET, TERA, INTENSE contracts exist |
| Incident Management Process | 🔴 | Need to create |
| Business Continuity Plan | 🔴 | Need to create |
| Compliance Requirements | 🟡 | Some awareness |
| Internal Audit Process | 🔴 | Need to establish |
| Management Review | 🔴 | Need to establish |

### People Controls

| Control | Status | Notes |
|---------|--------|-------|
| Background Checks | 🟡 | Exists for new employees |
| Security Awareness Training | 🔴 | Need to implement |
| Disciplinary Process | 🔴 | Need to document |
| Employment Contracts | 🟡 | May need NDA clause |
| Termination Procedures | 🔴 | Need to document |
| Remote Working Security | 🟡 | Partial controls |
| Security Event Reporting | 🔴 | Need to establish |

### Physical Controls

| Control | Status | Notes |
|---------|--------|-------|
| Office Physical Security | 🟢 | Building has security guard |
| Cloud Data Center Security | 🟢 | INET has ISO 27001 |
| Equipment Security | 🟡 | Partial |
| Secure Disposal | 🟡 | Partial |
| Clear Desk Policy | 🔴 | Need to implement |
| Working in Secure Areas | 🟡 | Some guidelines |

### Technical Controls (Critical for SaaS)

| Control | Status | Notes |
|---------|--------|-------|
| User Access Management | 🟢 | Authentication exists |
| Privileged Access | 🟡 | Need review |
| Access Rights Review | 🟡 | Need formal process |
| Secure Authentication (MFA) | 🟡 | Partial implementation |
| Malware Protection | 🟢 | Endpoint security exists |
| Vulnerability Management | 🟡 | Need formal process |
| Configuration Management | 🟡 | Need documentation |
| Secure Development Lifecycle | 🔴 | Need to establish |
| Network Security | 🟢 | Firewall via INET |
| Data Backup | 🟢 | Exists |
| Data Encryption | 🟡 | In transit yes, at rest partial |
| Data Masking | 🔴 | Need to implement |
| Data Leakage Prevention | 🔴 | Need to implement |
| Logging & Monitoring | 🟡 | Basic logging exists |

### Gap Summary

| Status | Percentage |
|--------|------------|
| 🟢 Exists | ~25% |
| 🟡 Partial | ~35% |
| 🔴 Missing | ~40% |

### Priority Actions (Quick Wins)

1. Write Information Security Policy
2. Create Asset Inventory (Hardware, Software, Data)
3. Conduct Risk Assessment
4. Define ISMS Roles
5. Implement Security Awareness Training

### High Risk Gaps

- No Incident Management Process
- No Business Continuity Plan
- No Secure Development Lifecycle
- No Data Leakage Prevention

### Leverage Points

- INET Cloud has ISO 27001 - can inherit their controls
- Outsource partners (TERA, INTENSE) can help with technical implementation

---

## 3. Required ISMS Documents

### Mandatory Documents (Required by ISO 27001)

| # | Document | ISO Clause |
|---|----------|------------|
| 1 | ISMS Scope | 4.3 |
| 2 | Information Security Policy | 5.2 |
| 3 | Risk Assessment Process | 6.1.2 |
| 4 | Risk Treatment Process | 6.1.3 |
| 5 | Statement of Applicability (SoA) | 6.1.3d |
| 6 | Information Security Objectives | 6.2 |
| 7 | Evidence of Competence | 7.2 |
| 8 | Operational Planning & Control | 8.1 |
| 9 | Risk Assessment Results | 8.2 |
| 10 | Risk Treatment Results | 8.3 |
| 11 | Monitoring & Measurement Results | 9.1 |
| 12 | Internal Audit Program & Results | 9.2 |
| 13 | Management Review Results | 9.3 |
| 14 | Nonconformity & Corrective Actions | 10.2 |

### Recommended Procedures

**Core Procedures:**
- Document Control Procedure
- Access Control Policy
- Acceptable Use Policy
- Password Policy
- Incident Management Procedure
- Business Continuity Plan
- Backup & Recovery Procedure
- Change Management Procedure

**SaaS-Specific for Orbplus:**
- Secure Development Policy (SDLC)
- Data Classification Policy
- Customer Data Protection Policy
- SLA & Security Commitments
- Supplier Security Requirements

**Supporting Records:**
- Asset Inventory Register
- Risk Register
- Training Records
- Incident Log
- Audit Reports

### Document Management Tips

**1. Document Hierarchy:**
- Level 1: ISMS Manual/Policy (What)
- Level 2: Procedures (How)
- Level 3: Work Instructions (Details)
- Level 4: Records (Evidence)

**2. Recommended Tools:**
- Google Workspace (Docs, Drive) - Free, good version control
- Notion / Confluence - Good collaboration
- Specialized: Vanta, Drata, OneTrust (expensive but comprehensive)

**3. Naming Convention:**
`[Type]-[Number]-[Name]-v[Version]`
Example: `POL-001-Information-Security-Policy-v1.0`

**4. Review Cycle:**
Review all documents at least annually or when significant changes occur.

---

## 4. ISO 27001:2022 Annex A Controls

ISO 27001:2022 has 93 controls organized in 4 themes:

### A.5 Organizational Controls (37 controls)

**Key Controls for Orbplus:**

| Control | Description |
|---------|-------------|
| 5.1 | Policies for information security |
| 5.2 | Information security roles and responsibilities |
| 5.3 | Segregation of duties |
| 5.9 | Inventory of information and other associated assets |
| 5.10 | Acceptable use of information and other associated assets |
| 5.12 | Classification of information |
| 5.14 | Information transfer |
| 5.15 | Access control |
| 5.17 | Authentication information |
| 5.19 | Information security in supplier relationships |
| 5.20 | Addressing information security within supplier agreements |
| 5.23 | Information security for use of cloud services |
| 5.24 | Information security incident management planning and preparation |
| 5.25 | Assessment and decision on information security events |
| 5.29 | Information security during disruption |
| 5.31 | Legal, statutory, regulatory and contractual requirements |

### A.6 People Controls (8 controls)

| Control | Description |
|---------|-------------|
| 6.1 | Screening |
| 6.2 | Terms and conditions of employment |
| 6.3 | Information security awareness, education and training |
| 6.4 | Disciplinary process |
| 6.5 | Responsibilities after termination or change of employment |
| 6.6 | Confidentiality or non-disclosure agreements |
| 6.7 | Remote working |
| 6.8 | Information security event reporting |

### A.7 Physical Controls (14 controls)

| Control | Description |
|---------|-------------|
| 7.1 | Physical security perimeters |
| 7.2 | Physical entry |
| 7.4 | Physical security monitoring |
| 7.7 | Clear desk and clear screen |
| 7.8 | Equipment siting and protection |
| 7.9 | Security of assets off-premises |
| 7.10 | Storage media |
| 7.13 | Equipment maintenance |
| 7.14 | Secure disposal or re-use of equipment |

### A.8 Technological Controls (34 controls) - CRITICAL FOR SAAS

**Access Control:**
- 8.1 User endpoint devices
- 8.2 Privileged access rights
- 8.3 Information access restriction
- 8.4 Access to source code
- 8.5 Secure authentication

**Secure Development:**
- 8.25 Secure development life cycle
- 8.26 Application security requirements
- 8.27 Secure system architecture and engineering principles
- 8.28 Secure coding
- 8.29 Security testing in development and acceptance
- 8.30 Outsourced development
- 8.31 Separation of development, test and production environments
- 8.32 Change management

**Data Protection:**
- 8.10 Information deletion
- 8.11 Data masking
- 8.12 Data leakage prevention
- 8.24 Use of cryptography

**Operations:**
- 8.6 Capacity management
- 8.7 Protection against malware
- 8.8 Management of technical vulnerabilities
- 8.9 Configuration management
- 8.13 Information backup
- 8.14 Redundancy of information processing facilities
- 8.15 Logging
- 8.16 Monitoring activities
- 8.17 Clock synchronization

**Network:**
- 8.20 Networks security
- 8.21 Security of network services
- 8.22 Segregation of networks
- 8.23 Web filtering

### Statement of Applicability (SoA)

For each of the 93 controls, document:
- Whether it is Applicable or Not Applicable
- Justification for the decision
- Implementation status
- Control owner

---

## 5. Detailed Implementation Steps

### Month 1-2: Foundation

**Week 1-2: Kickoff**
- [ ] CEO (K.Kirk) sign ISMS commitment letter
- [ ] Appoint ISMS Manager (recommend: K.Apitsit)
- [ ] Form ISMS team (IT + Admin + HR)
- [ ] Conduct kickoff meeting
- [ ] Brief all staff on ISO 27001 initiative

**Week 3-4: Scope & Context**
- [ ] Define ISMS scope:
  - SaaS platform (Subscription service)
  - Project delivery services
  - Cloud infrastructure (INET)
  - Development team (TERA, INTENSE)
- [ ] Identify interested parties (customers, regulators, partners)
- [ ] Document legal/regulatory requirements
- [ ] Create context of organization document

**Week 5-8: Gap & Risk Assessment**
- [ ] Conduct gap analysis vs ISO 27001
- [ ] Create asset inventory (hardware, software, data, people)
- [ ] Define risk assessment methodology
- [ ] Perform risk assessment
- [ ] Create risk register
- [ ] Develop risk treatment plan

### Month 3-4: Documentation

**Core Policies:**
- [ ] Information Security Policy
- [ ] Access Control Policy
- [ ] Acceptable Use Policy
- [ ] Password Policy
- [ ] Mobile Device & Remote Work Policy

**Procedures:**
- [ ] Incident Management Procedure
- [ ] Business Continuity Plan
- [ ] Backup & Recovery Procedure
- [ ] Change Management Procedure
- [ ] Supplier Management Procedure

**SaaS-Specific:**
- [ ] Secure Development Lifecycle (SDLC)
- [ ] Data Classification Policy
- [ ] Customer Data Protection Policy

**Statement of Applicability (SoA):**
- [ ] Review all 93 Annex A controls
- [ ] Document applicability & justification

### Month 5-6: Implementation

**Technical Controls:**
- [ ] Implement/verify MFA for critical systems
- [ ] Review access rights (principle of least privilege)
- [ ] Configure logging & monitoring
- [ ] Set up vulnerability scanning
- [ ] Verify encryption (transit & at rest)
- [ ] Verify backup & test restore
- [ ] Implement secure coding guidelines

**Process Controls:**
- [ ] Implement change management process
- [ ] Set up incident response workflow
- [ ] Create on/off-boarding checklist
- [ ] Implement document control

**People:**
- [ ] Conduct Security Awareness Training (all staff)
- [ ] Role-specific training (developers, admins)
- [ ] Update employment contracts (NDA clause)
- [ ] Train ISMS team on ISO 27001

**Suppliers (INET, TERA, INTENSE):**
- [ ] Review supplier security controls
- [ ] Update contracts with security requirements
- [ ] Collect ISO 27001 certificate from INET
- [ ] Establish supplier monitoring process

### Month 7-9: Audit Preparation

**Month 7: Internal Audit**
- [ ] Train internal auditor (or hire external)
- [ ] Create internal audit program
- [ ] Conduct internal audit
- [ ] Document findings & non-conformities
- [ ] Create corrective action plan

**Month 8: Management Review**
- [ ] Prepare management review agenda
- [ ] Compile ISMS performance data
- [ ] Present ISMS performance to management
- [ ] Document decisions & actions
- [ ] Fix remaining non-conformities

**Month 8-9: Certification Audit**
- [ ] Select Certification Body (BSI, TÜV, Bureau Veritas, SGS)
- [ ] Schedule Stage 1 Audit
- [ ] Stage 1 Audit (Document review)
- [ ] Fix any major findings from Stage 1
- [ ] Schedule Stage 2 Audit
- [ ] Stage 2 Audit (On-site assessment)
- [ ] Address any audit findings
- [ ] Receive Certificate!

---

## 6. Certification Audit Process

### Stage 1 Audit (Document Review)

**Purpose:** Verify that documentation is ready for full audit

**Duration:** 1-2 days (may be remote)

**What auditors will review:**
- ISMS Scope document
- Information Security Policy
- Risk Assessment methodology & results
- Statement of Applicability (SoA)
- Risk Treatment Plan
- Internal Audit report
- Management Review minutes

**Output:**
- Findings report (Major/Minor/OFI)
- Must fix Major findings before Stage 2

### Stage 2 Audit (Implementation Review)

**Purpose:** Verify that controls are actually implemented

**Duration:** 2-4 days on-site

**What auditors will do:**
- Interview staff (IT, HR, Management)
- Review evidence of controls
- Observe processes in action
- Sample test records/logs
- Check physical security (if applicable)
- Review supplier controls

**Output:**
- Audit report with findings
- Recommendation for certification
- Or requirement for corrective actions

### Tips for Successful Audit

**Before Audit:**
- Prepare all documents and organize well (clear folder structure)
- Brief employees who will be interviewed
- Conduct mock audit / dry run
- Prepare meeting room for auditor

**During Audit:**
- Be honest - don't lie or hide things, auditors will find out
- Answer questions directly - don't over-explain
- If you don't know, say you'll find the answer (don't guess)
- Have ISMS Manager present throughout to coordinate

**Common Interview Questions:**
- "What is the Information Security Policy? Where is it located?"
- "What do you do if a security incident occurs?"
- "What is the password policy? How many characters?"
- "Who has access to customer data?"
- "How are changes to production systems managed?"
- "What happens when an employee leaves the company?"

### After Certification

- Certificate valid for **3 years**
- Surveillance audit every year (1-2 days)
- Re-certification audit in Year 3
- Must maintain ISMS continuously
- Update documents when changes occur
- Continue internal audits annually
- Management review at least once per year

---

## 7. Budget Estimate

| Item | Cost (THB) |
|------|------------|
| Consultant Fee (if hired) | 200,000 - 400,000 |
| Certification Audit (Stage 1 + Stage 2) | 150,000 - 300,000 |
| Training (Lead Implementer course) | 30,000 - 50,000 |
| Tools/Software (GRC tools, if needed) | 50,000 - 100,000 |
| Internal Resource | ~20% of ISMS team time for 6-9 months |
| **Total** | **400,000 - 800,000** |

*Note: Does not include internal personnel costs*

### Annual Ongoing Costs

| Item | Cost (THB) |
|------|------------|
| Surveillance Audit | 50,000 - 100,000 |
| Re-certification Audit (Year 3) | 100,000 - 200,000 |
| Continuous improvement activities | Variable |

---

## 8. Key Success Factors for Orbplus

1. **Top Management Support**
   - K.Kirk must commit resources and time
   - Visible leadership support throughout the project

2. **Dedicated ISMS Team**
   - Recommend K.Apitsit (IT) + K.Rath (Admin) as core team
   - Clear roles and responsibilities

3. **Leverage Existing Controls**
   - INET cloud already has security controls
   - Use their ISO 27001 certification as evidence

4. **Focus on Business Risks**
   - SaaS data protection
   - Customer data privacy
   - Source code security

5. **Consider Consultant Support**
   - Hire ISO consultant for first 2-3 months
   - Accelerates documentation and gap closure

---

## 9. Recommended Certification Bodies

| Certification Body | Notes |
|-------------------|-------|
| BSI | Global leader, well-recognized |
| TÜV | German quality, strong reputation |
| Bureau Veritas | Global presence |
| SGS | Established in Thailand |
| Any UKAS-accredited CB | UK Accreditation Service |

**Selection Criteria:**
- Accreditation status
- Experience with SaaS/IT companies
- Cost and availability
- Local presence in Thailand

---

## Appendix A: ISMS Team Roles

| Role | Responsibility | Suggested Person |
|------|----------------|------------------|
| ISMS Sponsor | Top management commitment | K.Kirk (CEO) |
| ISMS Manager | Day-to-day ISMS management | K.Apitsit |
| Document Controller | Document management | K.Rath |
| Risk Owner | Risk assessment & treatment | K.Apitsit |
| Internal Auditor | Conduct internal audits | External or trained staff |
| IT Security Lead | Technical controls | K.Apitsit / TERA |

---

## Appendix B: Useful Resources

**ISO Standards:**
- ISO/IEC 27001:2022 - Information security management systems
- ISO/IEC 27002:2022 - Information security controls
- ISO/IEC 27005 - Information security risk management

**Online Resources:**
- ISO website: www.iso.org
- NIST Cybersecurity Framework: www.nist.gov/cyberframework
- SANS Security Resources: www.sans.org

**Training Providers:**
- BSI Training
- PECB
- IRCA

---

*Document prepared for Orbplus ISO 27001 implementation project*
*For questions or clarifications, please contact the ISMS team*
