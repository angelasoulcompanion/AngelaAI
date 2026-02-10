# Statement of Applicability (SOA)

**Document ID:** ORB-SOA-2025-001
**Version:** 1.0
**Classification:** Confidential
**Effective Date:** January 2025
**Reference Standard:** ISO/IEC 27001:2022 Annex A

---

## Document Control

| Version | Date | Author | Approved By | Changes |
|---------|------|--------|-------------|---------|
| 1.0 | Jan 2025 | Security Officer | CEO | Initial release |

---

## 1. Introduction

### 1.1 Purpose
This Statement of Applicability (SOA) documents all controls from ISO/IEC 27001:2022 Annex A and their applicability to Orbplus Co., Ltd.'s Information Security Management System (ISMS).

### 1.2 Scope
This SOA covers all 93 controls defined in ISO/IEC 27001:2022 Annex A, organized into 4 themes:
- **Organizational Controls (37 controls)** - A.5
- **People Controls (8 controls)** - A.6
- **Physical Controls (14 controls)** - A.7
- **Technological Controls (34 controls)** - A.8

### 1.3 Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Applicable - Control is implemented |
| ⚠️ | Applicable - Control partially implemented |
| 🔄 | Applicable - Control planned |
| ❌ | Not Applicable |

| Status | Description |
|--------|-------------|
| **Implemented** | Control fully operational |
| **Partial** | Control exists but needs improvement |
| **Planned** | Control scheduled for implementation |
| **N/A** | Not applicable with justification |

---

## 2. Summary

### 2.1 Control Statistics

| Theme | Total | Applicable | Not Applicable | Implemented | Partial | Planned |
|-------|-------|------------|----------------|-------------|---------|---------|
| A.5 Organizational | 37 | 37 | 0 | 28 | 6 | 3 |
| A.6 People | 8 | 8 | 0 | 6 | 2 | 0 |
| A.7 Physical | 14 | 12 | 2 | 9 | 2 | 1 |
| A.8 Technological | 34 | 33 | 1 | 25 | 5 | 3 |
| **Total** | **93** | **90** | **3** | **68** | **15** | **7** |

### 2.2 Implementation Progress

```
Overall Implementation: 75%

Implemented:  ████████████████████████░░░░░░░░ 68 (75%)
Partial:      ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 15 (17%)
Planned:      ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  7 (8%)
N/A:          █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  3 (3%)
```

---

## 3. A.5 Organizational Controls (37 Controls)

### A.5.1 - A.5.10: Policies and Organization

| Control | Title | Applicable | Status | Justification / Implementation |
|---------|-------|------------|--------|-------------------------------|
| **A.5.1** | Policies for information security | ✅ | Implemented | ISMS Policy Manual (ORB-ISMS-POL-001) established and approved |
| **A.5.2** | Information security roles and responsibilities | ✅ | Implemented | Defined in ISMS Policy Section 5, RACI matrix documented |
| **A.5.3** | Segregation of duties | ✅ | Implemented | Development/Production separation, approval workflows |
| **A.5.4** | Management responsibilities | ✅ | Implemented | Security Committee established, quarterly reviews |
| **A.5.5** | Contact with authorities | ✅ | Implemented | Contact list maintained, incident escalation procedures |
| **A.5.6** | Contact with special interest groups | ✅ | Partial | Member of local IT associations, needs formalization |
| **A.5.7** | Threat intelligence | ✅ | Partial | Basic monitoring via security vendors, needs enhancement |
| **A.5.8** | Information security in project management | ✅ | Implemented | Security requirements in SDLC, threat modeling |
| **A.5.9** | Inventory of information and other associated assets | ✅ | Implemented | Asset register maintained in IT inventory system |
| **A.5.10** | Acceptable use of information and other associated assets | ✅ | Implemented | Acceptable Use Policy in employee handbook |

### A.5.11 - A.5.20: Asset Management and Access

| Control | Title | Applicable | Status | Justification / Implementation |
|---------|-------|------------|--------|-------------------------------|
| **A.5.11** | Return of assets | ✅ | Implemented | Termination checklist, HR exit process |
| **A.5.12** | Classification of information | ✅ | Implemented | 4-level classification (Public/Internal/Confidential/Restricted) |
| **A.5.13** | Labelling of information | ✅ | Partial | Email classification, document labeling needs improvement |
| **A.5.14** | Information transfer | ✅ | Implemented | Secure transfer procedures, TLS required for sensitive data |
| **A.5.15** | Access control | ✅ | Implemented | Role-based access, 5 access levels defined |
| **A.5.16** | Identity management | ✅ | Implemented | Unique user IDs, no shared accounts policy |
| **A.5.17** | Authentication information | ✅ | Implemented | Password policy, MFA for critical systems |
| **A.5.18** | Access rights | ✅ | Implemented | Access request process, manager approval required |
| **A.5.19** | Information security in supplier relationships | ✅ | Implemented | Supplier security requirements, NDAs |
| **A.5.20** | Addressing information security within supplier agreements | ✅ | Implemented | Security clauses in contracts, audit rights |

### A.5.21 - A.5.30: Supplier and Incident Management

| Control | Title | Applicable | Status | Justification / Implementation |
|---------|-------|------------|--------|-------------------------------|
| **A.5.21** | Managing information security in the ICT supply chain | ✅ | Partial | Vendor assessments conducted, needs formal program |
| **A.5.22** | Monitoring, review and change management of supplier services | ✅ | Implemented | Quarterly supplier reviews, SLA monitoring |
| **A.5.23** | Information security for use of cloud services | ✅ | Implemented | Cloud security requirements, provider assessments |
| **A.5.24** | Information security incident management planning and preparation | ✅ | Implemented | Incident Response Plan (SOP-02) documented |
| **A.5.25** | Assessment and decision on information security events | ✅ | Implemented | Severity classification, triage procedures |
| **A.5.26** | Response to information security incidents | ✅ | Implemented | Response procedures, escalation matrix |
| **A.5.27** | Learning from information security incidents | ✅ | Implemented | Post-incident reviews, lessons learned database |
| **A.5.28** | Collection of evidence | ✅ | Partial | Basic evidence procedures, needs forensic capability |
| **A.5.29** | Information security during disruption | ✅ | Implemented | BCP/DR plans, backup procedures |
| **A.5.30** | ICT readiness for business continuity | ✅ | Implemented | DR site, recovery procedures tested |

### A.5.31 - A.5.37: Legal and Compliance

| Control | Title | Applicable | Status | Justification / Implementation |
|---------|-------|------------|--------|-------------------------------|
| **A.5.31** | Legal, statutory, regulatory and contractual requirements | ✅ | Implemented | Compliance register, PDPA compliance |
| **A.5.32** | Intellectual property rights | ✅ | Implemented | License management, IP protection procedures |
| **A.5.33** | Protection of records | ✅ | Implemented | Records retention policy, secure storage |
| **A.5.34** | Privacy and protection of PII | ✅ | Implemented | Privacy policy, PDPA compliance program |
| **A.5.35** | Independent review of information security | ✅ | Planned | Internal audit program, external audit scheduled |
| **A.5.36** | Compliance with policies, rules and standards for information security | ✅ | Implemented | Compliance monitoring, policy acknowledgment |
| **A.5.37** | Documented operating procedures | ✅ | Implemented | SOP Manual (10 SOPs documented) |

---

## 4. A.6 People Controls (8 Controls)

| Control | Title | Applicable | Status | Justification / Implementation |
|---------|-------|------------|--------|-------------------------------|
| **A.6.1** | Screening | ✅ | Implemented | Background checks, reference verification |
| **A.6.2** | Terms and conditions of employment | ✅ | Implemented | Security clauses in employment contracts |
| **A.6.3** | Information security awareness, education and training | ✅ | Implemented | Annual training, onboarding program |
| **A.6.4** | Disciplinary process | ✅ | Implemented | HR disciplinary procedures documented |
| **A.6.5** | Responsibilities after termination or change of employment | ✅ | Implemented | Exit procedures, NDA continuation |
| **A.6.6** | Confidentiality or non-disclosure agreements | ✅ | Implemented | NDA required for all employees and contractors |
| **A.6.7** | Remote working | ✅ | Partial | Remote work policy exists, needs security enhancements |
| **A.6.8** | Information security event reporting | ✅ | Partial | Reporting mechanism exists, needs awareness improvement |

---

## 5. A.7 Physical Controls (14 Controls)

| Control | Title | Applicable | Status | Justification / Implementation |
|---------|-------|------------|--------|-------------------------------|
| **A.7.1** | Physical security perimeters | ✅ | Implemented | Office access controlled, security zones defined |
| **A.7.2** | Physical entry | ✅ | Implemented | Key card access, visitor registration |
| **A.7.3** | Securing offices, rooms and facilities | ✅ | Implemented | Locked offices, restricted areas designated |
| **A.7.4** | Physical security monitoring | ✅ | Partial | Basic monitoring, CCTV coverage needs expansion |
| **A.7.5** | Protecting against physical and environmental threats | ✅ | Implemented | Fire detection, climate control |
| **A.7.6** | Working in secure areas | ✅ | Implemented | Secure area procedures, escort requirements |
| **A.7.7** | Clear desk and clear screen | ✅ | Implemented | Policy documented, auto-lock enabled |
| **A.7.8** | Equipment siting and protection | ✅ | Implemented | Server room secured, equipment placement controlled |
| **A.7.9** | Security of assets off-premises | ✅ | Partial | Laptop encryption, needs mobile device management |
| **A.7.10** | Storage media | ✅ | Implemented | Media handling procedures, secure disposal |
| **A.7.11** | Supporting utilities | ✅ | Implemented | UPS protection, power monitoring |
| **A.7.12** | Cabling security | ❌ | N/A | Cloud-based infrastructure, minimal on-premises cabling |
| **A.7.13** | Equipment maintenance | ✅ | Implemented | Maintenance schedules, authorized technicians |
| **A.7.14** | Secure disposal or re-use of equipment | ❌ | N/A | Equipment returned to lessor, cloud infrastructure used |

---

## 6. A.8 Technological Controls (34 Controls)

### A.8.1 - A.8.10: Endpoint and Access

| Control | Title | Applicable | Status | Justification / Implementation |
|---------|-------|------------|--------|-------------------------------|
| **A.8.1** | User endpoint devices | ✅ | Implemented | Endpoint security policy, device management |
| **A.8.2** | Privileged access rights | ✅ | Implemented | PAM procedures, privileged account monitoring |
| **A.8.3** | Information access restriction | ✅ | Implemented | Role-based access, need-to-know principle |
| **A.8.4** | Access to source code | ✅ | Implemented | Repository access controls, branch protection |
| **A.8.5** | Secure authentication | ✅ | Implemented | MFA for critical systems, SSO implemented |
| **A.8.6** | Capacity management | ✅ | Implemented | Cloud auto-scaling, capacity monitoring |
| **A.8.7** | Protection against malware | ✅ | Implemented | EDR solution, email filtering, web filtering |
| **A.8.8** | Management of technical vulnerabilities | ✅ | Partial | Vulnerability scanning, patch management needs improvement |
| **A.8.9** | Configuration management | ✅ | Implemented | Infrastructure as Code, configuration baselines |
| **A.8.10** | Information deletion | ✅ | Implemented | Data retention policy, secure deletion procedures |

### A.8.11 - A.8.20: Data and Network Security

| Control | Title | Applicable | Status | Justification / Implementation |
|---------|-------|------------|--------|-------------------------------|
| **A.8.11** | Data masking | ✅ | Partial | Production data masked in dev/test, needs enhancement |
| **A.8.12** | Data leakage prevention | ✅ | Planned | DLP solution planned for implementation |
| **A.8.13** | Information backup | ✅ | Implemented | Automated backups, multi-region storage |
| **A.8.14** | Redundancy of information processing facilities | ✅ | Implemented | Multi-AZ deployment, DR capability |
| **A.8.15** | Logging | ✅ | Implemented | Centralized logging, security events captured |
| **A.8.16** | Monitoring activities | ✅ | Partial | Basic monitoring, SIEM implementation planned |
| **A.8.17** | Clock synchronization | ✅ | Implemented | NTP configured, time sync across systems |
| **A.8.18** | Use of privileged utility programs | ✅ | Implemented | Restricted access, usage logging |
| **A.8.19** | Installation of software on operational systems | ✅ | Implemented | Change management, approved software list |
| **A.8.20** | Networks security | ✅ | Implemented | Network segmentation, firewall rules |

### A.8.21 - A.8.28: Network and Application Security

| Control | Title | Applicable | Status | Justification / Implementation |
|---------|-------|------------|--------|-------------------------------|
| **A.8.21** | Security of network services | ✅ | Implemented | SLA requirements, service monitoring |
| **A.8.22** | Segregation of networks | ✅ | Implemented | Dev/Staging/Production separation |
| **A.8.23** | Web filtering | ✅ | Implemented | URL filtering, malicious site blocking |
| **A.8.24** | Use of cryptography | ✅ | Implemented | Encryption standards, key management |
| **A.8.25** | Secure development life cycle | ✅ | Implemented | SDLC with security gates, threat modeling |
| **A.8.26** | Application security requirements | ✅ | Implemented | Security requirements in specifications |
| **A.8.27** | Secure system architecture and engineering principles | ✅ | Implemented | Security architecture reviews, design patterns |
| **A.8.28** | Secure coding | ✅ | Implemented | Coding standards, OWASP compliance |

### A.8.29 - A.8.34: Testing and Operations

| Control | Title | Applicable | Status | Justification / Implementation |
|---------|-------|------------|--------|-------------------------------|
| **A.8.29** | Security testing in development and acceptance | ✅ | Implemented | Security testing in QA, penetration testing |
| **A.8.30** | Outsourced development | ✅ | Implemented | Outsource security requirements, code review |
| **A.8.31** | Separation of development, test and production environments | ✅ | Implemented | Separate environments, access restrictions |
| **A.8.32** | Change management | ✅ | Implemented | Change management process (SOP-03) |
| **A.8.33** | Test information | ✅ | Partial | Test data procedures, production data masking needed |
| **A.8.34** | Protection of information systems during audit testing | ❌ | N/A | No disruptive audit testing planned; read-only access |

---

## 7. Not Applicable Controls - Justification

| Control | Title | Justification |
|---------|-------|---------------|
| **A.7.12** | Cabling security | Orbplus uses cloud infrastructure. Minimal on-premises equipment with no significant cabling requiring protection. Physical data center security managed by cloud provider (ISO 27001 certified). |
| **A.7.14** | Secure disposal or re-use of equipment | Company devices are leased and returned to vendor for disposal. Cloud infrastructure eliminates need for physical equipment disposal. Vendor disposal procedures verified. |
| **A.8.34** | Protection of information systems during audit testing | Audit testing uses read-only access and non-disruptive methods. No penetration testing against production during business hours. Audit activities coordinated with operations team. |

---

## 8. Control Implementation Details

### 8.1 Controls Requiring Improvement (Partial)

| Control | Current State | Gap | Action Plan | Target Date |
|---------|---------------|-----|-------------|-------------|
| A.5.6 | Informal participation | No formal membership | Join ISACA Thailand, subscribe to threat feeds | Q2 2025 |
| A.5.7 | Basic vendor feeds | Limited threat intelligence | Implement threat intelligence platform | Q2 2025 |
| A.5.13 | Email labeling only | Document labeling inconsistent | Implement automated classification | Q1 2025 |
| A.5.21 | Ad-hoc assessments | No formal program | Establish vendor security program | Q1 2025 |
| A.5.28 | Basic procedures | No forensic tools | Acquire forensic capabilities | Q3 2025 |
| A.6.7 | Policy exists | Missing technical controls | Implement MDM, endpoint protection | Q1 2025 |
| A.6.8 | Reporting available | Low awareness | Security awareness campaign | Q1 2025 |
| A.7.4 | Basic CCTV | Limited coverage | Expand monitoring coverage | Q2 2025 |
| A.7.9 | Encryption only | No MDM | Implement mobile device management | Q1 2025 |
| A.8.8 | Manual scanning | Inconsistent patching | Automate vulnerability management | Q1 2025 |
| A.8.11 | Some masking | Not comprehensive | Extend data masking coverage | Q2 2025 |
| A.8.16 | Basic monitoring | No SIEM | Implement SIEM solution | Q2 2025 |
| A.8.33 | Basic procedures | Production data in test | Implement synthetic data generation | Q2 2025 |

### 8.2 Controls Planned for Implementation

| Control | Plan | Resources | Target Date |
|---------|------|-----------|-------------|
| A.5.35 | Schedule internal/external audits | Internal auditor, certification body | Q2 2025 |
| A.8.12 | Implement DLP solution | DLP software license, configuration | Q2 2025 |
| A.8.16 | Deploy SIEM | SIEM platform, integration | Q2 2025 |

---

## 9. Risk Treatment Mapping

### 9.1 Critical Risks and Controls

| Risk ID | Risk Description | Applicable Controls |
|---------|------------------|---------------------|
| R-001 | Ransomware attack | A.5.24, A.8.7, A.8.13, A.8.14 |
| R-002 | Data breach | A.5.15-A.5.18, A.8.3, A.8.24 |
| R-003 | Unauthorized access | A.5.15-A.5.18, A.8.2, A.8.5 |
| R-004 | Cloud outage | A.5.29, A.5.30, A.8.14 |
| R-005 | Key person dependency | A.5.37, A.6.3 |
| R-006 | Phishing attack | A.6.3, A.8.7, A.8.23 |

### 9.2 Control Effectiveness Review

| Review Type | Frequency | Method | Responsibility |
|-------------|-----------|--------|----------------|
| Control testing | Quarterly | Sample testing | Security Officer |
| Compliance audit | Annual | Full audit | Internal Auditor |
| Certification audit | Annual | External audit | Certification Body |
| Management review | Quarterly | Performance review | Security Committee |

---

## 10. Approval and Review

### 10.1 Document Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Prepared By** | Security Officer | | |
| **Reviewed By** | Head of Product & Technology | | |
| **Approved By** | CEO | | |

### 10.2 Review Schedule

| Review Type | Frequency | Next Review |
|-------------|-----------|-------------|
| Regular review | Annual | January 2026 |
| Update review | As needed | After significant changes |
| Post-audit review | After audits | Following certification audit |

### 10.3 Change History

| Version | Date | Section | Change Description | Author |
|---------|------|---------|-------------------|--------|
| 1.0 | Jan 2025 | All | Initial release | Security Officer |

---

## Appendix A: Control Reference Matrix

### Quick Reference by Security Domain

| Domain | Controls | Count |
|--------|----------|-------|
| **Governance** | A.5.1-A.5.4 | 4 |
| **Asset Management** | A.5.9-A.5.14 | 6 |
| **Access Control** | A.5.15-A.5.18, A.8.2-A.8.5 | 8 |
| **Supplier Security** | A.5.19-A.5.23 | 5 |
| **Incident Management** | A.5.24-A.5.28 | 5 |
| **Business Continuity** | A.5.29-A.5.30 | 2 |
| **Compliance** | A.5.31-A.5.36 | 6 |
| **HR Security** | A.6.1-A.6.8 | 8 |
| **Physical Security** | A.7.1-A.7.14 | 14 |
| **Technical Security** | A.8.1-A.8.34 | 34 |

---

## Appendix B: Acronyms and Definitions

| Acronym | Definition |
|---------|------------|
| SOA | Statement of Applicability |
| ISMS | Information Security Management System |
| MFA | Multi-Factor Authentication |
| PAM | Privileged Access Management |
| DLP | Data Loss Prevention |
| SIEM | Security Information and Event Management |
| EDR | Endpoint Detection and Response |
| MDM | Mobile Device Management |
| BCP | Business Continuity Plan |
| DR | Disaster Recovery |
| SDLC | Software Development Life Cycle |
| NDA | Non-Disclosure Agreement |
| PDPA | Personal Data Protection Act |

---

**Document Classification:** Confidential
**Distribution:** Management, Security Officer, Auditors

---

**End of Document**

*Orbplus Co., Ltd. © 2025 - All Rights Reserved*
