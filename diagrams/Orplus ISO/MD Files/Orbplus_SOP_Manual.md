# Orbplus Standard Operating Procedures (SOP) Manual

**Document ID:** ORB-SOP-2025-001
**Version:** 1.0
**Effective Date:** January 2025
**Classification:** Internal Use Only

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [SOP-01: Access Control Management](#sop-01-access-control-management)
3. [SOP-02: Incident Response](#sop-02-incident-response)
4. [SOP-03: Change Management](#sop-03-change-management)
5. [SOP-04: Backup & Recovery](#sop-04-backup--recovery)
6. [SOP-05: Software Development Lifecycle](#sop-05-software-development-lifecycle)
7. [SOP-06: Code Review Process](#sop-06-code-review-process)
8. [SOP-07: Release Management](#sop-07-release-management)
9. [SOP-08: Customer Onboarding](#sop-08-customer-onboarding)
10. [SOP-09: Support Ticket Handling](#sop-09-support-ticket-handling)
11. [SOP-10: Document Control](#sop-10-document-control)
12. [Appendix: Roles & Responsibilities](#appendix-roles--responsibilities)

---

## 1. Introduction

### 1.1 Purpose
This SOP Manual establishes standardized procedures for Orbplus Co., Ltd. operations to ensure:
- Consistent quality in service delivery
- Compliance with ISO 27001:2022 requirements
- Clear accountability and responsibilities
- Efficient and secure operations

### 1.2 Scope
These procedures apply to all Orbplus employees, contractors, and outsource partners involved in:
- Software development and maintenance
- Customer support and service delivery
- Information security management
- Administrative operations

### 1.3 Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2025 | Management | Initial release |

### 1.4 Definitions

| Term | Definition |
|------|------------|
| SOP | Standard Operating Procedure |
| ISMS | Information Security Management System |
| CI/CD | Continuous Integration/Continuous Deployment |
| SLA | Service Level Agreement |
| RTO | Recovery Time Objective |
| RPO | Recovery Point Objective |

---

## SOP-01: Access Control Management

**Document ID:** ORB-SOP-01
**Owner:** Head of Product & Technology
**Review Cycle:** Annual

### 1. Purpose
To ensure proper management of user access rights to Orbplus systems and data.

### 2. Scope
All systems, applications, and data repositories used by Orbplus.

### 3. Procedure

#### 3.1 New User Access Request

| Step | Action | Responsible | Timeline |
|------|--------|-------------|----------|
| 1 | Submit Access Request Form | Requesting Manager | Day 0 |
| 2 | Verify employment status | HR/Admin | Day 1 |
| 3 | Approve access level | Department Head | Day 1-2 |
| 4 | Create user accounts | System Administrator | Day 2-3 |
| 5 | Assign role-based permissions | System Administrator | Day 2-3 |
| 6 | Provide credentials securely | System Administrator | Day 3 |
| 7 | Conduct security awareness briefing | Security Officer | Day 3-5 |

#### 3.2 Access Modification

| Step | Action | Responsible |
|------|--------|-------------|
| 1 | Submit Change Request Form | Current Manager |
| 2 | Approve role change | New Department Head |
| 3 | Review current permissions | System Administrator |
| 4 | Modify access rights | System Administrator |
| 5 | Update access log | System Administrator |

#### 3.3 Access Revocation (Termination/Transfer)

| Step | Action | Responsible | Timeline |
|------|--------|-------------|----------|
| 1 | HR notifies IT of termination | HR/Admin | Immediately |
| 2 | Disable all user accounts | System Administrator | Within 4 hours |
| 3 | Revoke VPN/Remote access | System Administrator | Within 4 hours |
| 4 | Collect company devices | HR/Admin | Last working day |
| 5 | Transfer data ownership | Department Head | Within 1 week |
| 6 | Archive user data | System Administrator | Within 2 weeks |
| 7 | Document in access log | System Administrator | Same day |

#### 3.4 Periodic Access Review

| Frequency | Scope | Reviewer |
|-----------|-------|----------|
| Monthly | Privileged accounts | Security Officer |
| Quarterly | All user accounts | Department Heads |
| Annually | Complete access audit | External Auditor |

### 4. Access Levels

| Level | Description | Approval Required |
|-------|-------------|-------------------|
| Level 1 - Basic | Read-only access to assigned systems | Supervisor |
| Level 2 - Standard | Read/Write access to assigned systems | Department Head |
| Level 3 - Elevated | Access to sensitive data | Head of Technology |
| Level 4 - Admin | System administration privileges | CEO |
| Level 5 - Super Admin | Full infrastructure access | CEO + Security Officer |

### 5. Records
- Access Request Forms
- Access Modification Logs
- Quarterly Review Reports
- Annual Audit Reports

---

## SOP-02: Incident Response

**Document ID:** ORB-SOP-02
**Owner:** Head of Product & Technology
**Review Cycle:** Annual

### 1. Purpose
To establish a systematic approach for detecting, responding to, and recovering from security incidents.

### 2. Scope
All security incidents affecting Orbplus systems, data, or operations.

### 3. Incident Classification

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| **Critical (P1)** | System down, data breach, major security compromise | 15 minutes | Ransomware, data leak, complete outage |
| **High (P2)** | Significant impact on operations or security | 1 hour | Partial outage, unauthorized access attempt |
| **Medium (P3)** | Limited impact, workaround available | 4 hours | Single user affected, minor vulnerability |
| **Low (P4)** | Minimal impact, informational | 24 hours | Policy violation, suspicious activity |

### 4. Procedure

#### 4.1 Detection & Reporting

| Step | Action | Responsible |
|------|--------|-------------|
| 1 | Identify potential incident | Anyone |
| 2 | Report via Incident Report Form or emergency hotline | Reporter |
| 3 | Log incident in tracking system | IT Support |
| 4 | Assign incident ID and severity | Security Officer |
| 5 | Notify Incident Response Team | Security Officer |

#### 4.2 Assessment & Containment

| Step | Action | Responsible |
|------|--------|-------------|
| 1 | Assess scope and impact | Incident Response Team |
| 2 | Identify affected systems | Technical Lead |
| 3 | Implement containment measures | System Administrator |
| 4 | Preserve evidence | Security Officer |
| 5 | Document all actions taken | Incident Coordinator |

#### 4.3 Eradication & Recovery

| Step | Action | Responsible |
|------|--------|-------------|
| 1 | Identify root cause | Technical Lead |
| 2 | Remove threat/vulnerability | System Administrator |
| 3 | Restore affected systems | System Administrator |
| 4 | Verify system integrity | QA Team |
| 5 | Monitor for recurrence | IT Support |

#### 4.4 Post-Incident Review

| Step | Action | Responsible | Timeline |
|------|--------|-------------|----------|
| 1 | Conduct post-mortem meeting | Incident Response Team | Within 1 week |
| 2 | Document lessons learned | Security Officer | Within 2 weeks |
| 3 | Update procedures if needed | Process Owner | Within 1 month |
| 4 | Implement preventive measures | Technical Lead | As determined |

### 5. Escalation Matrix

| Severity | Notify Immediately | Notify Within 1 Hour |
|----------|-------------------|----------------------|
| Critical | CEO, CTO, Security Officer | All Department Heads, Legal |
| High | CTO, Security Officer | Affected Department Head |
| Medium | Security Officer | Supervisor |
| Low | - | Security Officer (daily report) |

### 6. Communication Templates

**Internal Notification:**
```
INCIDENT ALERT - [Severity Level]
Incident ID: [ID]
Time Detected: [DateTime]
Affected Systems: [List]
Current Status: [Investigating/Contained/Resolved]
Action Required: [Instructions]
```

**Customer Notification (if required):**
```
Dear Valued Customer,

We are writing to inform you of a security incident that may have affected [scope].

What happened: [Brief description]
What we're doing: [Actions taken]
What you should do: [Recommendations]

We apologize for any inconvenience and are committed to protecting your data.

Orbplus Security Team
```

---

## SOP-03: Change Management

**Document ID:** ORB-SOP-03
**Owner:** Head of Product & Technology
**Review Cycle:** Annual

### 1. Purpose
To ensure all changes to systems, applications, and infrastructure are properly planned, tested, approved, and documented.

### 2. Scope
All changes to production systems, including:
- Software updates and patches
- Configuration changes
- Infrastructure modifications
- Database schema changes

### 3. Change Categories

| Category | Description | Approval | Lead Time |
|----------|-------------|----------|-----------|
| **Standard** | Pre-approved, low-risk, routine changes | Auto-approved | 24 hours |
| **Normal** | Planned changes with moderate risk | CAB approval | 5 business days |
| **Emergency** | Urgent changes to resolve critical issues | Emergency CAB | Immediate |

### 4. Procedure

#### 4.1 Change Request Submission

| Step | Action | Responsible |
|------|--------|-------------|
| 1 | Complete Change Request Form (CRF) | Requestor |
| 2 | Define scope, impact, and rollback plan | Requestor |
| 3 | Attach test results (if applicable) | Developer |
| 4 | Submit to Change Manager | Requestor |

#### 4.2 Change Assessment

| Step | Action | Responsible |
|------|--------|-------------|
| 1 | Review CRF for completeness | Change Manager |
| 2 | Assess risk and impact | Technical Reviewer |
| 3 | Verify testing adequacy | QA Lead |
| 4 | Check resource availability | Operations |
| 5 | Categorize change | Change Manager |

#### 4.3 Change Advisory Board (CAB) Review

| Step | Action | Responsible |
|------|--------|-------------|
| 1 | Schedule CAB meeting (Normal changes) | Change Manager |
| 2 | Present change details | Requestor |
| 3 | Discuss risks and mitigation | CAB Members |
| 4 | Vote on approval | CAB Members |
| 5 | Document decision | Change Manager |

**CAB Members:**
- Head of Product & Technology (Chair)
- Technical Lead/Architect
- QA Lead
- Operations Representative
- Security Officer (for security-related changes)

#### 4.4 Change Implementation

| Step | Action | Responsible |
|------|--------|-------------|
| 1 | Schedule implementation window | Change Manager |
| 2 | Notify affected stakeholders | Change Manager |
| 3 | Prepare rollback procedures | Implementer |
| 4 | Execute change | Implementer |
| 5 | Verify successful implementation | QA |
| 6 | Document results | Implementer |

#### 4.5 Post-Implementation Review

| Step | Action | Responsible |
|------|--------|-------------|
| 1 | Monitor for issues (24-72 hours) | Operations |
| 2 | Collect feedback | Change Manager |
| 3 | Close change ticket | Change Manager |
| 4 | Update documentation | Technical Writer |

### 5. Emergency Change Process

| Step | Action | Responsible | Timeline |
|------|--------|-------------|----------|
| 1 | Report emergency | Anyone | Immediate |
| 2 | Emergency CAB approval (verbal) | Available CAB members | 15 minutes |
| 3 | Implement change | Technical Lead | ASAP |
| 4 | Document change retrospectively | Implementer | Within 24 hours |
| 5 | Full CAB review | CAB | Next CAB meeting |

### 6. Change Request Form Contents

- Change ID
- Requestor information
- Change description
- Business justification
- Affected systems
- Risk assessment (High/Medium/Low)
- Impact assessment
- Implementation plan
- Rollback plan
- Testing results
- Required approvals
- Scheduled date/time

---

## SOP-04: Backup & Recovery

**Document ID:** ORB-SOP-04
**Owner:** Cloud/DevOps Engineer
**Review Cycle:** Annual

### 1. Purpose
To ensure business continuity through proper backup procedures and tested recovery processes.

### 2. Scope
All critical systems, databases, and data repositories.

### 3. Backup Strategy

#### 3.1 Backup Schedule

| Data Type | Frequency | Retention | Location |
|-----------|-----------|-----------|----------|
| **Production Database** | Every 6 hours | 30 days | Primary + DR site |
| **Transaction Logs** | Every 15 minutes | 7 days | Primary + DR site |
| **Application Code** | On commit (Git) | Indefinite | GitHub/GitLab |
| **Configuration Files** | Daily | 90 days | Secure backup |
| **User Documents** | Daily | 90 days | Cloud storage |
| **System Images** | Weekly | 4 weeks | DR site |

#### 3.2 Backup Types

| Type | Description | When Used |
|------|-------------|-----------|
| Full Backup | Complete copy of all data | Weekly (Sunday) |
| Incremental | Only changed data since last backup | Daily |
| Differential | Changed data since last full backup | Not used |
| Transaction Log | Database transaction logs | Every 15 minutes |

### 4. Backup Procedure

#### 4.1 Automated Backup Execution

| Step | Action | Responsible |
|------|--------|-------------|
| 1 | Automated backup job triggers | Backup System |
| 2 | Verify backup completion | Monitoring System |
| 3 | Check backup integrity | Backup System |
| 4 | Replicate to DR site | Replication Service |
| 5 | Send status notification | Monitoring System |

#### 4.2 Backup Verification

| Step | Action | Responsible | Frequency |
|------|--------|-------------|-----------|
| 1 | Review backup logs | DevOps Engineer | Daily |
| 2 | Test restore sample data | DevOps Engineer | Weekly |
| 3 | Full recovery test | DevOps Team | Monthly |
| 4 | DR site failover test | DevOps Team | Quarterly |

### 5. Recovery Procedure

#### 5.1 Recovery Objectives

| Metric | Target | Description |
|--------|--------|-------------|
| **RTO** (Recovery Time Objective) | 4 hours | Maximum acceptable downtime |
| **RPO** (Recovery Point Objective) | 15 minutes | Maximum acceptable data loss |

#### 5.2 Recovery Process

| Step | Action | Responsible | Timeline |
|------|--------|-------------|----------|
| 1 | Identify recovery requirement | Incident Manager | Immediate |
| 2 | Assess scope of recovery | DevOps Lead | 15 minutes |
| 3 | Select appropriate backup | DevOps Engineer | 15 minutes |
| 4 | Initiate recovery process | DevOps Engineer | 30 minutes |
| 5 | Verify data integrity | QA Team | 1-2 hours |
| 6 | Restore service | DevOps Team | 2-4 hours |
| 7 | Notify stakeholders | Operations | Ongoing |

#### 5.3 Recovery Scenarios

| Scenario | Recovery Method | Expected Time |
|----------|-----------------|---------------|
| Single file/record | Point-in-time restore | 30 minutes |
| Database corruption | Restore from backup + logs | 2 hours |
| Application failure | Redeploy from repository | 1 hour |
| Complete site failure | Failover to DR site | 4 hours |

### 6. Backup Security

| Control | Description |
|---------|-------------|
| Encryption at rest | AES-256 encryption for all backups |
| Encryption in transit | TLS 1.3 for backup transfers |
| Access control | Limited to authorized personnel only |
| Audit logging | All backup access is logged |
| Offsite storage | DR site in different geographic location |

---

## SOP-05: Software Development Lifecycle

**Document ID:** ORB-SOP-05
**Owner:** Head of Product & Technology
**Review Cycle:** Annual

### 1. Purpose
To establish a consistent and secure software development process.

### 2. Scope
All software development activities for Orbplus products.

### 3. SDLC Phases

#### Phase 1: Requirements

| Step | Action | Responsible | Deliverable |
|------|--------|-------------|-------------|
| 1 | Gather business requirements | Business Analyst | Requirements Document |
| 2 | Define user stories | Product Owner | User Story Backlog |
| 3 | Identify security requirements | Security Officer | Security Requirements |
| 4 | Prioritize backlog | Product Owner | Prioritized Backlog |
| 5 | Estimate effort | Development Team | Story Points |

#### Phase 2: Design

| Step | Action | Responsible | Deliverable |
|------|--------|-------------|-------------|
| 1 | Create technical design | Tech Lead | Design Document |
| 2 | Design database schema | DBA | ERD/Schema |
| 3 | Define API contracts | Tech Lead | API Specification |
| 4 | Security design review | Security Officer | Security Review Report |
| 5 | Design approval | Tech Lead | Approved Design |

#### Phase 3: Development

| Step | Action | Responsible | Deliverable |
|------|--------|-------------|-------------|
| 1 | Create feature branch | Developer | Git Branch |
| 2 | Implement code | Developer | Source Code |
| 3 | Write unit tests | Developer | Test Cases |
| 4 | Self-review code | Developer | Clean Code |
| 5 | Submit pull request | Developer | PR for Review |

#### Phase 4: Code Review

| Step | Action | Responsible | Deliverable |
|------|--------|-------------|-------------|
| 1 | Review code quality | Peer Developer | Review Comments |
| 2 | Check security issues | Security Champion | Security Findings |
| 3 | Verify test coverage | QA Lead | Coverage Report |
| 4 | Approve/Request changes | Reviewer | PR Status |

#### Phase 5: Testing

| Step | Action | Responsible | Deliverable |
|------|--------|-------------|-------------|
| 1 | Run automated tests | CI/CD Pipeline | Test Results |
| 2 | Perform integration testing | QA Team | Integration Report |
| 3 | Execute security testing | Security Team | Security Report |
| 4 | User acceptance testing | Business Analyst | UAT Sign-off |

#### Phase 6: Deployment

| Step | Action | Responsible | Deliverable |
|------|--------|-------------|-------------|
| 1 | Merge to main branch | Tech Lead | Merged Code |
| 2 | Deploy to staging | DevOps | Staging Environment |
| 3 | Final verification | QA Team | Verification Report |
| 4 | Deploy to production | DevOps | Live System |
| 5 | Post-deployment monitoring | Operations | Monitoring Dashboard |

### 4. Development Standards

| Standard | Requirement |
|----------|-------------|
| Version Control | Git with branching strategy |
| Code Style | Follow language-specific style guides |
| Documentation | Inline comments + README |
| Testing | Minimum 80% code coverage |
| Security | OWASP Top 10 compliance |

### 5. Branching Strategy

| Branch | Purpose | Merge To |
|--------|---------|----------|
| `main` | Production-ready code | - |
| `develop` | Integration branch | main |
| `feature/*` | New features | develop |
| `bugfix/*` | Bug fixes | develop |
| `hotfix/*` | Production fixes | main + develop |
| `release/*` | Release preparation | main + develop |

---

## SOP-06: Code Review Process

**Document ID:** ORB-SOP-06
**Owner:** Tech Lead/Architect
**Review Cycle:** Annual

### 1. Purpose
To ensure code quality, security, and knowledge sharing through systematic code reviews.

### 2. Scope
All code changes before merging to shared branches.

### 3. Code Review Checklist

#### 3.1 Functionality

| Item | Check |
|------|-------|
| Code implements requirements correctly | ☐ |
| Edge cases are handled | ☐ |
| Error handling is appropriate | ☐ |
| No obvious bugs | ☐ |

#### 3.2 Code Quality

| Item | Check |
|------|-------|
| Code follows style guidelines | ☐ |
| No code duplication | ☐ |
| Functions are small and focused | ☐ |
| Variable names are meaningful | ☐ |
| Comments explain "why" not "what" | ☐ |

#### 3.3 Security

| Item | Check |
|------|-------|
| Input validation present | ☐ |
| No hardcoded secrets | ☐ |
| SQL injection prevention | ☐ |
| XSS prevention | ☐ |
| Authentication/authorization correct | ☐ |
| Sensitive data handling | ☐ |

#### 3.4 Performance

| Item | Check |
|------|-------|
| No unnecessary database queries | ☐ |
| Efficient algorithms used | ☐ |
| No memory leaks | ☐ |
| Caching considered where appropriate | ☐ |

#### 3.5 Testing

| Item | Check |
|------|-------|
| Unit tests included | ☐ |
| Test coverage adequate | ☐ |
| Tests are meaningful | ☐ |
| Edge cases tested | ☐ |

### 4. Review Process

| Step | Action | Responsible | Timeline |
|------|--------|-------------|----------|
| 1 | Developer creates PR with description | Developer | - |
| 2 | Automated checks run (lint, tests) | CI/CD | Automatic |
| 3 | Assign reviewer(s) | Developer/Lead | Same day |
| 4 | Reviewer examines code | Reviewer | 24-48 hours |
| 5 | Provide feedback/comments | Reviewer | With review |
| 6 | Developer addresses feedback | Developer | 24 hours |
| 7 | Re-review if needed | Reviewer | 24 hours |
| 8 | Approve and merge | Reviewer | After approval |

### 5. Review Guidelines

**For Reviewers:**
- Be constructive and respectful
- Explain the reasoning behind suggestions
- Distinguish between "must fix" and "nice to have"
- Acknowledge good code practices
- Focus on the code, not the person

**For Authors:**
- Provide clear PR description
- Keep PRs small and focused (<400 lines)
- Respond to all comments
- Ask for clarification if needed
- Don't take feedback personally

### 6. Approval Requirements

| Change Type | Minimum Reviewers | Required Approvers |
|-------------|-------------------|--------------------|
| Feature | 1 peer | 1 peer developer |
| Bug fix | 1 peer | 1 peer developer |
| Security-related | 2 reviewers | 1 peer + Security Champion |
| Infrastructure | 2 reviewers | 1 peer + DevOps Lead |
| Database schema | 2 reviewers | 1 peer + DBA |

---

## SOP-07: Release Management

**Document ID:** ORB-SOP-07
**Owner:** Head of Product & Technology
**Review Cycle:** Annual

### 1. Purpose
To ensure controlled and reliable software releases to production.

### 2. Scope
All production releases of Orbplus software products.

### 3. Release Types

| Type | Description | Frequency | Notice Period |
|------|-------------|-----------|---------------|
| **Major** | New features, breaking changes | Quarterly | 2 weeks |
| **Minor** | Enhancements, non-breaking | Monthly | 1 week |
| **Patch** | Bug fixes, security updates | As needed | 24-48 hours |
| **Hotfix** | Critical production fixes | Emergency | Immediate |

### 4. Release Procedure

#### 4.1 Release Planning

| Step | Action | Responsible | Timeline |
|------|--------|-------------|----------|
| 1 | Define release scope | Product Owner | 2 weeks before |
| 2 | Create release branch | Tech Lead | 1 week before |
| 3 | Freeze feature additions | Development Team | 1 week before |
| 4 | Complete release notes | Product Owner | 3 days before |
| 5 | Schedule release window | Release Manager | 3 days before |

#### 4.2 Release Preparation

| Step | Action | Responsible |
|------|--------|-------------|
| 1 | Run full test suite | QA Team |
| 2 | Perform security scan | Security Team |
| 3 | Update documentation | Technical Writer |
| 4 | Prepare rollback plan | DevOps Team |
| 5 | Notify stakeholders | Release Manager |

#### 4.3 Release Execution

| Step | Action | Responsible | Checkpoint |
|------|--------|-------------|------------|
| 1 | Final go/no-go decision | Release Manager | ☐ |
| 2 | Create database backup | DBA | ☐ |
| 3 | Deploy to production | DevOps | ☐ |
| 4 | Run smoke tests | QA Team | ☐ |
| 5 | Verify critical functions | QA Team | ☐ |
| 6 | Monitor system health | Operations | ☐ |
| 7 | Announce release complete | Release Manager | ☐ |

#### 4.4 Post-Release

| Step | Action | Responsible | Timeline |
|------|--------|-------------|----------|
| 1 | Monitor for issues | Operations | 24-72 hours |
| 2 | Collect user feedback | Customer Support | 1 week |
| 3 | Document lessons learned | Release Manager | 1 week |
| 4 | Close release ticket | Release Manager | After stabilization |

### 5. Release Checklist

**Pre-Release:**
- [ ] All features complete and tested
- [ ] Code review approved
- [ ] Security scan passed
- [ ] Performance testing passed
- [ ] Documentation updated
- [ ] Release notes prepared
- [ ] Rollback plan documented
- [ ] Stakeholders notified

**Go-Live:**
- [ ] Backup completed
- [ ] Deployment successful
- [ ] Smoke tests passed
- [ ] Critical functions verified
- [ ] Monitoring active

**Post-Release:**
- [ ] No critical issues reported
- [ ] Performance metrics normal
- [ ] Customer feedback collected
- [ ] Release retrospective completed

### 6. Rollback Procedure

| Step | Action | Responsible | Timeline |
|------|--------|-------------|----------|
| 1 | Identify rollback trigger | Release Manager | Immediate |
| 2 | Notify stakeholders | Release Manager | 5 minutes |
| 3 | Execute rollback script | DevOps | 15-30 minutes |
| 4 | Restore database (if needed) | DBA | 30-60 minutes |
| 5 | Verify system stability | QA Team | 30 minutes |
| 6 | Conduct post-mortem | Release Manager | Within 24 hours |

---

## SOP-08: Customer Onboarding

**Document ID:** ORB-SOP-08
**Owner:** Head of Customer & Sales
**Review Cycle:** Annual

### 1. Purpose
To ensure consistent and efficient onboarding experience for new customers.

### 2. Scope
All new customer subscriptions to Orbplus services.

### 3. Onboarding Process

#### Phase 1: Welcome (Day 0-1)

| Step | Action | Responsible | Deliverable |
|------|--------|-------------|-------------|
| 1 | Send welcome email | Sales/Account Manager | Welcome Package |
| 2 | Schedule kickoff call | Account Manager | Meeting Invite |
| 3 | Create customer account | System Admin | Account Credentials |
| 4 | Assign customer success contact | Customer Support | Contact Assignment |

#### Phase 2: Setup (Day 1-5)

| Step | Action | Responsible | Deliverable |
|------|--------|-------------|-------------|
| 1 | Conduct kickoff meeting | Account Manager | Meeting Notes |
| 2 | Gather configuration requirements | Business Analyst | Configuration Form |
| 3 | Configure customer environment | Technical Team | Configured System |
| 4 | Import initial data (if applicable) | Data Team | Imported Data |
| 5 | Create admin user accounts | System Admin | User Credentials |

#### Phase 3: Training (Day 5-10)

| Step | Action | Responsible | Deliverable |
|------|--------|-------------|-------------|
| 1 | Schedule training sessions | Customer Support | Training Calendar |
| 2 | Conduct admin training | Trainer | Completion Certificate |
| 3 | Conduct end-user training | Trainer | Completion Certificate |
| 4 | Provide training materials | Trainer | User Guides |

#### Phase 4: Go-Live (Day 10-14)

| Step | Action | Responsible | Deliverable |
|------|--------|-------------|-------------|
| 1 | Perform readiness assessment | Account Manager | Readiness Checklist |
| 2 | Go-live support | Customer Support | Support Coverage |
| 3 | Verify system functionality | QA | Verification Report |
| 4 | Confirm customer satisfaction | Account Manager | Satisfaction Survey |

#### Phase 5: Handover (Day 14-30)

| Step | Action | Responsible | Deliverable |
|------|--------|-------------|-------------|
| 1 | Transition to regular support | Account Manager | Handover Document |
| 2 | Schedule first check-in | Customer Success | Meeting Invite |
| 3 | Provide support contact info | Customer Support | Support Guide |
| 4 | Close onboarding ticket | Account Manager | Closed Ticket |

### 4. Onboarding Checklist

- [ ] Contract signed
- [ ] Payment processed
- [ ] Welcome email sent
- [ ] Kickoff call completed
- [ ] Environment configured
- [ ] Data imported
- [ ] Users created
- [ ] Training completed
- [ ] Go-live confirmed
- [ ] Handover completed
- [ ] First check-in scheduled

### 5. Customer Information Requirements

| Information | Required | Purpose |
|-------------|----------|---------|
| Company name | Yes | Account setup |
| Primary contact | Yes | Communication |
| Billing contact | Yes | Invoicing |
| Technical contact | Yes | Technical support |
| Number of users | Yes | Licensing |
| Data import requirements | If applicable | Data migration |
| Integration requirements | If applicable | Technical setup |
| Customization needs | If applicable | Configuration |

---

## SOP-09: Support Ticket Handling

**Document ID:** ORB-SOP-09
**Owner:** Customer Support Lead
**Review Cycle:** Annual

### 1. Purpose
To ensure efficient and consistent handling of customer support requests.

### 2. Scope
All customer support tickets and inquiries.

### 3. Ticket Priority Levels

| Priority | Description | Response Time | Resolution Time |
|----------|-------------|---------------|-----------------|
| **P1 - Critical** | System down, no workaround | 30 minutes | 4 hours |
| **P2 - High** | Major function impaired | 2 hours | 8 hours |
| **P3 - Medium** | Minor function impaired, workaround exists | 4 hours | 24 hours |
| **P4 - Low** | General inquiry, enhancement request | 8 hours | 72 hours |

### 4. Ticket Handling Procedure

#### 4.1 Ticket Receipt & Classification

| Step | Action | Responsible | Timeline |
|------|--------|-------------|----------|
| 1 | Receive ticket (email/portal/phone) | Support Team | - |
| 2 | Log ticket in system | Support Agent | 5 minutes |
| 3 | Classify priority | Support Agent | 5 minutes |
| 4 | Assign to appropriate team | Support Lead | 10 minutes |
| 5 | Send acknowledgment to customer | Support Agent | 15 minutes |

#### 4.2 Investigation & Resolution

| Step | Action | Responsible |
|------|--------|-------------|
| 1 | Review ticket details | Assigned Agent |
| 2 | Gather additional information if needed | Assigned Agent |
| 3 | Investigate issue | Assigned Agent |
| 4 | Escalate if necessary | Assigned Agent |
| 5 | Implement solution | Assigned Agent |
| 6 | Test solution | Assigned Agent |

#### 4.3 Communication & Closure

| Step | Action | Responsible |
|------|--------|-------------|
| 1 | Update customer on progress | Assigned Agent |
| 2 | Provide solution to customer | Assigned Agent |
| 3 | Confirm resolution with customer | Assigned Agent |
| 4 | Document resolution | Assigned Agent |
| 5 | Close ticket | Assigned Agent |
| 6 | Send satisfaction survey | System (auto) |

### 5. Escalation Matrix

| Level | Trigger | Escalate To | Response Time |
|-------|---------|-------------|---------------|
| Level 1 | First contact | Support Agent | Immediate |
| Level 2 | Cannot resolve in 2 hours (P1/P2) | Senior Support | 2 hours |
| Level 3 | Technical complexity | Development Team | 4 hours |
| Level 4 | Customer escalation | Support Manager | Immediate |
| Level 5 | Business impact | Management | Immediate |

### 6. Communication Guidelines

**Initial Response:**
```
Dear [Customer Name],

Thank you for contacting Orbplus Support. We have received your request and assigned ticket number [TICKET-ID].

Priority: [Priority Level]
Expected Response Time: [Time]

We will begin investigating your issue immediately and keep you updated on our progress.

Best regards,
Orbplus Support Team
```

**Progress Update:**
```
Dear [Customer Name],

Update on ticket [TICKET-ID]:

Current Status: [Status]
Actions Taken: [Description]
Next Steps: [Plan]
Expected Resolution: [Time]

Please let us know if you have any questions.

Best regards,
[Agent Name]
```

**Resolution:**
```
Dear [Customer Name],

We are pleased to inform you that ticket [TICKET-ID] has been resolved.

Issue: [Description]
Resolution: [Solution]
Prevention: [If applicable]

If you experience any further issues, please don't hesitate to contact us.

Best regards,
[Agent Name]
```

### 7. SLA Tracking

| Metric | Target | Measurement |
|--------|--------|-------------|
| First Response Time | Meet priority SLA | Time to first response |
| Resolution Time | Meet priority SLA | Time to resolution |
| Customer Satisfaction | > 90% | Survey score |
| First Contact Resolution | > 70% | Tickets resolved on first contact |
| Ticket Reopen Rate | < 5% | Reopened tickets |

---

## SOP-10: Document Control

**Document ID:** ORB-SOP-10
**Owner:** Head of Finance & Admin
**Review Cycle:** Annual

### 1. Purpose
To ensure proper management, control, and security of all company documents.

### 2. Scope
All official Orbplus documents, policies, procedures, and records.

### 3. Document Classification

| Classification | Description | Access | Examples |
|----------------|-------------|--------|----------|
| **Public** | For external distribution | Anyone | Marketing materials, public announcements |
| **Internal** | For all employees | All employees | Policies, procedures, guidelines |
| **Confidential** | Need-to-know basis | Authorized personnel | Customer data, financial reports |
| **Restricted** | Highly sensitive | Named individuals only | Security keys, contracts, HR records |

### 4. Document Lifecycle

#### 4.1 Document Creation

| Step | Action | Responsible |
|------|--------|-------------|
| 1 | Draft document using template | Author |
| 2 | Apply document ID and version | Author |
| 3 | Submit for review | Author |
| 4 | Review and provide feedback | Reviewer |
| 5 | Revise as needed | Author |
| 6 | Approve document | Approver |
| 7 | Publish and distribute | Document Controller |

#### 4.2 Document Review & Update

| Step | Action | Responsible | Frequency |
|------|--------|-------------|-----------|
| 1 | Identify documents for review | Document Controller | Per schedule |
| 2 | Distribute for review | Document Controller | - |
| 3 | Collect feedback | Document Controller | 2 weeks |
| 4 | Update document if needed | Document Owner | - |
| 5 | Re-approve if major changes | Approver | - |
| 6 | Publish updated version | Document Controller | - |

#### 4.3 Document Archival

| Step | Action | Responsible |
|------|--------|-------------|
| 1 | Identify obsolete documents | Document Controller |
| 2 | Mark as obsolete | Document Controller |
| 3 | Remove from active circulation | Document Controller |
| 4 | Transfer to archive | Document Controller |
| 5 | Apply retention period | Document Controller |

### 5. Document Naming Convention

```
[Department]-[Type]-[Subject]-[Version]

Examples:
IT-POL-AccessControl-v1.0
HR-SOP-Onboarding-v2.1
FIN-TMP-ExpenseReport-v1.0
```

**Type Codes:**
| Code | Type |
|------|------|
| POL | Policy |
| SOP | Standard Operating Procedure |
| WI | Work Instruction |
| TMP | Template |
| FRM | Form |
| GDL | Guideline |

### 6. Version Control

| Version Change | Description |
|----------------|-------------|
| Major (X.0) | Significant changes, new sections, restructuring |
| Minor (X.Y) | Small updates, corrections, clarifications |

### 7. Document Retention

| Document Type | Retention Period | After Retention |
|---------------|------------------|-----------------|
| Policies & SOPs | 7 years after obsolete | Archive |
| Financial records | 10 years | Secure destruction |
| Customer contracts | 7 years after termination | Secure destruction |
| HR records | 7 years after termination | Secure destruction |
| Project documents | 5 years after completion | Archive |
| Audit records | 7 years | Archive |

### 8. Document Security

| Classification | Storage | Access Control | Distribution |
|----------------|---------|----------------|--------------|
| Public | Any | None | Unrestricted |
| Internal | Company drives | Employee login | Internal only |
| Confidential | Secure folders | Role-based | Approved list |
| Restricted | Encrypted storage | Named users only | Controlled |

---

## Appendix: Roles & Responsibilities

### Key Roles

| Role | Primary Responsibilities |
|------|-------------------------|
| **CEO** | Overall accountability, final approval authority |
| **Head of Product & Technology** | SDLC, change management, technical decisions |
| **Tech Lead/Architect** | Technical standards, code review, architecture |
| **Security Officer** | Security policies, incident response, audits |
| **QA Lead** | Testing standards, quality assurance |
| **DevOps Lead** | Infrastructure, deployment, backup/recovery |
| **Customer Support Lead** | Support operations, SLA management |
| **Document Controller** | Document management, version control |
| **Change Manager** | Change process, CAB coordination |
| **Release Manager** | Release planning and coordination |

### RACI Matrix for SOPs

| SOP | Responsible | Accountable | Consulted | Informed |
|-----|-------------|-------------|-----------|----------|
| Access Control | IT Admin | Head of Tech | Security Officer | All employees |
| Incident Response | Security Officer | CEO | Legal, Tech | Affected parties |
| Change Management | Change Manager | Head of Tech | CAB | Stakeholders |
| Backup & Recovery | DevOps | Head of Tech | DBA | Operations |
| SDLC | Tech Lead | Head of Tech | QA, Security | Dev Team |
| Code Review | Developers | Tech Lead | QA | Dev Team |
| Release Management | Release Manager | Head of Tech | QA, DevOps | Customers |
| Customer Onboarding | Account Manager | Head of Sales | Support, Tech | Customer |
| Support Tickets | Support Agent | Support Lead | Tech Team | Customer |
| Document Control | Doc Controller | Admin Head | All Owners | All employees |

---

## Document Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Prepared By | | | |
| Reviewed By | | | |
| Approved By | CEO | | |

---

**End of Document**

*Orbplus Co., Ltd. - All Rights Reserved*
