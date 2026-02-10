# Business Continuity Plan (BCP)

**Document ID:** ORB-BCP-2025-001
**Version:** 1.0
**Classification:** Confidential
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
2. [Scope and Objectives](#2-scope-and-objectives)
3. [Business Impact Analysis](#3-business-impact-analysis)
4. [Risk Assessment Summary](#4-risk-assessment-summary)
5. [Recovery Strategy](#5-recovery-strategy)
6. [Emergency Response Procedures](#6-emergency-response-procedures)
7. [Crisis Communication Plan](#7-crisis-communication-plan)
8. [IT Disaster Recovery Plan](#8-it-disaster-recovery-plan)
9. [Business Recovery Procedures](#9-business-recovery-procedures)
10. [Plan Activation](#10-plan-activation)
11. [Roles and Responsibilities](#11-roles-and-responsibilities)
12. [Testing and Maintenance](#12-testing-and-maintenance)
13. [Appendices](#13-appendices)

---

## 1. Introduction

### 1.1 Purpose
This Business Continuity Plan (BCP) establishes the framework for Orbplus Co., Ltd. to:
- Respond effectively to disruptive incidents
- Maintain critical business operations during disruption
- Recover normal operations in a timely manner
- Protect employees, customers, and stakeholders

### 1.2 Plan Objectives

| Objective | Description |
|-----------|-------------|
| **Minimize Impact** | Reduce the impact of disruptions on business operations |
| **Ensure Safety** | Protect employee safety and wellbeing |
| **Maintain Service** | Continue critical services to customers |
| **Rapid Recovery** | Restore normal operations as quickly as possible |
| **Protect Reputation** | Maintain stakeholder confidence |

### 1.3 Plan Activation Triggers

| Trigger | Examples |
|---------|----------|
| **Natural Disaster** | Flood, earthquake, severe weather |
| **Technology Failure** | Major system outage, cyber attack, data center failure |
| **Infrastructure Failure** | Power outage, network failure, building damage |
| **Health Emergency** | Pandemic, outbreak affecting workforce |
| **Security Incident** | Major breach, ransomware, physical security threat |
| **Supplier Failure** | Critical vendor outage, supply chain disruption |

---

## 2. Scope and Objectives

### 2.1 Scope

**In Scope:**
- All Orbplus business operations
- All employees and contractors
- Customer-facing services (SaaS platform)
- IT infrastructure and systems
- Office facilities

**Out of Scope:**
- Customer internal operations
- Third-party systems outside Orbplus control

### 2.2 Recovery Objectives

| Metric | Definition | Target |
|--------|------------|--------|
| **RTO** | Recovery Time Objective - Maximum acceptable downtime | 4 hours |
| **RPO** | Recovery Point Objective - Maximum acceptable data loss | 15 minutes |
| **MTPD** | Maximum Tolerable Period of Disruption | 24 hours |
| **WRT** | Work Recovery Time - Time to restore normal operations | 48 hours |

### 2.3 Critical Success Factors

1. Management commitment and support
2. Adequate resources and budget
3. Regular testing and updates
4. Employee awareness and training
5. Effective communication channels
6. Reliable backup systems

---

## 3. Business Impact Analysis

### 3.1 Critical Business Functions

| Priority | Function | Description | RTO | RPO | Impact if Unavailable |
|----------|----------|-------------|-----|-----|----------------------|
| **P1** | Customer SaaS Platform | Production ERP system access | 4 hrs | 15 min | Revenue loss, customer impact, SLA breach |
| **P1** | Customer Database | Customer data and transactions | 4 hrs | 15 min | Data loss, compliance violation |
| **P2** | Customer Support | Help desk and technical support | 8 hrs | 4 hrs | Customer dissatisfaction, escalations |
| **P2** | Email/Communication | Internal and external communication | 8 hrs | 4 hrs | Communication disruption |
| **P3** | Development Environment | Software development systems | 24 hrs | 24 hrs | Development delays |
| **P3** | Finance/Accounting | Financial operations | 24 hrs | 24 hrs | Payment delays |
| **P4** | HR/Administration | Administrative functions | 48 hrs | 48 hrs | Administrative backlog |

### 3.2 Impact Timeline

| Timeframe | Business Impact | Financial Impact |
|-----------|-----------------|------------------|
| **0-4 hours** | Customer inconvenience, support calls | Minimal |
| **4-8 hours** | SLA breach potential, customer complaints | Moderate |
| **8-24 hours** | Significant customer impact, escalations | High (potential SLA penalties) |
| **24-48 hours** | Major customer loss risk, reputation damage | Severe |
| **>48 hours** | Critical business viability risk | Critical |

### 3.3 Dependencies

| Function | Internal Dependencies | External Dependencies |
|----------|----------------------|----------------------|
| SaaS Platform | Database, Network, DevOps | Cloud Provider (AWS/GCP), Internet |
| Customer Support | Email, CRM, Knowledge Base | Phone System, Ticketing System |
| Development | Source Code Repo, CI/CD | GitHub/GitLab, Cloud Services |
| Finance | Accounting System, Banking | Banks, Payment Processors |

### 3.4 Resource Requirements

| Resource | Normal Operations | Minimum for Continuity |
|----------|-------------------|------------------------|
| Staff | 100% | 50% (critical roles) |
| IT Systems | All systems | P1 and P2 systems |
| Office Space | Full office | Remote work capable |
| Network | Full bandwidth | Basic connectivity |

---

## 4. Risk Assessment Summary

### 4.1 Key Risks to Business Continuity

| Risk | Likelihood | Impact | Risk Level | Mitigation |
|------|------------|--------|------------|------------|
| Cloud provider outage | Medium | Critical | High | Multi-region, DR site |
| Ransomware attack | High | Critical | Critical | Backup, EDR, training |
| Power outage (office) | Medium | Low | Medium | Remote work capability |
| Internet outage | Medium | High | High | Backup ISP, cloud-based |
| Key personnel unavailable | Medium | High | High | Cross-training, documentation |
| Natural disaster | Low | Critical | Medium | Remote work, DR site |
| Pandemic | Low | High | Medium | Remote work policy |
| Cyber attack/breach | High | Critical | Critical | Security controls, IR plan |

### 4.2 Risk Treatment Summary

| Risk Category | Primary Strategy | Secondary Strategy |
|---------------|------------------|-------------------|
| Technology | Redundancy, DR site | Manual workarounds |
| Personnel | Cross-training | Contractors, outsource |
| Facility | Remote work | Alternative site |
| Supplier | Multiple vendors | Internal alternatives |

---

## 5. Recovery Strategy

### 5.1 Overall Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    RECOVERY STRATEGY                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ Primary  │───▶│ Failover │───▶│ Recovery │───▶│  Normal  │  │
│  │   Site   │    │  to DR   │    │ Primary  │    │Operations│  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       │              │               │               │          │
│    Normal         4 hours        24-48 hours      Ongoing      │
│   Operations       RTO             WRT                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Strategy by Function

| Function | Primary Strategy | Backup Strategy | Recovery Site |
|----------|------------------|-----------------|---------------|
| **SaaS Platform** | Multi-AZ deployment | DR region failover | Secondary cloud region |
| **Database** | Real-time replication | Point-in-time recovery | DR site |
| **Customer Support** | Remote work | Outsource partner | Home offices |
| **Development** | Cloud-based tools | Local environments | Remote |
| **Office Operations** | Remote work | Alternative office | Co-working space |

### 5.3 Technology Recovery Strategy

| Component | Strategy | RTO | Details |
|-----------|----------|-----|---------|
| **Application Servers** | Auto-scaling, multi-AZ | 15 min | Automatic failover |
| **Database** | Multi-AZ RDS, read replicas | 15 min | Automatic failover |
| **File Storage** | S3 cross-region replication | 1 hr | Manual switch |
| **DNS** | Route 53 health checks | 5 min | Automatic failover |
| **Email** | Cloud-based (Google) | 0 min | Provider redundancy |
| **VPN** | Backup VPN gateway | 1 hr | Manual configuration |

### 5.4 Alternate Work Arrangements

| Scenario | Strategy | Requirements |
|----------|----------|--------------|
| **Office inaccessible** | Full remote work | Laptop, VPN, internet |
| **Regional outage** | Work from other locations | Laptop, mobile hotspot |
| **Extended disruption** | Co-working spaces | Pre-arranged agreements |

---

## 6. Emergency Response Procedures

### 6.1 Initial Response (First 30 Minutes)

```
┌─────────────────────────────────────────────────────────────────┐
│              INITIAL RESPONSE FLOWCHART                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    ┌─────────────┐                               │
│                    │  Incident   │                               │
│                    │  Detected   │                               │
│                    └──────┬──────┘                               │
│                           │                                      │
│                    ┌──────▼──────┐                               │
│                    │   Assess    │                               │
│                    │   Severity  │                               │
│                    └──────┬──────┘                               │
│                           │                                      │
│           ┌───────────────┼───────────────┐                      │
│           │               │               │                      │
│     ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐               │
│     │   Minor   │   │  Major    │   │ Critical  │               │
│     │  (Local)  │   │ (Limited) │   │  (Wide)   │               │
│     └─────┬─────┘   └─────┬─────┘   └─────┬─────┘               │
│           │               │               │                      │
│     Normal Ops      Notify CMT      Activate BCP                │
│     Response       Limited Response  Full Response               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Emergency Response Checklist

#### Step 1: Immediate Actions (0-15 minutes)

| # | Action | Responsible | Complete |
|---|--------|-------------|----------|
| 1 | Ensure employee safety | All managers | ☐ |
| 2 | Assess the situation | First responder | ☐ |
| 3 | Contact emergency services if needed | First responder | ☐ |
| 4 | Notify Incident Commander | First responder | ☐ |
| 5 | Secure the area if necessary | Facilities | ☐ |

#### Step 2: Assessment (15-30 minutes)

| # | Action | Responsible | Complete |
|---|--------|-------------|----------|
| 6 | Determine incident severity | Incident Commander | ☐ |
| 7 | Identify affected systems/functions | Technical Lead | ☐ |
| 8 | Estimate impact duration | Technical Lead | ☐ |
| 9 | Decide on BCP activation level | Incident Commander | ☐ |
| 10 | Notify Crisis Management Team | Incident Commander | ☐ |

#### Step 3: Activation (30-60 minutes)

| # | Action | Responsible | Complete |
|---|--------|-------------|----------|
| 11 | Convene Crisis Management Team | CMT Lead | ☐ |
| 12 | Activate relevant recovery procedures | CMT | ☐ |
| 13 | Establish communication channels | Communications Lead | ☐ |
| 14 | Notify affected stakeholders | Communications Lead | ☐ |
| 15 | Begin recovery operations | Recovery Teams | ☐ |

### 6.3 Emergency Contact Procedures

| Situation | Contact | Method |
|-----------|---------|--------|
| **Life Safety Emergency** | Emergency Services | Call 191 (Police), 1669 (Ambulance) |
| **Building Emergency** | Building Management | Call building security |
| **IT Emergency** | On-call DevOps | PagerDuty / Phone |
| **Security Incident** | Security Officer | Phone / Signal |
| **Management Escalation** | CEO | Phone / WhatsApp |

---

## 7. Crisis Communication Plan

### 7.1 Communication Objectives

1. Provide accurate and timely information
2. Maintain stakeholder confidence
3. Coordinate response activities
4. Manage media and public relations
5. Document communications for records

### 7.2 Stakeholder Communication Matrix

| Stakeholder | Information Needed | Method | Frequency | Responsible |
|-------------|-------------------|--------|-----------|-------------|
| **Employees** | Safety, work status, instructions | Email, LINE, Meeting | Immediate + hourly | HR Lead |
| **Customers** | Service status, expected recovery | Email, Status page, Portal | Immediate + updates | Customer Success |
| **Management** | Full situation, decisions needed | Phone, Meeting | Immediate + hourly | CMT Lead |
| **Suppliers** | Impact, requirements | Email, Phone | As needed | Procurement |
| **Media** | Official statement only | Press release | As needed | CEO only |
| **Regulators** | Compliance notifications | Official letter | As required | Legal/Compliance |

### 7.3 Communication Templates

#### Template 1: Initial Customer Notification

```
Subject: Service Disruption Notification - Orbplus

Dear Valued Customer,

We are currently experiencing a service disruption affecting
[affected services]. Our team is actively working to restore
normal operations.

Current Status: [Investigating/Identified/Recovering]
Estimated Recovery: [Time estimate or "being determined"]
Impact: [Brief description of impact]

We will provide updates every [30 minutes/hour] until the
issue is resolved.

For urgent matters, please contact: [emergency contact]

We apologize for any inconvenience and appreciate your patience.

Orbplus Support Team
```

#### Template 2: Status Update

```
Subject: Service Update - [Time] - Orbplus

Status Update: [Investigating/Identified/Monitoring/Resolved]

Current Situation:
[Brief description of current state]

Actions Taken:
- [Action 1]
- [Action 2]

Next Update: [Time]

Thank you for your patience.
```

#### Template 3: Resolution Notification

```
Subject: Service Restored - Orbplus

Dear Valued Customer,

We are pleased to inform you that the service disruption
reported on [date/time] has been resolved.

Incident Summary:
- Duration: [Start time] to [End time]
- Cause: [Brief root cause]
- Resolution: [What was done]

Preventive Measures:
[Brief description of prevention steps]

We apologize for any inconvenience caused. If you experience
any issues, please contact our support team.

Orbplus Support Team
```

### 7.4 Communication Channels

| Channel | Use Case | Primary | Backup |
|---------|----------|---------|--------|
| **Internal - Urgent** | Emergency notifications | LINE Group | Phone tree |
| **Internal - Updates** | Status updates | Email | Slack |
| **Customer - Status** | Service status | Status page | Email |
| **Customer - Support** | Individual queries | Support portal | Email |
| **External - Media** | Press statements | Press release | Website |

### 7.5 Spokesperson Authority

| Audience | Authorized Spokesperson | Backup |
|----------|------------------------|--------|
| Media/Press | CEO only | None (no comment) |
| Customers | Customer Success Lead | Support Manager |
| Employees | HR Lead | Department Heads |
| Regulators | CEO / Legal | Security Officer |
| Partners/Suppliers | Head of Operations | Procurement |

---

## 8. IT Disaster Recovery Plan

### 8.1 IT Recovery Priorities

| Priority | Systems | RTO | Recovery Method |
|----------|---------|-----|-----------------|
| **P1** | Production Database | 15 min | Multi-AZ failover |
| **P1** | Application Servers | 15 min | Auto-scaling |
| **P1** | Load Balancers | 5 min | Health check failover |
| **P2** | File Storage | 1 hr | Cross-region restore |
| **P2** | Email System | 0 min | Cloud provider (Google) |
| **P2** | VPN Gateway | 1 hr | Backup gateway |
| **P3** | Development Systems | 24 hr | Rebuild from backup |
| **P3** | Internal Tools | 24 hr | Cloud-based alternatives |

### 8.2 DR Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DR ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   PRIMARY REGION                    DR REGION                    │
│   ┌─────────────┐                  ┌─────────────┐              │
│   │   Users     │                  │   Users     │              │
│   └──────┬──────┘                  └──────┬──────┘              │
│          │                                │                      │
│   ┌──────▼──────┐    DNS Failover  ┌──────▼──────┐              │
│   │     CDN     │◄────────────────►│     CDN     │              │
│   └──────┬──────┘                  └──────┬──────┘              │
│          │                                │                      │
│   ┌──────▼──────┐                  ┌──────▼──────┐              │
│   │    Load     │                  │    Load     │              │
│   │  Balancer   │                  │  Balancer   │              │
│   └──────┬──────┘                  └──────┬──────┘              │
│          │                                │                      │
│   ┌──────▼──────┐                  ┌──────▼──────┐              │
│   │ App Servers │                  │ App Servers │              │
│   │  (Active)   │                  │  (Standby)  │              │
│   └──────┬──────┘                  └──────┬──────┘              │
│          │                                │                      │
│   ┌──────▼──────┐   Replication    ┌──────▼──────┐              │
│   │  Database   │─────────────────►│  Database   │              │
│   │  (Primary)  │                  │  (Replica)  │              │
│   └─────────────┘                  └─────────────┘              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 Backup Schedule

| Data Type | Method | Frequency | Retention | Location |
|-----------|--------|-----------|-----------|----------|
| Database - Full | Automated snapshot | Daily 2 AM | 30 days | Primary + DR |
| Database - Incremental | Transaction logs | Every 15 min | 7 days | Primary + DR |
| Application Code | Git repository | On commit | Indefinite | GitHub + Local |
| Configuration | Encrypted backup | Daily | 90 days | S3 + DR |
| User Files | Incremental | Hourly | 30 days | S3 cross-region |
| System Images | AMI/Snapshot | Weekly | 4 weeks | Both regions |

### 8.4 Recovery Procedures

#### Procedure 1: Database Failover

| Step | Action | Command/Tool | Time |
|------|--------|--------------|------|
| 1 | Verify primary failure | Health checks | Auto |
| 2 | Promote read replica | AWS Console / CLI | 5 min |
| 3 | Update connection strings | Parameter Store | 2 min |
| 4 | Verify application connectivity | Health checks | 5 min |
| 5 | Monitor for issues | CloudWatch | Ongoing |

#### Procedure 2: Full Region Failover

| Step | Action | Responsible | Time |
|------|--------|-------------|------|
| 1 | Confirm primary region failure | DevOps Lead | 5 min |
| 2 | Notify CMT of failover | DevOps Lead | 2 min |
| 3 | Update DNS to DR region | DevOps | 5 min |
| 4 | Verify DR systems active | DevOps | 10 min |
| 5 | Scale up DR resources | DevOps | 15 min |
| 6 | Confirm service restoration | QA | 10 min |
| 7 | Notify stakeholders | Communications | 5 min |
| **Total** | | | **~52 min** |

#### Procedure 3: Data Restoration

| Step | Action | Time |
|------|--------|------|
| 1 | Identify recovery point | 5 min |
| 2 | Select appropriate backup | 5 min |
| 3 | Restore database to point-in-time | 30-60 min |
| 4 | Verify data integrity | 15 min |
| 5 | Reconnect applications | 10 min |
| 6 | Validate functionality | 15 min |

### 8.5 DR Testing Schedule

| Test Type | Frequency | Duration | Scope |
|-----------|-----------|----------|-------|
| Backup Verification | Weekly | 30 min | Sample data restore |
| Component Failover | Monthly | 2 hrs | Individual component |
| Full DR Failover | Quarterly | 4 hrs | Complete region failover |
| Tabletop Exercise | Quarterly | 2 hrs | Scenario walkthrough |

---

## 9. Business Recovery Procedures

### 9.1 Customer Service Recovery

| Step | Action | Responsible | Timeframe |
|------|--------|-------------|-----------|
| 1 | Activate remote support capability | Support Lead | 0-30 min |
| 2 | Update support channels status | Support Lead | 30 min |
| 3 | Prioritize critical customer issues | Support Team | Ongoing |
| 4 | Enable backup communication channels | IT Support | 1 hr |
| 5 | Resume normal support operations | Support Lead | When stable |

### 9.2 Financial Operations Recovery

| Step | Action | Responsible | Timeframe |
|------|--------|-------------|-----------|
| 1 | Secure access to banking systems | Finance Head | 0-1 hr |
| 2 | Verify accounting system access | Finance Team | 1-2 hr |
| 3 | Process critical payments | Finance Team | 2-4 hr |
| 4 | Resume normal financial operations | Finance Head | 24 hr |

### 9.3 Development Operations Recovery

| Step | Action | Responsible | Timeframe |
|------|--------|-------------|-----------|
| 1 | Verify code repository access | Tech Lead | 0-1 hr |
| 2 | Restore development environments | DevOps | 2-4 hr |
| 3 | Verify CI/CD pipeline | DevOps | 4-8 hr |
| 4 | Resume development activities | Tech Lead | 24 hr |

### 9.4 Return to Normal Operations

| Phase | Activities | Criteria for Completion |
|-------|------------|------------------------|
| **Stabilization** | Monitor systems, handle issues | No critical issues for 4 hrs |
| **Verification** | Full system testing | All functions operational |
| **Failback** | Return to primary site (if applicable) | Primary site ready |
| **Post-Incident** | Documentation, lessons learned | Report completed |
| **Closure** | Stand down, normal operations | Management approval |

---

## 10. Plan Activation

### 10.1 Activation Levels

| Level | Trigger | Response | Authority |
|-------|---------|----------|-----------|
| **Level 1 - Alert** | Potential disruption identified | Monitor, prepare | Department Head |
| **Level 2 - Partial** | Limited disruption, single function affected | Limited recovery | Security Officer |
| **Level 3 - Full** | Major disruption, multiple functions affected | Full BCP activation | CEO |

### 10.2 Activation Decision Tree

```
                    ┌─────────────────┐
                    │ Incident Occurs │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Is there impact │
                    │ to operations?  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │ No           │ Yes          │
              ▼              ▼              │
        ┌─────────┐   ┌─────────────┐       │
        │ Monitor │   │ Duration >  │       │
        │  Only   │   │  4 hours?   │       │
        └─────────┘   └──────┬──────┘       │
                             │              │
              ┌──────────────┼──────────────┤
              │ No           │ Yes          │
              ▼              ▼              │
        ┌───────────┐  ┌───────────┐        │
        │  Level 1  │  │ Multiple  │        │
        │   Alert   │  │ functions?│        │
        └───────────┘  └─────┬─────┘        │
                             │              │
              ┌──────────────┼──────────────┤
              │ No           │ Yes          │
              ▼              ▼              │
        ┌───────────┐  ┌───────────┐        │
        │  Level 2  │  │  Level 3  │        │
        │  Partial  │  │   Full    │        │
        └───────────┘  └───────────┘        │
```

### 10.3 Activation Checklist

| # | Action | Responsible | Complete |
|---|--------|-------------|----------|
| 1 | Confirm incident severity and scope | Incident Commander | ☐ |
| 2 | Determine activation level | Incident Commander | ☐ |
| 3 | Notify Crisis Management Team | Incident Commander | ☐ |
| 4 | Convene CMT meeting (virtual or physical) | CMT Lead | ☐ |
| 5 | Assign recovery team roles | CMT Lead | ☐ |
| 6 | Activate relevant recovery procedures | Recovery Teams | ☐ |
| 7 | Establish communication schedule | Communications Lead | ☐ |
| 8 | Document activation time and decisions | CMT Secretary | ☐ |

---

## 11. Roles and Responsibilities

### 11.1 Crisis Management Team (CMT)

| Role | Primary | Backup | Responsibilities |
|------|---------|--------|------------------|
| **CMT Lead** | CEO | Head of Tech | Overall coordination, decisions |
| **Incident Commander** | Security Officer | DevOps Lead | Technical response coordination |
| **Communications Lead** | Head of Admin | HR Lead | Stakeholder communications |
| **IT Recovery Lead** | DevOps Lead | Tech Lead | IT systems recovery |
| **Business Recovery Lead** | Head of Tech | Product Owner | Business operations recovery |
| **Finance Lead** | Finance Head | Accounting | Financial matters |
| **HR Lead** | HR Manager | Admin | Employee welfare |
| **CMT Secretary** | BA | Support Lead | Documentation, logistics |

### 11.2 Recovery Teams

| Team | Lead | Members | Responsibility |
|------|------|---------|----------------|
| **IT Recovery** | DevOps Lead | DevOps, DBA | Infrastructure, systems recovery |
| **Application Recovery** | Tech Lead | Developers | Application restoration |
| **Customer Support** | Support Lead | Support Team | Customer communication, support |
| **Business Operations** | Head of Admin | Admin Staff | Office, logistics, HR |

### 11.3 Responsibilities Matrix

| Activity | CMT Lead | IC | IT Lead | Comms Lead | Business Lead |
|----------|----------|----|---------|-----------| --------------|
| Declare activation | A | R | C | I | I |
| Technical recovery | I | A | R | I | I |
| Stakeholder communication | A | I | C | R | C |
| Resource allocation | A | C | R | C | R |
| Decision making | A | R | C | C | C |
| Documentation | I | C | C | C | R |

*A=Accountable, R=Responsible, C=Consulted, I=Informed*

---

## 12. Testing and Maintenance

### 12.1 Testing Schedule

| Test Type | Frequency | Duration | Participants | Objective |
|-----------|-----------|----------|--------------|-----------|
| **Tabletop Exercise** | Quarterly | 2 hours | CMT | Decision-making, coordination |
| **Component Test** | Monthly | 2 hours | IT Team | Individual system recovery |
| **Functional Test** | Quarterly | 4 hours | Recovery Teams | Function-specific recovery |
| **Full DR Test** | Annual | 1 day | All Teams | Complete failover |
| **Communication Test** | Quarterly | 30 min | All Staff | Contact tree, channels |

### 12.2 Test Scenarios

| Scenario | Type | Objectives |
|----------|------|------------|
| **Cloud Region Failure** | Full DR | Test complete failover to DR |
| **Ransomware Attack** | Tabletop | Test response and recovery decisions |
| **Database Corruption** | Component | Test point-in-time recovery |
| **Office Inaccessible** | Functional | Test remote work activation |
| **Key Personnel Unavailable** | Tabletop | Test backup personnel procedures |
| **Supplier Failure** | Tabletop | Test alternate supplier activation |

### 12.3 Test Documentation

| Document | Purpose | Retention |
|----------|---------|-----------|
| Test Plan | Define test scope and objectives | 3 years |
| Test Script | Step-by-step procedures | 3 years |
| Test Results | Actual outcomes and metrics | 3 years |
| Lessons Learned | Improvement opportunities | 3 years |
| Action Items | Follow-up tasks | Until closed |

### 12.4 Plan Maintenance

| Activity | Frequency | Responsible |
|----------|-----------|-------------|
| Review and update BCP | Annual | Security Officer |
| Update contact lists | Quarterly | HR Lead |
| Review recovery procedures | Semi-annual | IT Lead |
| Update risk assessment | Annual | Security Officer |
| Post-incident review | After each activation | CMT Lead |
| Post-test review | After each test | Test Lead |

### 12.5 Change Triggers

Plan must be reviewed when:
- Significant organizational changes
- New critical systems or processes
- Lessons learned from incidents or tests
- Changes in recovery objectives
- New regulatory requirements
- Supplier or technology changes

---

## 13. Appendices

### Appendix A: Emergency Contact List

#### Crisis Management Team

| Role | Name | Phone | Email | Backup Phone |
|------|------|-------|-------|--------------|
| CMT Lead (CEO) | | | | |
| Security Officer | | | | |
| Head of Tech | | | | |
| Head of Admin | | | | |
| DevOps Lead | | | | |
| Support Lead | | | | |

#### External Contacts

| Organization | Contact | Phone | Purpose |
|--------------|---------|-------|---------|
| Emergency Services | | 191 / 1669 | Police / Ambulance |
| Building Security | | | Facility emergency |
| Cloud Provider Support | | | Infrastructure issues |
| ISP Support | | | Network issues |
| Insurance Provider | | | Claims |
| Legal Counsel | | | Legal matters |

### Appendix B: Critical System Information

| System | URL/Access | Admin Contact | Recovery Priority |
|--------|------------|---------------|-------------------|
| Production Database | | DevOps | P1 |
| Application Servers | | DevOps | P1 |
| Customer Portal | | DevOps | P1 |
| Email (Google) | | IT Admin | P2 |
| GitHub/GitLab | | Tech Lead | P3 |
| Accounting System | | Finance | P3 |

### Appendix C: Alternate Site Information

| Site Type | Location | Capacity | Contact | Activation Time |
|-----------|----------|----------|---------|-----------------|
| DR Region | [Cloud Region] | Full capacity | DevOps | < 1 hour |
| Co-working Space | [Location] | 10 people | [Contact] | 24 hours |
| Home Offices | Various | Full staff | HR | Immediate |

### Appendix D: Vendor Contact Information

| Vendor | Service | Support Contact | Account Number |
|--------|---------|-----------------|----------------|
| [Cloud Provider] | Infrastructure | | |
| [ISP] | Internet | | |
| [Domain Registrar] | DNS | | |
| [Backup Provider] | Backup | | |

### Appendix E: Recovery Checklists

#### IT Systems Recovery Checklist

| # | System | Action | Status | Notes |
|---|--------|--------|--------|-------|
| 1 | DNS | Verify/update records | ☐ | |
| 2 | Load Balancer | Verify health checks | ☐ | |
| 3 | Application | Verify deployment | ☐ | |
| 4 | Database | Verify replication | ☐ | |
| 5 | Monitoring | Verify alerts | ☐ | |
| 6 | Backup | Verify last backup | ☐ | |

#### Business Recovery Checklist

| # | Function | Action | Status | Notes |
|---|----------|--------|--------|-------|
| 1 | Communication | Establish channels | ☐ | |
| 2 | Customer Support | Activate remote support | ☐ | |
| 3 | Staff | Account for all employees | ☐ | |
| 4 | Suppliers | Notify critical suppliers | ☐ | |
| 5 | Finance | Secure financial access | ☐ | |

### Appendix F: Document Revision History

| Version | Date | Section | Change | Author |
|---------|------|---------|--------|--------|
| 1.0 | Jan 2025 | All | Initial release | Security Officer |

---

## Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Prepared By** | Security Officer | | |
| **Reviewed By** | Head of Product & Technology | | |
| **Approved By** | CEO | | |

---

**Document Classification:** Confidential
**Distribution:** Crisis Management Team, Recovery Team Leads
**Storage:** Secure location + offline copies

---

**End of Document**

*Orbplus Co., Ltd. © 2025 - All Rights Reserved*
