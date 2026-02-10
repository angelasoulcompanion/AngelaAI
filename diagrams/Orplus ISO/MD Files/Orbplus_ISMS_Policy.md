# Orbplus Information Security Management System (ISMS) Policy Manual

**Document ID:** ORB-ISMS-POL-001
**Version:** 1.0
**Classification:** Internal
**Effective Date:** January 2025
**Review Date:** January 2026

---

## Document Control

| Version | Date | Author | Approved By | Changes |
|---------|------|--------|-------------|---------|
| 1.0 | Jan 2025 | Security Officer | CEO | Initial release |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Information Security Policy](#2-information-security-policy)
3. [ISMS Scope](#3-isms-scope)
4. [Leadership and Commitment](#4-leadership-and-commitment)
5. [Roles and Responsibilities](#5-roles-and-responsibilities)
6. [Risk Management Policy](#6-risk-management-policy)
7. [Access Control Policy](#7-access-control-policy)
8. [Asset Management Policy](#8-asset-management-policy)
9. [Human Resources Security Policy](#9-human-resources-security-policy)
10. [Physical and Environmental Security Policy](#10-physical-and-environmental-security-policy)
11. [Operations Security Policy](#11-operations-security-policy)
12. [Communications Security Policy](#12-communications-security-policy)
13. [System Acquisition and Development Policy](#13-system-acquisition-and-development-policy)
14. [Supplier Relationship Policy](#14-supplier-relationship-policy)
15. [Incident Management Policy](#15-incident-management-policy)
16. [Business Continuity Policy](#16-business-continuity-policy)
17. [Compliance Policy](#17-compliance-policy)
18. [Policy Review and Maintenance](#18-policy-review-and-maintenance)
19. [Appendices](#19-appendices)

---

## 1. Introduction

### 1.1 Purpose
This document establishes the Information Security Management System (ISMS) policies for Orbplus Co., Ltd. These policies provide the framework for protecting information assets and ensuring the confidentiality, integrity, and availability of information.

### 1.2 Applicability
This policy manual applies to:
- All employees of Orbplus Co., Ltd.
- All contractors, consultants, and temporary staff
- All third-party service providers with access to Orbplus information
- All information assets owned, operated, or managed by Orbplus

### 1.3 Compliance
Compliance with these policies is mandatory. Violations may result in disciplinary action, up to and including termination of employment or contract, and may be subject to legal action.

### 1.4 Related Documents

| Document | Description |
|----------|-------------|
| ORB-SOP-Manual | Standard Operating Procedures |
| ORB-RA-2025-001 | Risk Assessment Report |
| ORB-SOA-001 | Statement of Applicability |
| ORB-BCP-001 | Business Continuity Plan |

---

## 2. Information Security Policy

### 2.1 Policy Statement

**Orbplus Co., Ltd. is committed to protecting its information assets and those of its customers from all threats, whether internal or external, deliberate or accidental.**

Information security is essential to maintain:
- Customer confidence and trust
- Business operations and continuity
- Competitive advantage
- Legal and regulatory compliance
- Corporate reputation

### 2.2 Security Objectives

| Objective | Description | Measure |
|-----------|-------------|---------|
| **Confidentiality** | Information is accessible only to authorized individuals | Access control, encryption |
| **Integrity** | Information is accurate and complete | Data validation, audit trails |
| **Availability** | Information is available when needed | Redundancy, backup, DR |

### 2.3 Security Principles

1. **Defense in Depth** - Multiple layers of security controls
2. **Least Privilege** - Minimum access necessary for job functions
3. **Separation of Duties** - Critical functions divided among personnel
4. **Need to Know** - Information shared only when necessary
5. **Security by Design** - Security built into systems from inception

### 2.4 Management Commitment

Management commits to:
- Providing adequate resources for information security
- Establishing and maintaining the ISMS
- Ensuring security awareness across the organization
- Reviewing ISMS performance regularly
- Continuous improvement of security posture

---

## 3. ISMS Scope

### 3.1 Organizational Scope

| Element | Details |
|---------|---------|
| **Organization** | Orbplus Co., Ltd. |
| **Business Activities** | Development, deployment, and support of cloud-based ERP solutions |
| **Locations** | Head office and remote work environments |
| **Products/Services** | Orbplus ERP, API integrations, customer support |

### 3.2 Information Assets in Scope

| Asset Category | Examples |
|----------------|----------|
| **Information** | Customer data, source code, business records |
| **Software** | ERP applications, development tools, operating systems |
| **Hardware** | Cloud infrastructure, workstations, network equipment |
| **Services** | Cloud hosting, email, development platforms |
| **People** | Employees, contractors, outsource partners |

### 3.3 Exclusions

| Exclusion | Justification |
|-----------|---------------|
| Customer IT infrastructure | Outside Orbplus control |
| End-user personal devices | Not company-managed |

### 3.4 Interfaces and Dependencies

| Interface | Description | Controls |
|-----------|-------------|----------|
| Cloud Service Providers | AWS/GCP hosting | Contractual security requirements |
| Outsource Partners | TERA, INTENSE, INET | Security agreements, access controls |
| Customers | SaaS users | Terms of service, data protection |

---

## 4. Leadership and Commitment

### 4.1 Top Management Responsibilities

The CEO and management team shall:

1. Establish the information security policy and objectives
2. Ensure ISMS requirements are integrated into business processes
3. Ensure adequate resources are available
4. Communicate the importance of effective security management
5. Ensure the ISMS achieves its intended outcomes
6. Direct and support continual improvement
7. Support other relevant management roles

### 4.2 Security Governance Structure

```
┌─────────────────────────────────────────┐
│                  CEO                     │
│         (Ultimate Accountability)        │
└─────────────────────┬───────────────────┘
                      │
┌─────────────────────┴───────────────────┐
│           Security Committee             │
│    (Strategic Direction & Oversight)     │
└─────────────────────┬───────────────────┘
                      │
┌─────────────────────┴───────────────────┐
│           Security Officer               │
│      (Operational Management)            │
└─────────────────────┬───────────────────┘
                      │
┌─────────────────────┴───────────────────┐
│          Department Heads                │
│       (Implementation & Compliance)      │
└─────────────────────────────────────────┘
```

### 4.3 Security Committee

**Members:**
- CEO (Chair)
- Head of Product & Technology
- Head of Finance & Admin
- Security Officer (Secretary)

**Responsibilities:**
- Review and approve security policies
- Oversee risk management activities
- Review security incidents and trends
- Approve security investments
- Monitor ISMS performance

**Meeting Frequency:** Quarterly (or as needed)

---

## 5. Roles and Responsibilities

### 5.1 Role Definitions

#### 5.1.1 CEO
| Responsibility |
|----------------|
| Ultimate accountability for information security |
| Approve ISMS policies and objectives |
| Allocate resources for security initiatives |
| Champion security culture |

#### 5.1.2 Security Officer
| Responsibility |
|----------------|
| Develop and maintain ISMS documentation |
| Coordinate risk assessments |
| Monitor security controls effectiveness |
| Manage security incidents |
| Conduct security awareness programs |
| Liaise with external parties on security matters |
| Report to management on ISMS performance |

#### 5.1.3 Head of Product & Technology
| Responsibility |
|----------------|
| Technical implementation of security controls |
| Secure software development practices |
| Infrastructure security management |
| Technical incident response |

#### 5.1.4 Department Heads
| Responsibility |
|----------------|
| Implement security policies in their areas |
| Ensure staff awareness and compliance |
| Identify and report security risks |
| Authorize access for their staff |

#### 5.1.5 All Employees
| Responsibility |
|----------------|
| Comply with security policies and procedures |
| Protect information assets in their custody |
| Report security incidents and concerns |
| Complete required security training |
| Use information systems responsibly |

### 5.2 RACI Matrix

| Activity | CEO | Security Officer | Head of Tech | Dept Heads | Employees |
|----------|-----|------------------|--------------|------------|-----------|
| Policy Approval | A | R | C | C | I |
| Risk Assessment | A | R | C | C | I |
| Control Implementation | I | C | A/R | R | I |
| Incident Response | I | A | R | C | R |
| Security Training | A | R | C | C | R |
| Compliance Monitoring | I | A/R | C | R | I |
| Access Management | I | C | A | R | I |

*R=Responsible, A=Accountable, C=Consulted, I=Informed*

---

## 6. Risk Management Policy

### 6.1 Policy Statement
Orbplus shall identify, assess, and treat information security risks in a systematic and consistent manner to protect information assets and achieve business objectives.

### 6.2 Risk Management Framework

#### 6.2.1 Risk Assessment Process
1. **Establish Context** - Define scope, criteria, and methodology
2. **Risk Identification** - Identify assets, threats, vulnerabilities
3. **Risk Analysis** - Determine likelihood and impact
4. **Risk Evaluation** - Compare against risk criteria
5. **Risk Treatment** - Select and implement controls
6. **Monitor and Review** - Ongoing monitoring and reassessment

#### 6.2.2 Risk Criteria

| Risk Level | Score | Acceptance | Authority |
|------------|-------|------------|-----------|
| Critical | 20-25 | Not acceptable | CEO required |
| High | 12-19 | Requires treatment | Management approval |
| Medium | 6-11 | Treatment recommended | Dept Head approval |
| Low | 1-5 | Acceptable | Document decision |

#### 6.2.3 Risk Treatment Options

| Option | Description | When to Use |
|--------|-------------|-------------|
| **Avoid** | Eliminate the risk source | Unacceptable risk, no viable controls |
| **Mitigate** | Reduce likelihood or impact | Most common approach |
| **Transfer** | Share with third party | Insurance, outsourcing |
| **Accept** | Acknowledge without action | Low risk, cost exceeds benefit |

### 6.3 Risk Assessment Schedule

| Assessment Type | Frequency | Trigger |
|-----------------|-----------|---------|
| Full Assessment | Annual | Scheduled review |
| Targeted Assessment | As needed | New systems, major changes |
| Control Review | Quarterly | Ongoing monitoring |

### 6.4 Risk Documentation
All risk assessments shall be documented in the Risk Register, including:
- Risk description and owner
- Likelihood and impact ratings
- Current and planned controls
- Treatment decisions and status
- Review dates

---

## 7. Access Control Policy

### 7.1 Policy Statement
Access to information and information systems shall be controlled based on business and security requirements.

### 7.2 Access Control Principles

1. **Default Deny** - Access denied unless explicitly granted
2. **Least Privilege** - Minimum access required for job function
3. **Need to Know** - Access based on business need
4. **Separation of Duties** - Conflicting duties separated

### 7.3 User Access Management

#### 7.3.1 User Registration
| Requirement |
|-------------|
| All users must be uniquely identified |
| User IDs must not be shared |
| Access requires formal authorization |
| Temporary accounts must have expiry dates |

#### 7.3.2 Access Authorization

| Access Level | Approver | Examples |
|--------------|----------|----------|
| Basic (L1) | Supervisor | Read-only access |
| Standard (L2) | Department Head | Read/Write access |
| Elevated (L3) | Head of Technology | Sensitive data access |
| Admin (L4) | CEO | System administration |
| Super Admin (L5) | CEO + Security Officer | Full infrastructure access |

#### 7.3.3 Access Review

| Review Type | Frequency | Reviewer |
|-------------|-----------|----------|
| Privileged Access | Monthly | Security Officer |
| All User Access | Quarterly | Department Heads |
| System Access Audit | Annual | External Auditor |

#### 7.3.4 Access Revocation
- Immediate revocation upon termination
- Same-day modification upon role change
- Automatic disable after 90 days inactivity

### 7.4 Authentication Requirements

| System Type | Authentication Method |
|-------------|----------------------|
| Production Systems | MFA required |
| Administrative Access | MFA + strong password |
| Customer-facing Applications | Password + optional MFA |
| VPN/Remote Access | MFA required |

### 7.5 Password Policy

| Requirement | Specification |
|-------------|---------------|
| Minimum Length | 12 characters |
| Complexity | Upper, lower, number, special |
| Maximum Age | 90 days |
| History | Last 12 passwords |
| Lockout | 5 failed attempts |
| Lockout Duration | 30 minutes |

---

## 8. Asset Management Policy

### 8.1 Policy Statement
All information assets shall be identified, classified, and protected according to their value and sensitivity.

### 8.2 Asset Inventory

#### 8.2.1 Asset Categories

| Category | Examples | Owner |
|----------|----------|-------|
| Information | Customer data, source code, configs | Data Owner |
| Software | Applications, tools, licenses | IT Manager |
| Hardware | Servers, workstations, devices | IT Manager |
| Services | Cloud services, subscriptions | Service Owner |
| People | Skills, knowledge | HR |

#### 8.2.2 Asset Register Requirements
Each asset entry shall include:
- Unique identifier
- Description
- Owner and custodian
- Location
- Classification
- Value assessment

### 8.3 Information Classification

| Classification | Description | Handling |
|----------------|-------------|----------|
| **Restricted** | Severe impact if disclosed | Encryption, strict access, audit |
| **Confidential** | Significant business impact | Access control, secure storage |
| **Internal** | For internal use only | Standard controls |
| **Public** | Approved for public release | No restrictions |

### 8.4 Labeling and Handling

| Classification | Labeling | Storage | Transmission | Disposal |
|----------------|----------|---------|--------------|----------|
| Restricted | "RESTRICTED" header/footer | Encrypted storage | Encrypted only | Secure destruction |
| Confidential | "CONFIDENTIAL" marking | Secure location | Secure channel | Shred/wipe |
| Internal | "INTERNAL" optional | Standard | Standard | Normal disposal |
| Public | None required | Any | Any | Normal disposal |

### 8.5 Acceptable Use

#### 8.5.1 Permitted Use
- Business purposes aligned with job responsibilities
- Incidental personal use that doesn't interfere with work
- Use in compliance with licenses and agreements

#### 8.5.2 Prohibited Use
- Unauthorized access or data extraction
- Installation of unauthorized software
- Sharing credentials or bypassing controls
- Illegal activities or harassment
- Storing personal data on company systems

### 8.6 Return of Assets
All company assets must be returned upon:
- Termination of employment
- End of contract
- Change of role (if applicable)
- Request by management

---

## 9. Human Resources Security Policy

### 9.1 Policy Statement
Security shall be addressed throughout the employment lifecycle, from recruitment to termination.

### 9.2 Prior to Employment

#### 9.2.1 Screening
| Requirement | Application |
|-------------|-------------|
| Identity verification | All positions |
| Qualification verification | All positions |
| Reference checks | All positions |
| Background check | Sensitive positions |
| Credit check | Financial roles (with consent) |

#### 9.2.2 Terms of Employment
Employment contracts shall include:
- Confidentiality obligations
- Acceptable use agreement
- Security responsibilities
- Consequences of violations

### 9.3 During Employment

#### 9.3.1 Security Awareness

| Training | Audience | Frequency |
|----------|----------|-----------|
| Security Induction | New hires | On joining |
| General Awareness | All staff | Annual |
| Role-specific Training | Technical staff | Annual |
| Phishing Simulation | All staff | Quarterly |

#### 9.3.2 Performance and Conduct
- Security responsibilities in job descriptions
- Security compliance in performance reviews
- Disciplinary process for violations

### 9.4 Termination and Change

#### 9.4.1 Termination Process
| Step | Timing | Responsible |
|------|--------|-------------|
| Notify IT of termination | Immediately | HR |
| Disable accounts | Within 4 hours | IT |
| Revoke physical access | Last day | Facilities |
| Collect assets | Last day | HR/Manager |
| Exit interview | Last day | HR |
| Archive data | Within 2 weeks | IT |

#### 9.4.2 Role Changes
- Review and adjust access rights
- Update responsibilities and training
- Transfer asset ownership

---

## 10. Physical and Environmental Security Policy

### 10.1 Policy Statement
Physical access to facilities and equipment shall be controlled to prevent unauthorized access, damage, or interference.

### 10.2 Secure Areas

#### 10.2.1 Security Perimeters
| Zone | Description | Controls |
|------|-------------|----------|
| Public | Reception, lobby | Visitor sign-in |
| Office | General work areas | Access card |
| Restricted | Server room, archives | Access card + PIN |

#### 10.2.2 Entry Controls
| Control | Requirement |
|---------|-------------|
| Physical access | Key card/badge required |
| Visitor management | Sign-in, escort required |
| Loading areas | Controlled, monitored |
| Emergency exits | Alarmed, for emergency only |

### 10.3 Equipment Security

#### 10.3.1 Equipment Placement
- Servers in secure, climate-controlled locations
- Monitors positioned to prevent shoulder surfing
- Sensitive equipment in restricted areas

#### 10.3.2 Supporting Utilities
| Utility | Protection |
|---------|------------|
| Power | UPS, surge protection |
| Cooling | Climate control, monitoring |
| Cabling | Protected, labeled |

#### 10.3.3 Maintenance
- Authorized personnel only
- Maintenance logs maintained
- Data cleared before disposal

### 10.4 Clear Desk and Screen

| Requirement | Implementation |
|-------------|----------------|
| Clear desk | Lock documents when away |
| Clear screen | Auto-lock after 5 minutes |
| Printers | Collect printouts immediately |
| Whiteboards | Erase sensitive information |

---

## 11. Operations Security Policy

### 11.1 Policy Statement
Day-to-day operations shall be performed securely, with appropriate controls to protect against malware, data loss, and operational failures.

### 11.2 Operational Procedures

#### 11.2.1 Documented Procedures
All critical operations shall be documented, including:
- System administration tasks
- Backup and recovery procedures
- Incident response procedures
- Change management procedures

#### 11.2.2 Change Management
| Change Type | Lead Time | Approval |
|-------------|-----------|----------|
| Standard | 24 hours | Auto-approved |
| Normal | 5 days | CAB |
| Emergency | Immediate | Emergency CAB |

### 11.3 Protection from Malware

| Control | Implementation |
|---------|----------------|
| Endpoint protection | EDR on all endpoints |
| Email filtering | Anti-malware, anti-phishing |
| Web filtering | Malicious URL blocking |
| Updates | Regular signature updates |
| Awareness | User training on threats |

### 11.4 Backup

#### 11.4.1 Backup Requirements

| Data Type | Frequency | Retention | Location |
|-----------|-----------|-----------|----------|
| Production DB | 6 hours | 30 days | Primary + DR |
| Transaction logs | 15 minutes | 7 days | Primary + DR |
| Application code | On commit | Indefinite | Git repository |
| Configurations | Daily | 90 days | Secure backup |
| System images | Weekly | 4 weeks | DR site |

#### 11.4.2 Backup Testing
| Test | Frequency |
|------|-----------|
| Sample restoration | Weekly |
| Full recovery test | Monthly |
| DR failover test | Quarterly |

### 11.5 Logging and Monitoring

#### 11.5.1 Events to Log

| Event Type | Examples |
|------------|----------|
| Access events | Login, logout, failed attempts |
| Privileged actions | Admin activities, config changes |
| Security events | Alerts, incidents, policy violations |
| System events | Errors, failures, performance |

#### 11.5.2 Log Protection
- Logs stored in tamper-proof location
- Access restricted to authorized personnel
- Retention minimum 1 year
- Regular review and alerting

### 11.6 Vulnerability Management

| Activity | Frequency | Responsibility |
|----------|-----------|----------------|
| Vulnerability scanning | Monthly | Security Officer |
| Patch assessment | Weekly | DevOps |
| Critical patches | Within 72 hours | DevOps |
| Penetration testing | Annual | External vendor |

---

## 12. Communications Security Policy

### 12.1 Policy Statement
Information transmitted over networks shall be protected against interception, modification, and unauthorized access.

### 12.2 Network Security

#### 12.2.1 Network Controls

| Control | Implementation |
|---------|----------------|
| Segmentation | Separate dev/prod/management |
| Firewalls | Perimeter and internal |
| IDS/IPS | Network monitoring |
| VPN | Remote access encryption |
| DDoS protection | Cloud-based mitigation |

#### 12.2.2 Network Access

| Access Type | Requirements |
|-------------|--------------|
| Internal network | Employee authentication |
| Remote access | VPN + MFA |
| Guest access | Isolated network |
| Cloud resources | VPN or secure API |

### 12.3 Information Transfer

#### 12.3.1 Electronic Transfer

| Data Classification | Transfer Method |
|--------------------|-----------------|
| Restricted | Encrypted channel only |
| Confidential | Secure channel (TLS 1.2+) |
| Internal | Standard secure protocols |
| Public | No restrictions |

#### 12.3.2 Email Security

| Control | Implementation |
|---------|----------------|
| Encryption | TLS for transport |
| Attachments | Scanning, size limits |
| External email | Warning banner |
| Sensitive data | Encryption required |

### 12.4 Secure Development Communications

| Communication | Security |
|---------------|----------|
| Code repositories | Authenticated access, encrypted |
| CI/CD pipelines | Secured, audit logged |
| API communications | TLS, authentication |
| Secrets management | Vault/encrypted storage |

---

## 13. System Acquisition and Development Policy

### 13.1 Policy Statement
Security shall be integrated into the development lifecycle from requirements through deployment and maintenance.

### 13.2 Security Requirements

#### 13.2.1 Requirements Analysis
All new systems/features shall include:
- Security requirements specification
- Data classification requirements
- Access control requirements
- Compliance requirements

#### 13.2.2 Security by Design
- Threat modeling for new features
- Security architecture review
- Privacy impact assessment (if applicable)

### 13.3 Secure Development

#### 13.3.1 Coding Standards

| Requirement | Implementation |
|-------------|----------------|
| Input validation | Validate all input |
| Output encoding | Prevent injection attacks |
| Authentication | Strong, centralized |
| Session management | Secure tokens, timeouts |
| Error handling | No sensitive data in errors |
| Cryptography | Use approved libraries |

#### 13.3.2 OWASP Top 10 Compliance
All applications shall be protected against:
1. Broken Access Control
2. Cryptographic Failures
3. Injection
4. Insecure Design
5. Security Misconfiguration
6. Vulnerable Components
7. Authentication Failures
8. Integrity Failures
9. Logging Failures
10. Server-Side Request Forgery

### 13.4 Code Review and Testing

| Activity | When | Who |
|----------|------|-----|
| Peer code review | Every PR | Developer |
| Security review | Security-sensitive changes | Security Champion |
| Static analysis | Every build | Automated |
| Dynamic testing | Pre-release | QA |
| Penetration testing | Annual/major release | External |

### 13.5 Deployment Security

| Control | Requirement |
|---------|-------------|
| Environment separation | Dev/Staging/Production |
| Configuration management | Infrastructure as Code |
| Secrets management | No hardcoded secrets |
| Deployment approval | Change management process |
| Rollback capability | Tested rollback procedures |

---

## 14. Supplier Relationship Policy

### 14.1 Policy Statement
Security requirements shall be established and maintained with all suppliers who access, process, or store Orbplus information.

### 14.2 Supplier Selection

#### 14.2.1 Security Assessment

| Supplier Type | Assessment Required |
|---------------|---------------------|
| Cloud/hosting providers | Security questionnaire, certifications |
| Software vendors | Security review, vulnerability history |
| Outsource partners | Background check, security agreement |
| Professional services | NDA, access controls |

#### 14.2.2 Required Certifications/Standards

| Service Type | Preferred Certifications |
|--------------|--------------------------|
| Cloud infrastructure | ISO 27001, SOC 2 Type II |
| Payment processing | PCI DSS |
| Data processing | ISO 27001, GDPR compliance |

### 14.3 Contractual Requirements

All supplier agreements shall include:
- Information security requirements
- Confidentiality obligations
- Data protection requirements
- Right to audit
- Incident notification requirements
- Termination and data return clauses

### 14.4 Ongoing Management

| Activity | Frequency | Responsibility |
|----------|-----------|----------------|
| Performance review | Quarterly | Service Owner |
| Security review | Annual | Security Officer |
| Contract review | Annual | Procurement |
| Incident review | As needed | Security Officer |

### 14.5 Current Supplier Register

| Supplier | Service | Classification | Last Review |
|----------|---------|----------------|-------------|
| INET | Cloud/DevOps | Critical | [Date] |
| TERA | Development | High | [Date] |
| INTENSE | Development | High | [Date] |
| [Cloud Provider] | Infrastructure | Critical | [Date] |

---

## 15. Incident Management Policy

### 15.1 Policy Statement
Security incidents shall be reported, assessed, and responded to in a timely and effective manner to minimize impact and prevent recurrence.

### 15.2 Incident Definition

A security incident is any event that:
- Compromises confidentiality, integrity, or availability
- Violates security policies
- Indicates unauthorized access or misuse
- Could result in harm to the organization

### 15.3 Incident Classification

| Severity | Description | Response Time |
|----------|-------------|---------------|
| **Critical (P1)** | Major breach, system down | 15 minutes |
| **High (P2)** | Significant impact | 1 hour |
| **Medium (P3)** | Limited impact | 4 hours |
| **Low (P4)** | Minimal impact | 24 hours |

### 15.4 Incident Response Process

#### 15.4.1 Response Phases

| Phase | Activities |
|-------|------------|
| **1. Detection** | Identify, report, log incident |
| **2. Assessment** | Classify severity, assign team |
| **3. Containment** | Limit damage, preserve evidence |
| **4. Eradication** | Remove threat, fix vulnerability |
| **5. Recovery** | Restore systems, verify integrity |
| **6. Post-Incident** | Document, lessons learned, improve |

#### 15.4.2 Incident Response Team

| Role | Primary | Backup |
|------|---------|--------|
| Incident Commander | Security Officer | Head of Tech |
| Technical Lead | DevOps Lead | Tech Lead |
| Communications | CEO | Head of Admin |
| Documentation | Security Officer | BA |

### 15.5 Reporting Requirements

| Stakeholder | When to Notify | Method |
|-------------|----------------|--------|
| Management | Critical/High incidents | Immediate call |
| Affected customers | Data breach | Written notification |
| Regulators | As legally required | Formal notification |
| Insurance | Covered incidents | Claim process |

### 15.6 Evidence Preservation

| Evidence Type | Handling |
|---------------|----------|
| System logs | Copy to secure storage |
| Memory dumps | Forensic capture |
| Network captures | Packet capture |
| Physical evidence | Secure, chain of custody |

---

## 16. Business Continuity Policy

### 16.1 Policy Statement
Orbplus shall maintain plans and capabilities to continue critical business operations in the event of disruption.

### 16.2 Business Impact Analysis

#### 16.2.1 Critical Business Functions

| Function | RTO | RPO | Priority |
|----------|-----|-----|----------|
| Customer SaaS access | 4 hours | 15 minutes | Critical |
| Customer support | 8 hours | 4 hours | High |
| Development | 24 hours | 24 hours | Medium |
| Administration | 48 hours | 24 hours | Low |

#### 16.2.2 Recovery Objectives

| Metric | Definition | Target |
|--------|------------|--------|
| **RTO** | Recovery Time Objective | 4 hours |
| **RPO** | Recovery Point Objective | 15 minutes |
| **MTPD** | Maximum Tolerable Period of Disruption | 24 hours |

### 16.3 Continuity Strategies

| Strategy | Implementation |
|----------|----------------|
| Data backup | Multi-region, immutable backups |
| System redundancy | High availability infrastructure |
| DR site | Secondary region capability |
| Alternative work | Remote work capability |
| Communication | Alternative contact methods |

### 16.4 Business Continuity Plan

#### 16.4.1 Plan Components
- Emergency response procedures
- Crisis communication plan
- IT disaster recovery procedures
- Alternative workplace procedures
- Supplier continuity requirements
- Recovery procedures

#### 16.4.2 Testing Schedule

| Test Type | Frequency | Scope |
|-----------|-----------|-------|
| Tabletop exercise | Quarterly | Scenario walkthrough |
| Component testing | Monthly | Individual systems |
| Full DR test | Annual | Complete failover |

### 16.5 Plan Maintenance

| Activity | Frequency |
|----------|-----------|
| Plan review | Annual |
| Contact list update | Quarterly |
| Post-incident review | After each activation |
| Post-test review | After each test |

---

## 17. Compliance Policy

### 17.1 Policy Statement
Orbplus shall identify and comply with all applicable legal, regulatory, and contractual requirements related to information security.

### 17.2 Applicable Requirements

| Requirement | Description | Applicability |
|-------------|-------------|---------------|
| PDPA | Personal Data Protection Act | Customer/employee data |
| ISO 27001:2022 | Information Security Management | ISMS framework |
| Contract obligations | Customer agreements | Service delivery |
| Software licenses | Vendor agreements | Software use |

### 17.3 Compliance Monitoring

| Activity | Frequency | Responsibility |
|----------|-----------|----------------|
| Regulatory review | Quarterly | Security Officer |
| Internal audit | Annual | Internal Auditor |
| External audit | Annual | Certification Body |
| Compliance reporting | Quarterly | Security Officer |

### 17.4 Intellectual Property

| Requirement | Implementation |
|-------------|----------------|
| Software licensing | License inventory, compliance |
| Customer IP | Protection per contract |
| Orbplus IP | Copyright, trade secrets |
| Third-party content | Proper attribution |

### 17.5 Privacy and Data Protection

| Requirement | Control |
|-------------|---------|
| Lawful basis | Document purpose for data collection |
| Data minimization | Collect only necessary data |
| Retention limits | Delete when no longer needed |
| Subject rights | Process requests within timeline |
| Security | Appropriate technical controls |

### 17.6 Audit and Assessment

#### 17.6.1 Internal Audit

| Aspect | Requirement |
|--------|-------------|
| Independence | Auditor independent of audited area |
| Scope | All ISMS controls |
| Frequency | Annual minimum |
| Reporting | To management and Security Committee |

#### 17.6.2 Management Review

| Input | Frequency |
|-------|-----------|
| Audit results | After each audit |
| Incident reports | Quarterly |
| Risk assessment | Annual |
| KPI performance | Quarterly |
| Improvement opportunities | Ongoing |

---

## 18. Policy Review and Maintenance

### 18.1 Review Schedule

| Document Type | Review Frequency | Reviewer |
|---------------|------------------|----------|
| ISMS Policy Manual | Annual | Security Committee |
| SOPs | Annual | Process Owners |
| Risk Assessment | Annual | Security Officer |
| BCP | Annual | Management |

### 18.2 Change Triggers

Policies shall be reviewed when:
- Significant security incidents occur
- Major organizational changes happen
- New regulatory requirements emerge
- Technology changes significantly
- Audit findings require action

### 18.3 Version Control

| Requirement | Implementation |
|-------------|----------------|
| Version numbering | Major.Minor (e.g., 1.0) |
| Change tracking | Document change log |
| Approval | Management sign-off |
| Distribution | Controlled distribution list |
| Archive | Retain previous versions |

### 18.4 Communication

| Audience | Method | Frequency |
|----------|--------|-----------|
| All employees | Policy portal, email | On change |
| New employees | Onboarding | At joining |
| Contractors | Contract attachment | At engagement |
| Management | Security Committee | Quarterly |

---

## 19. Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| Asset | Anything that has value to the organization |
| CIA | Confidentiality, Integrity, Availability |
| Control | Measure that modifies risk |
| ISMS | Information Security Management System |
| Risk | Effect of uncertainty on objectives |
| Threat | Potential cause of unwanted incident |
| Vulnerability | Weakness that can be exploited |

### Appendix B: Document References

| Reference | Description |
|-----------|-------------|
| ISO 27001:2022 | ISMS Requirements |
| ISO 27002:2022 | Security Controls |
| ISO 27005:2022 | Risk Management |
| ISO 22301:2019 | Business Continuity |

### Appendix C: Contact Information

| Role | Contact |
|------|---------|
| Security Officer | [Contact details] |
| IT Support | [Contact details] |
| HR | [Contact details] |
| Emergency | [Contact details] |

### Appendix D: Revision History

| Version | Date | Section | Change Description |
|---------|------|---------|-------------------|
| 1.0 | Jan 2025 | All | Initial release |

---

## Approval

This ISMS Policy Manual has been reviewed and approved by:

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **CEO** | | | |
| **Head of Product & Technology** | | | |
| **Head of Finance & Admin** | | | |
| **Security Officer** | | | |

---

**Document Classification:** Internal
**Distribution:** All Employees

*This document is the property of Orbplus Co., Ltd. and contains confidential information. Unauthorized reproduction or distribution is prohibited.*

---

**End of Document**

*Orbplus Co., Ltd. © 2025 - All Rights Reserved*
