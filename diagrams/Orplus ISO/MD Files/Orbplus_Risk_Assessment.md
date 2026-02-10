# Orbplus Information Security Risk Assessment

**Document ID:** ORB-RA-2025-001
**Version:** 1.0
**Classification:** Confidential
**Effective Date:** January 2025
**Next Review:** January 2026

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2025 | Security Officer | Initial release |

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Prepared By | | | |
| Reviewed By | | | |
| Approved By | CEO | | |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Scope and Objectives](#2-scope-and-objectives)
3. [Risk Assessment Methodology](#3-risk-assessment-methodology)
4. [Asset Inventory](#4-asset-inventory)
5. [Threat Catalog](#5-threat-catalog)
6. [Vulnerability Assessment](#6-vulnerability-assessment)
7. [Risk Analysis](#7-risk-analysis)
8. [Risk Register](#8-risk-register)
9. [Risk Treatment Plan](#9-risk-treatment-plan)
10. [Monitoring and Review](#10-monitoring-and-review)
11. [Appendices](#11-appendices)

---

## 1. Executive Summary

### 1.1 Purpose
This document presents the Information Security Risk Assessment for Orbplus Co., Ltd., conducted in accordance with ISO 27001:2022 requirements. The assessment identifies, analyzes, and evaluates information security risks to the organization's assets, operations, and stakeholders.

### 1.2 Key Findings Summary

| Risk Level | Count | Percentage |
|------------|-------|------------|
| Critical | 2 | 7% |
| High | 6 | 21% |
| Medium | 12 | 43% |
| Low | 8 | 29% |
| **Total Risks Identified** | **28** | **100%** |

### 1.3 Top 5 Critical/High Risks

| Rank | Risk | Level | Status |
|------|------|-------|--------|
| 1 | Ransomware/Malware Attack | Critical | Treatment Required |
| 2 | Data Breach - Customer Data | Critical | Treatment Required |
| 3 | Unauthorized Access to Production | High | Treatment Required |
| 4 | Cloud Service Provider Outage | High | Treatment Required |
| 5 | Key Personnel Dependency | High | Treatment Required |

### 1.4 Recommendations
1. Implement advanced endpoint protection and backup solutions
2. Enhance access control with MFA for all systems
3. Establish business continuity and disaster recovery plans
4. Document and cross-train critical knowledge areas
5. Conduct regular security awareness training

---

## 2. Scope and Objectives

### 2.1 Scope
This risk assessment covers:

**In Scope:**
- All information assets owned or managed by Orbplus
- IT infrastructure (cloud and on-premise)
- Software development and deployment processes
- Customer data and business operations
- Third-party services and outsource partners
- Physical office locations

**Out of Scope:**
- Customer's own IT infrastructure
- End-user devices not managed by Orbplus

### 2.2 Objectives
1. Identify and classify information assets
2. Identify threats and vulnerabilities
3. Assess likelihood and impact of potential risks
4. Prioritize risks based on severity
5. Develop appropriate risk treatment strategies
6. Support compliance with ISO 27001:2022

### 2.3 Assessment Team

| Role | Responsibility |
|------|----------------|
| Risk Assessment Lead | Coordinate assessment, compile findings |
| Security Officer | Technical risk analysis, control recommendations |
| Department Heads | Asset identification, business impact assessment |
| CEO | Final approval, risk acceptance decisions |

---

## 3. Risk Assessment Methodology

### 3.1 Approach
Orbplus adopts a qualitative risk assessment methodology based on:
- ISO 27005:2022 Information Security Risk Management
- ISO 31000:2018 Risk Management Guidelines

### 3.2 Risk Formula

```
Risk Level = Likelihood × Impact
```

### 3.3 Likelihood Scale

| Level | Score | Description | Frequency |
|-------|-------|-------------|-----------|
| **Very High** | 5 | Almost certain to occur | Multiple times per year |
| **High** | 4 | Likely to occur | Once per year |
| **Medium** | 3 | Possible | Once every 2-3 years |
| **Low** | 2 | Unlikely | Once every 5 years |
| **Very Low** | 1 | Rare | Less than once in 10 years |

### 3.4 Impact Scale

| Level | Score | Financial Impact | Operational Impact | Reputational Impact |
|-------|-------|------------------|-------------------|---------------------|
| **Critical** | 5 | >฿5M or >20% revenue | Complete business halt >1 week | Major media coverage, regulatory action |
| **High** | 4 | ฿1M - ฿5M | Major disruption 1-7 days | Significant customer complaints |
| **Medium** | 3 | ฿100K - ฿1M | Moderate disruption 1-24 hours | Some customer complaints |
| **Low** | 2 | ฿10K - ฿100K | Minor disruption <4 hours | Internal awareness only |
| **Negligible** | 1 | <฿10K | No significant impact | No external awareness |

### 3.5 Risk Matrix

|  | **Impact** |||||
|---|---|---|---|---|---|
| **Likelihood** | Negligible (1) | Low (2) | Medium (3) | High (4) | Critical (5) |
| Very High (5) | 5 (Medium) | 10 (Medium) | 15 (High) | 20 (Critical) | 25 (Critical) |
| High (4) | 4 (Low) | 8 (Medium) | 12 (High) | 16 (High) | 20 (Critical) |
| Medium (3) | 3 (Low) | 6 (Medium) | 9 (Medium) | 12 (High) | 15 (High) |
| Low (2) | 2 (Low) | 4 (Low) | 6 (Medium) | 8 (Medium) | 10 (Medium) |
| Very Low (1) | 1 (Low) | 2 (Low) | 3 (Low) | 4 (Low) | 5 (Medium) |

### 3.6 Risk Level Classification

| Risk Score | Level | Action Required |
|------------|-------|-----------------|
| 20-25 | **Critical** | Immediate action required. CEO approval for acceptance. |
| 12-19 | **High** | Priority treatment within 30 days. Management approval required. |
| 6-11 | **Medium** | Treatment within 90 days. Department head approval. |
| 1-5 | **Low** | Accept or treat as resources allow. Document decision. |

### 3.7 Risk Treatment Options

| Option | Description | When to Use |
|--------|-------------|-------------|
| **Avoid** | Eliminate the risk by removing the source | Risk exceeds acceptable level, no viable controls |
| **Mitigate** | Reduce likelihood or impact through controls | Most common approach for manageable risks |
| **Transfer** | Share risk with third party (insurance, outsourcing) | Financial risks, specialized services |
| **Accept** | Acknowledge and monitor without treatment | Low risks, cost exceeds benefit |

---

## 4. Asset Inventory

### 4.1 Asset Classification

| Category | Description | Examples |
|----------|-------------|----------|
| **Information** | Data and information | Customer data, source code, configurations |
| **Software** | Applications and systems | ERP products, development tools, OS |
| **Hardware** | Physical equipment | Servers, workstations, network devices |
| **Services** | IT and business services | Cloud hosting, email, internet |
| **People** | Human resources | Employees, contractors, partners |
| **Intangible** | Non-physical assets | Reputation, intellectual property |

### 4.2 Critical Asset Register

| Asset ID | Asset Name | Category | Owner | Classification | Business Value |
|----------|------------|----------|-------|----------------|----------------|
| A-001 | Customer Database | Information | Head of Tech | Confidential | Critical |
| A-002 | Source Code Repository | Information | Tech Lead | Confidential | Critical |
| A-003 | Production Servers (Cloud) | Hardware | DevOps | Confidential | Critical |
| A-004 | Development Environment | Software | Tech Lead | Internal | High |
| A-005 | Backup Systems | Hardware | DevOps | Confidential | Critical |
| A-006 | Employee Credentials | Information | HR/Admin | Restricted | High |
| A-007 | API Keys & Secrets | Information | DevOps | Restricted | Critical |
| A-008 | Financial Records | Information | Finance Head | Confidential | High |
| A-009 | Customer Contracts | Information | Sales | Confidential | High |
| A-010 | Development Team | People | Head of Tech | N/A | Critical |

### 4.3 Data Classification

| Classification | Description | Handling Requirements |
|----------------|-------------|----------------------|
| **Restricted** | Highly sensitive, severe impact if disclosed | Encrypted, strict access control, audit logging |
| **Confidential** | Business sensitive, significant impact | Access control, need-to-know basis |
| **Internal** | For internal use only | Standard access controls |
| **Public** | Approved for public release | No restrictions |

---

## 5. Threat Catalog

### 5.1 Threat Categories

| Category | Threat Type | Description |
|----------|-------------|-------------|
| **Malicious** | External attacks | Hackers, competitors, nation-states |
| **Malicious** | Internal threats | Disgruntled employees, insider theft |
| **Accidental** | Human error | Misconfiguration, accidental deletion |
| **Environmental** | Natural disasters | Flood, fire, earthquake |
| **Technical** | System failures | Hardware failure, software bugs |

### 5.2 Threat Register

| Threat ID | Threat | Category | Threat Agent | Affected Assets |
|-----------|--------|----------|--------------|-----------------|
| T-001 | Ransomware/Malware Attack | Malicious | Cybercriminals | All IT systems |
| T-002 | Phishing Attack | Malicious | Cybercriminals | Employees, credentials |
| T-003 | Data Breach | Malicious | External/Internal | Customer data |
| T-004 | DDoS Attack | Malicious | Cybercriminals | Production systems |
| T-005 | Unauthorized Access | Malicious | External/Internal | All systems |
| T-006 | SQL Injection | Malicious | Cybercriminals | Databases |
| T-007 | Insider Threat | Malicious | Employees | All assets |
| T-008 | Social Engineering | Malicious | Cybercriminals | Employees |
| T-009 | Supply Chain Attack | Malicious | Third parties | Software, services |
| T-010 | Data Loss (Accidental) | Accidental | Employees | Information assets |
| T-011 | Misconfiguration | Accidental | IT staff | Infrastructure |
| T-012 | Hardware Failure | Technical | N/A | Servers, storage |
| T-013 | Software Bug | Technical | N/A | Applications |
| T-014 | Cloud Provider Outage | Technical | Provider | Cloud services |
| T-015 | Power Outage | Environmental | N/A | All systems |
| T-016 | Natural Disaster | Environmental | N/A | Physical assets |
| T-017 | Key Person Unavailability | Accidental | N/A | Operations |
| T-018 | Third-Party Breach | Malicious | Partners | Shared data |

---

## 6. Vulnerability Assessment

### 6.1 Vulnerability Categories

| Category | Description |
|----------|-------------|
| Technical | Software flaws, misconfigurations, outdated systems |
| Procedural | Lack of policies, inadequate processes |
| Physical | Inadequate physical security, environmental controls |
| Human | Lack of awareness, insufficient training |

### 6.2 Identified Vulnerabilities

| Vuln ID | Vulnerability | Category | Affected Assets | Current Controls |
|---------|--------------|----------|-----------------|------------------|
| V-001 | No MFA on critical systems | Technical | All systems | Password policy only |
| V-002 | Incomplete backup testing | Procedural | Backups | Monthly backups exist |
| V-003 | Limited security awareness | Human | Employees | Basic onboarding |
| V-004 | Single point of failure (key staff) | Human | Operations | Limited documentation |
| V-005 | Outdated dependencies | Technical | Applications | Manual updates |
| V-006 | Insufficient access reviews | Procedural | Access rights | Annual review only |
| V-007 | No incident response plan | Procedural | All systems | Ad-hoc response |
| V-008 | Weak vendor management | Procedural | Third parties | Basic contracts |
| V-009 | Limited logging/monitoring | Technical | Infrastructure | Basic logs only |
| V-010 | No DLP solution | Technical | Data | Manual controls |
| V-011 | Shared accounts | Technical | Development | Some shared access |
| V-012 | No penetration testing | Technical | Applications | Code review only |

---

## 7. Risk Analysis

### 7.1 Risk Assessment Matrix

| Risk ID | Risk Description | Threat | Vulnerability | Likelihood | Impact | Risk Score | Risk Level |
|---------|-----------------|--------|---------------|------------|--------|------------|------------|
| R-001 | Ransomware encrypts critical systems | T-001 | V-001, V-002 | 4 | 5 | 20 | **Critical** |
| R-002 | Customer data breach via unauthorized access | T-003 | V-001, V-006 | 4 | 5 | 20 | **Critical** |
| R-003 | Unauthorized access to production environment | T-005 | V-001, V-011 | 4 | 4 | 16 | **High** |
| R-004 | Cloud service provider outage | T-014 | N/A | 3 | 5 | 15 | **High** |
| R-005 | Key personnel leave with critical knowledge | T-017 | V-004 | 4 | 4 | 16 | **High** |
| R-006 | Successful phishing compromises credentials | T-002 | V-003 | 4 | 4 | 16 | **High** |
| R-007 | SQL injection attack on application | T-006 | V-005, V-012 | 3 | 4 | 12 | **High** |
| R-008 | Third-party vendor breach exposes data | T-018 | V-008 | 3 | 4 | 12 | **High** |
| R-009 | DDoS attack causes service outage | T-004 | V-009 | 3 | 3 | 9 | **Medium** |
| R-010 | Accidental data deletion | T-010 | V-002 | 3 | 3 | 9 | **Medium** |
| R-011 | Insider steals confidential data | T-007 | V-010 | 2 | 5 | 10 | **Medium** |
| R-012 | Software vulnerability exploited | T-013 | V-005 | 3 | 3 | 9 | **Medium** |
| R-013 | Social engineering attack succeeds | T-008 | V-003 | 3 | 3 | 9 | **Medium** |
| R-014 | Configuration error causes data exposure | T-011 | V-006 | 3 | 3 | 9 | **Medium** |
| R-015 | Hardware failure causes data loss | T-012 | V-002 | 2 | 4 | 8 | **Medium** |
| R-016 | Supply chain compromise | T-009 | V-008 | 2 | 4 | 8 | **Medium** |
| R-017 | Inadequate incident response prolongs outage | T-001-T-018 | V-007 | 3 | 3 | 9 | **Medium** |
| R-018 | Unauthorized access via shared accounts | T-005 | V-011 | 3 | 3 | 9 | **Medium** |
| R-019 | Compliance violation due to poor documentation | N/A | V-007 | 3 | 3 | 9 | **Medium** |
| R-020 | Failed recovery from backup | T-012 | V-002 | 2 | 4 | 8 | **Medium** |
| R-021 | Power outage disrupts operations | T-015 | N/A | 2 | 2 | 4 | **Low** |
| R-022 | Minor software bugs affect user experience | T-013 | V-005 | 4 | 1 | 4 | **Low** |
| R-023 | Physical theft of equipment | Physical | Basic security | 1 | 3 | 3 | **Low** |
| R-024 | Natural disaster damages office | T-016 | N/A | 1 | 4 | 4 | **Low** |
| R-025 | Email system outage | T-014 | N/A | 2 | 2 | 4 | **Low** |
| R-026 | Weak password compromised | T-005 | V-001 | 2 | 2 | 4 | **Low** |
| R-027 | Delayed security patches | T-013 | V-005 | 2 | 2 | 4 | **Low** |
| R-028 | Loss of minor documentation | T-010 | V-006 | 2 | 1 | 2 | **Low** |

### 7.2 Risk Distribution

```
Risk Level Distribution:

Critical (20-25): ██ 2 risks (7%)
High (12-19):     ██████ 6 risks (21%)
Medium (6-11):    ████████████ 12 risks (43%)
Low (1-5):        ████████ 8 risks (29%)

Total: 28 risks identified
```

---

## 8. Risk Register

### 8.1 Critical Risks (Immediate Action Required)

#### R-001: Ransomware Attack
| Attribute | Details |
|-----------|---------|
| **Risk ID** | R-001 |
| **Risk Description** | Ransomware encrypts critical systems and data, demanding payment for decryption |
| **Risk Owner** | Head of Product & Technology |
| **Threat** | T-001 Ransomware/Malware |
| **Vulnerabilities** | V-001 No MFA, V-002 Incomplete backup testing |
| **Affected Assets** | A-001 Customer Database, A-002 Source Code, A-003 Production Servers |
| **Likelihood** | 4 (High) - Ransomware attacks are increasingly common |
| **Impact** | 5 (Critical) - Complete business halt, data loss, ransom demand |
| **Risk Score** | 20 (Critical) |
| **Current Controls** | Antivirus, basic backups, firewall |
| **Treatment** | Mitigate |
| **Planned Controls** | EDR solution, immutable backups, MFA, security awareness training |
| **Target Risk Score** | 8 (Medium) |
| **Due Date** | Within 30 days |
| **Status** | Treatment Required |

#### R-002: Customer Data Breach
| Attribute | Details |
|-----------|---------|
| **Risk ID** | R-002 |
| **Risk Description** | Unauthorized access leads to customer data exposure |
| **Risk Owner** | Head of Product & Technology |
| **Threat** | T-003 Data Breach |
| **Vulnerabilities** | V-001 No MFA, V-006 Insufficient access reviews |
| **Affected Assets** | A-001 Customer Database |
| **Likelihood** | 4 (High) - Data breaches are prevalent |
| **Impact** | 5 (Critical) - Regulatory penalties, reputation damage, customer loss |
| **Risk Score** | 20 (Critical) |
| **Current Controls** | Access control, encryption at rest |
| **Treatment** | Mitigate |
| **Planned Controls** | MFA, quarterly access reviews, DLP, database activity monitoring |
| **Target Risk Score** | 8 (Medium) |
| **Due Date** | Within 30 days |
| **Status** | Treatment Required |

### 8.2 High Risks (Priority Treatment)

#### R-003: Unauthorized Production Access
| Attribute | Details |
|-----------|---------|
| **Risk ID** | R-003 |
| **Risk Description** | Unauthorized access to production environment leads to data manipulation or theft |
| **Risk Owner** | DevOps Lead |
| **Likelihood × Impact** | 4 × 4 = 16 (High) |
| **Treatment** | Mitigate |
| **Planned Controls** | MFA, privileged access management, session recording, eliminate shared accounts |
| **Target Risk Score** | 6 (Medium) |
| **Due Date** | Within 60 days |

#### R-004: Cloud Provider Outage
| Attribute | Details |
|-----------|---------|
| **Risk ID** | R-004 |
| **Risk Description** | Major cloud service provider outage causes extended downtime |
| **Risk Owner** | DevOps Lead |
| **Likelihood × Impact** | 3 × 5 = 15 (High) |
| **Treatment** | Mitigate + Transfer |
| **Planned Controls** | Multi-region deployment, DR site, SLA guarantees, business continuity plan |
| **Target Risk Score** | 6 (Medium) |
| **Due Date** | Within 90 days |

#### R-005: Key Personnel Dependency
| Attribute | Details |
|-----------|---------|
| **Risk ID** | R-005 |
| **Risk Description** | Critical knowledge concentrated in few individuals |
| **Risk Owner** | CEO |
| **Likelihood × Impact** | 4 × 4 = 16 (High) |
| **Treatment** | Mitigate |
| **Planned Controls** | Knowledge documentation, cross-training, succession planning |
| **Target Risk Score** | 8 (Medium) |
| **Due Date** | Within 90 days |

#### R-006: Phishing Attack Success
| Attribute | Details |
|-----------|---------|
| **Risk ID** | R-006 |
| **Risk Description** | Phishing attack compromises employee credentials |
| **Risk Owner** | Security Officer |
| **Likelihood × Impact** | 4 × 4 = 16 (High) |
| **Treatment** | Mitigate |
| **Planned Controls** | Security awareness training, phishing simulations, MFA, email filtering |
| **Target Risk Score** | 6 (Medium) |
| **Due Date** | Within 60 days |

#### R-007: SQL Injection Attack
| Attribute | Details |
|-----------|---------|
| **Risk ID** | R-007 |
| **Risk Description** | SQL injection vulnerability exploited to access database |
| **Risk Owner** | Tech Lead |
| **Likelihood × Impact** | 3 × 4 = 12 (High) |
| **Treatment** | Mitigate |
| **Planned Controls** | Parameterized queries, WAF, penetration testing, secure coding training |
| **Target Risk Score** | 4 (Low) |
| **Due Date** | Within 60 days |

#### R-008: Third-Party Vendor Breach
| Attribute | Details |
|-----------|---------|
| **Risk ID** | R-008 |
| **Risk Description** | Security breach at third-party vendor exposes Orbplus data |
| **Risk Owner** | Head of Finance & Admin |
| **Likelihood × Impact** | 3 × 4 = 12 (High) |
| **Treatment** | Mitigate + Transfer |
| **Planned Controls** | Vendor security assessments, contractual security requirements, data minimization |
| **Target Risk Score** | 6 (Medium) |
| **Due Date** | Within 90 days |

### 8.3 Medium Risks Summary

| Risk ID | Risk Description | Score | Treatment | Due Date |
|---------|-----------------|-------|-----------|----------|
| R-009 | DDoS attack causes outage | 9 | Mitigate | 90 days |
| R-010 | Accidental data deletion | 9 | Mitigate | 60 days |
| R-011 | Insider data theft | 10 | Mitigate | 90 days |
| R-012 | Software vulnerability exploited | 9 | Mitigate | 60 days |
| R-013 | Social engineering attack | 9 | Mitigate | 60 days |
| R-014 | Configuration error exposure | 9 | Mitigate | 60 days |
| R-015 | Hardware failure data loss | 8 | Mitigate | 90 days |
| R-016 | Supply chain compromise | 8 | Mitigate | 90 days |
| R-017 | Inadequate incident response | 9 | Mitigate | 30 days |
| R-018 | Shared account unauthorized access | 9 | Mitigate | 60 days |
| R-019 | Compliance violation | 9 | Mitigate | 60 days |
| R-020 | Failed backup recovery | 8 | Mitigate | 60 days |

### 8.4 Low Risks Summary

| Risk ID | Risk Description | Score | Treatment |
|---------|-----------------|-------|-----------|
| R-021 | Power outage | 4 | Accept |
| R-022 | Minor software bugs | 4 | Accept |
| R-023 | Physical equipment theft | 3 | Accept |
| R-024 | Natural disaster | 4 | Accept + Insurance |
| R-025 | Email system outage | 4 | Accept |
| R-026 | Weak password compromise | 4 | Mitigate (via MFA) |
| R-027 | Delayed security patches | 4 | Mitigate |
| R-028 | Minor documentation loss | 2 | Accept |

---

## 9. Risk Treatment Plan

### 9.1 Treatment Priority Matrix

| Priority | Timeframe | Risks | Budget Estimate |
|----------|-----------|-------|-----------------|
| **Immediate** | 0-30 days | R-001, R-002, R-017 | ฿200,000 |
| **High** | 31-60 days | R-003, R-006, R-007, R-010, R-012-R-014, R-018-R-020 | ฿300,000 |
| **Medium** | 61-90 days | R-004, R-005, R-008, R-009, R-011, R-015, R-016 | ฿250,000 |
| **Ongoing** | Continuous | R-021-R-028 | ฿50,000/year |

### 9.2 Detailed Treatment Actions

#### Phase 1: Immediate (0-30 Days)

| Action ID | Action | Risk Addressed | Owner | Resources |
|-----------|--------|----------------|-------|-----------|
| A-001 | Implement MFA for all critical systems | R-001, R-002, R-003 | DevOps | MFA solution license |
| A-002 | Deploy EDR/Advanced endpoint protection | R-001 | IT | EDR software |
| A-003 | Implement immutable backup solution | R-001, R-002 | DevOps | Backup storage |
| A-004 | Test backup restoration | R-001, R-010, R-020 | DevOps | Test environment |
| A-005 | Create incident response plan | R-017 | Security Officer | Time |
| A-006 | Conduct emergency security awareness | R-006, R-013 | HR | Training materials |

#### Phase 2: High Priority (31-60 Days)

| Action ID | Action | Risk Addressed | Owner | Resources |
|-----------|--------|----------------|-------|-----------|
| A-007 | Eliminate shared accounts | R-003, R-018 | IT | Account management |
| A-008 | Implement privileged access management | R-003 | DevOps | PAM solution |
| A-009 | Deploy Web Application Firewall | R-007 | DevOps | WAF service |
| A-010 | Conduct penetration testing | R-007, R-012 | Security Officer | External vendor |
| A-011 | Implement comprehensive logging | R-009, R-014 | DevOps | SIEM/Log solution |
| A-012 | Review and harden configurations | R-014 | IT | Time |
| A-013 | Document critical procedures | R-005, R-019 | All departments | Time |
| A-014 | Implement phishing simulation program | R-006, R-013 | HR | Simulation tool |

#### Phase 3: Medium Priority (61-90 Days)

| Action ID | Action | Risk Addressed | Owner | Resources |
|-----------|--------|----------------|-------|-----------|
| A-015 | Develop DR/BCP plan | R-004 | Management | Consultant |
| A-016 | Implement multi-region deployment | R-004 | DevOps | Cloud infrastructure |
| A-017 | Cross-train team members | R-005 | Department Heads | Time |
| A-018 | Vendor security assessment program | R-008, R-016 | Procurement | Assessment tool |
| A-019 | Implement DLP solution | R-011 | IT | DLP software |
| A-020 | DDoS protection service | R-009 | DevOps | DDoS service |

### 9.3 Control Implementation Schedule

```
Timeline:
Week 1-2:   MFA Implementation [████████████████████] 100%
Week 2-3:   EDR Deployment     [████████████████████] 100%
Week 3-4:   Backup Enhancement [████████████████████] 100%
Week 4:     IR Plan Creation   [████████████████████] 100%
Week 5-6:   PAM Implementation [████████████████████] 100%
Week 6-8:   WAF + Pen Testing  [████████████████████] 100%
Week 8-10:  DR/BCP Planning    [████████████████████] 100%
Week 10-12: Training & Review  [████████████████████] 100%
```

### 9.4 Risk Acceptance

The following low risks have been formally accepted by management:

| Risk ID | Risk | Score | Justification | Accepted By | Date |
|---------|------|-------|---------------|-------------|------|
| R-021 | Power outage | 4 | UPS provides sufficient protection, low frequency | CEO | |
| R-022 | Minor software bugs | 4 | Normal development process, minimal impact | Head of Tech | |
| R-023 | Physical theft | 3 | Insurance coverage, data encryption | CEO | |
| R-024 | Natural disaster | 4 | Cloud infrastructure, insurance coverage | CEO | |
| R-025 | Email outage | 4 | Provider SLA, alternative communication exists | CEO | |
| R-028 | Minor doc loss | 2 | Minimal business impact | Head of Tech | |

---

## 10. Monitoring and Review

### 10.1 Review Schedule

| Activity | Frequency | Responsible | Output |
|----------|-----------|-------------|--------|
| Risk register review | Monthly | Security Officer | Updated register |
| Full risk assessment | Annual | Risk Assessment Team | Assessment report |
| Control effectiveness | Quarterly | Department Heads | Effectiveness report |
| Threat landscape review | Quarterly | Security Officer | Threat update |
| Treatment plan progress | Monthly | Risk Owners | Progress report |

### 10.2 Key Risk Indicators (KRIs)

| KRI | Target | Measurement | Frequency |
|-----|--------|-------------|-----------|
| Critical/High risks | <5 | Count of risks scoring ≥12 | Monthly |
| Treatment completion | >90% | Completed vs planned actions | Monthly |
| Security incidents | <2/quarter | Number of security incidents | Quarterly |
| Vulnerability patch time | <30 days | Average time to patch critical vulns | Monthly |
| Security awareness score | >80% | Phishing simulation success rate | Quarterly |

### 10.3 Reporting

| Report | Audience | Frequency | Content |
|--------|----------|-----------|---------|
| Risk Dashboard | Management | Monthly | KRIs, risk status, treatment progress |
| Detailed Risk Report | CEO | Quarterly | Full risk analysis, trends, recommendations |
| Board Summary | Board | Annually | Executive summary, strategic risks |

### 10.4 Triggers for Re-Assessment

The risk assessment will be reviewed and updated when:
- Significant change in business operations
- Major security incident occurs
- New threat or vulnerability identified
- Regulatory changes affecting information security
- Acquisition of new systems or services
- Changes in threat landscape
- Annual review cycle

---

## 11. Appendices

### Appendix A: Risk Assessment Participants

| Name | Role | Department | Contribution |
|------|------|------------|--------------|
| | CEO | Executive | Final approval, strategic risks |
| | Head of Product & Technology | Technology | Technical risk assessment |
| | Head of Finance & Admin | Administration | Business impact, financial risks |
| | Tech Lead | Development | Application security risks |
| | DevOps | Operations | Infrastructure risks |
| | Security Officer | Security | Overall coordination |

### Appendix B: Reference Documents

| Document | Description |
|----------|-------------|
| ISO 27001:2022 | Information Security Management System requirements |
| ISO 27005:2022 | Information Security Risk Management |
| ISO 31000:2018 | Risk Management Guidelines |
| NIST Cybersecurity Framework | Risk management framework |
| OWASP Top 10 | Web application security risks |

### Appendix C: Definitions

| Term | Definition |
|------|------------|
| Asset | Anything that has value to the organization |
| Threat | Potential cause of an unwanted incident |
| Vulnerability | Weakness that can be exploited by a threat |
| Risk | Effect of uncertainty on objectives |
| Impact | Consequence of a risk event |
| Likelihood | Probability of a risk event occurring |
| Control | Measure that modifies risk |
| Residual Risk | Risk remaining after treatment |

### Appendix D: Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | Jan 2025 | Initial release | Security Officer |

---

## Approval Signatures

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Prepared By** | Security Officer | | |
| **Reviewed By** | Head of Product & Technology | | |
| **Approved By** | CEO | | |

---

**Document Classification:** Confidential
**Distribution:** Management Team, Security Officer, Auditors (as required)

*This document contains sensitive information about Orbplus security risks and controls. Handle according to classification guidelines.*

---

**End of Document**

*Orbplus Co., Ltd. © 2025 - All Rights Reserved*
