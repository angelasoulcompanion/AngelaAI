# Data Governance Framework for EWG Phase#0

> **Document Version:** 1.0
> **Date:** January 13, 2026
> **Purpose:** Comprehensive framework for Data Governance, Data Policy, and Time of Data Capture
> **Audience:** C-Level Executives, Data Management Team, IT Leadership

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Data Governance Framework](#2-data-governance-framework)
3. [Data Policy Framework](#3-data-policy-framework)
4. [Time of Data Capture](#4-time-of-data-capture)
5. [Period-End Close Policy (Listed Company)](#5-period-end-close-policy-listed-company)
6. [Water Volume Data Consolidation (SSOT)](#6-water-volume-data-consolidation-ssot)
7. [Reference Framework: DAMA-DMBOK](#7-reference-framework-dama-dmbok)
8. [Implementation Roadmap](#8-implementation-roadmap)
9. [Appendix: Diagrams](#9-appendix-diagrams)
10. [References](#references)

---

## 1. Executive Summary

### 1.1 Purpose

This document establishes the theoretical foundation and practical framework for implementing Data Governance at EWG. It addresses three critical areas identified during C-Level interviews:

| Area | Focus | Business Value |
|------|-------|----------------|
| **Data Governance** | Authority and decision-making over data | Strategic asset management |
| **Data Policy** | Rules and standards for data handling | Compliance and consistency |
| **Time of Data Capture** | Data freshness and timeliness | Accurate decision-making |

### 1.2 Key Outcomes for Phase#0

- Establish governance structure with clear roles and responsibilities
- Define policy framework covering quality, security, access, and retention
- Document timeliness requirements for critical data domains
- Create roadmap for governance implementation

---

## 2. Data Governance Framework

### 2.1 Definition

**Data Governance** is the exercise of authority, control, and shared decision-making over the management of data assets. It ensures data is treated as a strategic enterprise asset with proper accountability.

> *"Data Governance is the business foundation of data management - changing behavior to ensure the delivery of trusted and valuable information."*
> — DAMA International

### 2.2 Core Objectives

| # | Objective | Description | Business Impact |
|---|-----------|-------------|-----------------|
| 1 | **Data Quality & Reliability** | Ensure accuracy, completeness, consistency | Trustworthy analytics and reporting |
| 2 | **Security & Privacy** | Protect sensitive information | Risk mitigation, regulatory compliance |
| 3 | **Regulatory Compliance** | Maintain auditable controls | Avoid penalties, build stakeholder trust |
| 4 | **Decision Enablement** | Improve data discoverability | Faster, data-driven decisions |
| 5 | **Operational Efficiency** | Reduce redundant efforts | Cost savings, productivity gains |

### 2.3 The Four Pillars

Data Governance rests on four foundational pillars that must work together:

![Data Governance 4 Pillars](./diagrams/01_data_governance_4_pillars.drawio.svg)

#### 2.3.1 People

| Role | Responsibility | Accountability Level |
|------|----------------|---------------------|
| **Data Governance Council** | Set strategy, approve policies, resolve escalations | Strategic |
| **Data Owner** | Accountable for domain-level quality and business value | Business |
| **Data Steward** | Day-to-day quality management and policy enforcement | Operational |
| **Data Custodian** | Technical implementation of controls and infrastructure | Technical |
| **Data Product Manager** | Ensure data products meet user needs | Delivery |

#### 2.3.2 Process

| Process Area | Description | Key Activities |
|--------------|-------------|----------------|
| **Lifecycle Management** | Manage data from creation to disposal | Creation, storage, archival, deletion |
| **Issue Resolution** | Handle data quality and access issues | Incident tracking, root cause analysis |
| **Change Management** | Control changes to data structures | Impact assessment, approval workflows |
| **Quality Assurance** | Maintain data fitness for use | Profiling, validation, remediation |

#### 2.3.3 Technology

| Technology Component | Purpose | Examples |
|---------------------|---------|----------|
| **Data Catalog** | Inventory and discovery | Alation, Collibra, Atlan |
| **Lineage Mapping** | Track data flow and transformations | dbt, Apache Atlas |
| **Access Controls** | Manage permissions | IAM, RBAC systems |
| **Quality Monitoring** | Automated quality checks | Great Expectations, dbt tests |

#### 2.3.4 Policy

| Policy Type | Scope | Key Elements |
|-------------|-------|--------------|
| **Classification** | Data sensitivity levels | Public, Internal, Confidential, Restricted |
| **Quality Standards** | Acceptable data quality | Accuracy thresholds, completeness rules |
| **Access Rules** | Who can access what | Role-based access, approval workflows |
| **Retention Rules** | Data lifecycle duration | Retention periods, archival, deletion |

### 2.4 Governance Operating Model

#### RACI Matrix Template

| Activity | Governance Council | Data Owner | Data Steward | Data Custodian |
|----------|-------------------|------------|--------------|----------------|
| Set data strategy | **A** | C | I | I |
| Approve policies | **A** | R | C | I |
| Define quality rules | C | **A** | R | I |
| Implement controls | I | C | C | **R/A** |
| Monitor compliance | I | **A** | R | C |
| Resolve escalations | **A** | R | C | I |

> **Legend:** R = Responsible, A = Accountable, C = Consulted, I = Informed

---

## 3. Data Policy Framework

### 3.1 Definition

**Data Policy** is a formal document that defines how an organization governs, manages, and uses its data assets. It provides enforceable rules that all stakeholders must follow.

### 3.2 Policy Hierarchy

![Data Policy Hierarchy](./diagrams/02_data_policy_hierarchy.drawio.svg)

| Level | Document Type | Description | Example |
|-------|---------------|-------------|---------|
| 1 | **Enterprise Data Policy** | High-level principles and strategic direction | "Data is a strategic asset" |
| 2 | **Data Standards** | Technical specifications for implementation | "All dates use ISO 8601 format" |
| 3 | **Data Procedures** | Step-by-step operational instructions | "How to request data access" |
| 4 | **Data Guidelines** | Best practices and recommendations | "Recommended naming conventions" |

### 3.3 Core Policy Domains

#### 3.3.1 Data Classification Policy

| Classification | Description | Examples | Handling Requirements |
|----------------|-------------|----------|----------------------|
| **Public** | No restrictions on disclosure | Marketing materials, public reports | Standard controls |
| **Internal** | For business use only | Internal processes, operational metrics | Employee access only |
| **Confidential** | Sensitive business information | Financial data, strategic plans | Need-to-know, encryption |
| **Restricted** | Highly sensitive, regulated | PII, health records, credentials | Strict controls, audit logging |

#### 3.3.2 Data Quality Policy

| Dimension | Definition | Measurement | Target |
|-----------|------------|-------------|--------|
| **Accuracy** | Data correctly represents reality | Error rate | < 1% |
| **Completeness** | Required data is present | Null ratio | > 99% |
| **Consistency** | Data agrees across systems | Discrepancy count | 0 |
| **Timeliness** | Data is current when needed | Data age | Per SLA |
| **Validity** | Data conforms to rules | Validation pass rate | 100% |
| **Uniqueness** | No unwanted duplicates | Duplicate ratio | < 0.1% |

#### 3.3.3 Data Access Policy

| Access Level | Who | What | How |
|--------------|-----|------|-----|
| **Open** | All employees | Public data | Self-service |
| **Controlled** | Department members | Internal data | Manager approval |
| **Restricted** | Specific roles | Confidential data | Data owner approval |
| **Privileged** | Named individuals | Restricted data | Governance council approval |

#### 3.3.4 Data Retention Policy

| Data Category | Active Period | Archive Period | Total Retention | Disposal Method |
|---------------|---------------|----------------|-----------------|-----------------|
| **Transactional** | 2 years | 5 years | 7 years | Secure deletion |
| **Customer PII** | Active relationship | +3 years | Per consent | Anonymization/deletion |
| **Financial Records** | 1 year | 9 years | 10 years | Certified destruction |
| **Audit Logs** | 1 year | 6 years | 7 years | Secure deletion |
| **Analytics** | 3 years | 2 years | 5 years | Aggregation/deletion |

#### 3.3.5 Data Security Policy

| Control Area | Requirements | Implementation |
|--------------|--------------|----------------|
| **Encryption at Rest** | AES-256 for Confidential+ | Database encryption, disk encryption |
| **Encryption in Transit** | TLS 1.2+ required | HTTPS, secure protocols |
| **Access Authentication** | MFA for Confidential+ | SSO with MFA |
| **Audit Logging** | All access logged | Centralized log management |
| **Data Masking** | PII masked in non-prod | Dynamic data masking |

#### 3.3.6 Data Sharing Policy

| Sharing Type | Requirements | Approval |
|--------------|--------------|----------|
| **Internal - Same Domain** | Purpose documented | Data Steward |
| **Internal - Cross Domain** | DUA required | Data Owner |
| **External - Partners** | Contract + DPA | Legal + Data Owner |
| **External - Public** | Anonymization verified | Governance Council |

> **DUA** = Data Use Agreement, **DPA** = Data Processing Agreement

#### 3.3.7 Data Privacy Policy

| Requirement | Description | Implementation |
|-------------|-------------|----------------|
| **Consent Management** | Track and honor consent | Consent database |
| **Data Subject Rights** | Enable access, correction, deletion | Self-service portal |
| **Data Minimization** | Collect only what's needed | Collection review |
| **Purpose Limitation** | Use only for stated purpose | Usage tracking |
| **Cross-Border Transfer** | Ensure adequate protection | Transfer mechanisms (SCCs) |

---

## 4. Time of Data Capture

### 4.1 Core Concepts

![Time of Data Capture Flow](./diagrams/03_time_of_data_capture_flow.drawio.svg)

#### 4.1.1 Key Definitions

| Concept | Definition | Formula/Measurement |
|---------|------------|---------------------|
| **Data Timeliness** | Degree to which data is available when needed | Event → Available |
| **Data Freshness** | Age of data at any given point | Current Time - Last Update |
| **Data Latency** | Delay between generation and availability | Pipeline processing time |
| **Data Currency** | How current relative to real-world state | Last update vs. current |
| **Data Volatility** | Rate at which data changes | Change frequency |

#### 4.1.2 Timeliness Components

```
Timeliness = f(Currency, Volatility)

Where:
  Currency = Age + Delivery Time + Input Time

  • Age = Current Time - Data Creation Time
  • Delivery Time = Time to transfer data
  • Input Time = Time to process and store
  • Volatility = Rate of change in source
```

### 4.2 Critical Timestamps

Every data pipeline should capture these timestamps:

| Timestamp | Column Name | Description | Capture Point |
|-----------|-------------|-------------|---------------|
| **Business Event Time** | `event_timestamp` | When the event actually occurred | Source system |
| **Record Creation** | `created_at` | When record was created in source | Source system |
| **Data Extraction** | `extracted_at` | When data was extracted | ETL ingestion |
| **Data Loading** | `loaded_at` | When data was loaded to destination | ETL completion |
| **Last Modification** | `updated_at` | When record was last modified | Any update |
| **Validity Period** | `valid_from`, `valid_to` | Temporal validity window | Business logic |

### 4.3 Timeliness Requirements Matrix

| Data Domain | Freshness Requirement | Acceptable Latency | Update Frequency | Use Case |
|-------------|----------------------|-------------------|------------------|----------|
| **Real-time Analytics** | < 1 minute | Seconds | Continuous (streaming) | Fraud detection, live dashboards |
| **Operational Reporting** | < 1 hour | Minutes | Near real-time | Inventory, order status |
| **Daily Reporting** | < 24 hours | Hours | Daily batch | Sales reports, KPIs |
| **Historical Analysis** | < 1 week | Days | Weekly batch | Trend analysis, planning |
| **Regulatory Reporting** | Per regulation | As specified | Per deadline | Compliance submissions |

### 4.4 Freshness Monitoring Metrics

| Metric | Formula | Target | Alert Threshold |
|--------|---------|--------|-----------------|
| **Data Age** | `NOW() - MAX(loaded_at)` | Per SLA | SLA + 10% |
| **Refresh Rate** | `Actual Updates / Expected Updates` | ≥ 99% | < 95% |
| **Staleness Ratio** | `Stale Records / Total Records` | < 1% | > 5% |
| **Pipeline Delay** | `AVG(loaded_at - event_timestamp)` | Per SLA | SLA exceeded |
| **Time-to-Insight** | `Query Time - Event Time` | Per need | > 2x target |

### 4.5 Timeliness SLA Template

| Data Product | Owner | Freshness SLA | Latency SLA | Availability | Escalation |
|--------------|-------|---------------|-------------|--------------|------------|
| Sales Dashboard | Sales Ops | 15 minutes | 5 minutes | 99.9% | P1 → Mgr |
| Financial Reports | Finance | 24 hours | 4 hours | 99.5% | P2 → CFO |
| Customer 360 | CRM Team | 1 hour | 15 minutes | 99.5% | P1 → CDO |
| Inventory Status | Supply Chain | 30 minutes | 10 minutes | 99.9% | P1 → COO |

---

## 5. Period-End Close Policy (Listed Company)

> **Critical for EWG:** As a SET-listed company, EWG must comply with strict regulatory reporting requirements from the Stock Exchange of Thailand (SET) and Securities and Exchange Commission (SEC Thailand).

![Data Close Cycle Policy](./diagrams/09_data_close_cycle_policy.drawio.svg)

### 5.1 Regulatory Context

#### 5.1.1 SET/SEC Reporting Requirements

| Report Type | Deadline | Regulatory Basis |
|-------------|----------|------------------|
| **Quarterly Financial Statements** (Reviewed) | 45 days from quarter-end | SET Disclosure Rules |
| **Annual Financial Statements** (Audited, without Q4) | 2 months from fiscal year-end | SET/SEC |
| **Annual Financial Statements** (Audited, with Q4) | 3 months from fiscal year-end | SET/SEC |
| **Form 56-1 One Report** | 3 months from fiscal year-end | SEC Thailand |
| **MD&A (Management Discussion & Analysis)** | With financial statements | SET (if variance > 20%) |

#### 5.1.2 Penalties for Non-Compliance

| Violation | Penalty |
|-----------|---------|
| Late submission | THB 100,000 + THB 3,000/day |
| Incomplete information | THB 100,000 + THB 3,000/day |
| Director/Executive share reporting | Up to THB 500,000 + THB 10,000/day |

### 5.2 Period-End Close Framework

![Period-End Close Timeline](./diagrams/05_period_end_close_timeline.drawio.svg)

#### 5.2.1 Close Calendar Overview

| Period | Close Type | Complexity | Key Activities |
|--------|------------|------------|----------------|
| **Month-End** | Soft Close | Standard | Reconciliations, accruals, basic reporting |
| **Quarter-End** | Hard Close | High | Full reconciliation, external reporting, MD&A |
| **Year-End** | Full Close | Critical | Audit preparation, tax adjustments, Form 56-1 |

#### 5.2.2 Monthly Close Cycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MONTHLY CLOSE TIMELINE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Month End          WD+1        WD+3        WD+5        WD+7           │
│      │               │           │           │           │             │
│      ▼               ▼           ▼           ▼           ▼             │
│  ┌───────┐      ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐        │
│  │ DATA  │      │SUB-LED │  │ INTER- │  │ TRIAL  │  │ MGMT   │        │
│  │CUTOFF │ ──▶  │ CLOSE  │──▶│ COMPANY│──▶│BALANCE │──▶│REPORTS │        │
│  │       │      │        │  │ ELIM.  │  │ REVIEW │  │        │        │
│  └───────┘      └────────┘  └────────┘  └────────┘  └────────┘        │
│                                                                         │
│  WD = Working Day                                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

| Day | Activity | Owner | Data Systems Impact |
|-----|----------|-------|---------------------|
| **WD 0** (Month-End) | Data cutoff, transaction freeze | IT/Finance | **DATA FREEZE** begins |
| **WD +1** | Sub-ledger close (AP, AR, Inventory) | Accounting | Source systems locked |
| **WD +2** | Bank reconciliation | Treasury | Cash data validated |
| **WD +3** | Intercompany elimination | Corporate Finance | Consolidation data ready |
| **WD +4** | Accruals and adjustments | Accounting | Adjustment entries posted |
| **WD +5** | Trial balance review | Controller | Data validated |
| **WD +6** | Variance analysis | FP&A | Analytics data updated |
| **WD +7** | Management reports | Finance | Reports published |

### 5.3 Quarterly Close Policy

#### 5.3.1 Quarter-End Timeline (45-Day Deadline)

| Phase | Timeline | Activities | Critical Data |
|-------|----------|------------|---------------|
| **Phase 1: Soft Close** | WD 1-5 | Same as month-end | Operational data |
| **Phase 2: Hard Close** | WD 6-10 | Journal review, reconciliations | GL data freeze |
| **Phase 3: Review** | WD 11-20 | Auditor review, adjustments | Audit adjustments |
| **Phase 4: Reporting** | WD 21-35 | MD&A preparation, board review | Final numbers |
| **Phase 5: Submission** | WD 36-45 | SET/SEC submission via SETLink | Regulatory filing |

#### 5.3.2 Quarter-End Data Governance Activities

| Activity | Data Governance Requirement | Responsible |
|----------|----------------------------|-------------|
| **Data Freeze** | No changes to financial data after cutoff | Data Custodian |
| **Data Validation** | Automated quality checks on all financial data | Data Steward |
| **Reconciliation** | Source-to-target reconciliation for all systems | Data Steward |
| **Lineage Documentation** | Document data flow for audit trail | Data Owner |
| **Access Restriction** | Limit write access during close period | IT Security |
| **Change Control** | No system changes during close window | IT/Change Mgmt |

### 5.4 Year-End Close Policy

#### 5.4.1 Year-End Timeline (90-Day Deadline)

![Data Freeze Policy](./diagrams/06_data_freeze_policy.drawio.svg)

| Phase | Timeline | Activities | Stakeholders |
|-------|----------|------------|--------------|
| **Pre-Close** | Dec 1-15 | Preparation, cutoff communications | All departments |
| **Soft Close** | Dec 16-31 | Q4 preliminary close | Finance |
| **Hard Close** | Jan 1-15 | Full year adjustments | Finance, Accounting |
| **Audit Fieldwork** | Jan 16 - Feb 15 | External audit procedures | Auditors, Finance |
| **Final Adjustments** | Feb 16-28 | Audit adjustments, tax provisions | Finance, Tax |
| **Board Approval** | Mar 1-15 | Financial statement approval | Board, Audit Committee |
| **Regulatory Filing** | Mar 16-31 | Form 56-1 submission | IR, Legal, Finance |

#### 5.4.2 Year-End Data Requirements

| Data Category | Requirement | Deadline | Owner |
|---------------|-------------|----------|-------|
| **Revenue Recognition** | Complete, accurate revenue data | Jan 5 | Sales/Finance |
| **Inventory Valuation** | Physical count reconciled | Jan 10 | Operations |
| **Fixed Assets** | Depreciation calculated, impairment tested | Jan 10 | Accounting |
| **Accounts Receivable** | Aging analysis, provision calculated | Jan 7 | Credit/Finance |
| **Accounts Payable** | Accruals complete, cutoff verified | Jan 5 | AP/Finance |
| **Tax Data** | All tax positions documented | Feb 15 | Tax |
| **Related Party** | All transactions identified and disclosed | Feb 20 | Legal/Finance |
| **Contingencies** | All claims and commitments documented | Feb 20 | Legal |

### 5.5 Data Freeze Policy

#### 5.5.1 Data Freeze Levels

| Level | Description | Duration | Scope |
|-------|-------------|----------|-------|
| **Level 1: Soft Freeze** | No new transactions in source systems | WD 0 - WD 2 | Transactional data |
| **Level 2: Hard Freeze** | No changes to GL without approval | WD 3 - WD 10 | Financial data |
| **Level 3: Audit Freeze** | Only audit adjustments allowed | WD 11 - Filing | All financial data |
| **Level 4: Archive** | Data locked, read-only | Post-filing | Historical data |

#### 5.5.2 Data Freeze Exception Process

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATA FREEZE EXCEPTION WORKFLOW                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│   │ Request  │───▶│ Review   │───▶│ Approve  │───▶│ Execute  │        │
│   │ (User)   │    │(Steward) │    │ (Owner)  │    │(Custodian)│        │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘        │
│        │               │               │               │               │
│        ▼               ▼               ▼               ▼               │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│   │Justific- │    │Impact    │    │Sign-off  │    │Audit     │        │
│   │ation     │    │Analysis  │    │Document  │    │Trail     │        │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘        │
│                                                                         │
│   SLA: 24 hours for standard requests, 4 hours for critical            │
└─────────────────────────────────────────────────────────────────────────┘
```

| Exception Type | Approval Required | Documentation |
|----------------|-------------------|---------------|
| **Correction of Error** | Data Steward | Error description, impact |
| **Late Invoice** | Data Owner | Business justification |
| **Audit Adjustment** | Controller + Auditor | Audit finding reference |
| **Reclassification** | Controller | Reason, GL accounts |
| **Prior Period Adjustment** | CFO + Audit Committee | Full impact analysis |

### 5.6 Reconciliation Requirements

#### 5.6.1 Mandatory Reconciliations

| Reconciliation Type | Frequency | Tolerance | Owner |
|--------------------|-----------|-----------|-------|
| **Bank Reconciliation** | Daily/Monthly | THB 0 | Treasury |
| **Intercompany Balances** | Monthly | THB 0 | Corporate Finance |
| **Sub-ledger to GL** | Monthly | THB 0 | Accounting |
| **Fixed Asset Register** | Quarterly | < 0.1% | Accounting |
| **Inventory (Perpetual vs Physical)** | Quarterly | < 1% | Operations |
| **Revenue (Billing vs GL)** | Monthly | THB 0 | Revenue Accounting |

#### 5.6.2 Data Quality Gates

| Gate | Timing | Check | Action if Failed |
|------|--------|-------|------------------|
| **G1: Completeness** | WD +1 | All sources loaded | Halt close, investigate |
| **G2: Accuracy** | WD +2 | Reconciliation pass | Review exceptions |
| **G3: Timeliness** | WD +3 | Data within SLA | Escalate to owner |
| **G4: Consistency** | WD +4 | Cross-system match | Resolve discrepancies |
| **G5: Sign-off** | WD +5 | Steward approval | Cannot proceed |

### 5.7 Audit Trail Requirements

#### 5.7.1 What Must Be Logged

| Event | Data Elements | Retention |
|-------|---------------|-----------|
| **Data Change** | Who, what, when, before/after values | 10 years |
| **Access** | User, timestamp, data accessed | 7 years |
| **Approval** | Approver, timestamp, decision | 10 years |
| **Exception** | Requestor, reason, resolution | 10 years |
| **System Change** | Change ID, description, approval | 10 years |

#### 5.7.2 Audit Trail Data Model

```sql
-- Example audit trail schema
CREATE TABLE financial_data_audit (
    audit_id UUID PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP NOT NULL,
    old_values JSONB,
    new_values JSONB,
    change_reason VARCHAR(500),
    approval_id UUID,
    period_end_date DATE,
    is_freeze_period BOOLEAN DEFAULT FALSE
);

-- Index for period-end queries
CREATE INDEX idx_audit_period ON financial_data_audit(period_end_date, is_freeze_period);
```

### 5.8 Period-End Data Governance Checklist

#### 5.8.1 Pre-Close Checklist (T-5 days)

- [ ] Communicate cutoff dates to all departments
- [ ] Verify all interfaces are operational
- [ ] Confirm backup procedures are ready
- [ ] Review pending transactions for cutoff
- [ ] Validate reconciliation templates
- [ ] Test data freeze procedures

#### 5.8.2 Close Period Checklist (T to T+10)

- [ ] Execute data freeze at scheduled time
- [ ] Confirm all sub-ledgers closed
- [ ] Complete all reconciliations
- [ ] Document all exceptions
- [ ] Obtain steward sign-offs
- [ ] Validate data quality gates

#### 5.8.3 Post-Close Checklist (T+10 to Filing)

- [ ] Archive close period data
- [ ] Generate audit trail reports
- [ ] Document lessons learned
- [ ] Update procedures if needed
- [ ] Submit regulatory filings
- [ ] Release data freeze

### 5.9 Key Contacts and Escalation

| Role | Responsibility | Escalation Path |
|------|----------------|-----------------|
| **Close Manager** | Overall close coordination | → CFO |
| **Data Steward (Finance)** | Financial data quality | → Controller → CFO |
| **IT Lead** | System availability, data freeze | → CIO → CFO |
| **External Auditor** | Audit procedures | → Audit Committee |
| **IR/Compliance** | Regulatory filing | → Legal → CEO |

---

## 6. Water Volume Data Consolidation (SSOT)

> **Issue Identified:** During C-Level interviews, it was found that water volume data is not consolidated across the organization. Different departments use different data sources, leading to inconsistent reporting and decision-making challenges.

### 6.1 Problem Statement

#### 6.1.1 Current State (As-Is)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CURRENT STATE: DATA SILOS                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐            │
│  │Production│   │Operations│   │ Finance  │   │ Planning │            │
│  │  System  │   │  System  │   │  System  │   │  System  │            │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘            │
│       │              │              │              │                   │
│       ▼              ▼              ▼              ▼                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐            │
│  │Water Vol │   │Water Vol │   │Water Vol │   │Water Vol │            │
│  │  Data A  │   │  Data B  │   │  Data C  │   │  Data D  │            │
│  │ (Manual) │   │(Estimated)│   │(Invoiced)│   │(Forecast)│            │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘            │
│       ↓              ↓              ↓              ↓                   │
│  ┌─────────────────────────────────────────────────────────┐          │
│  │              INCONSISTENT REPORTS & DECISIONS            │          │
│  │   ⚠ Different numbers in different meetings              │          │
│  │   ⚠ Time wasted reconciling data                         │          │
│  │   ⚠ Wrong decisions based on wrong data                  │          │
│  └─────────────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 6.1.2 Pain Points Identified

| Pain Point | Impact | Affected Stakeholders |
|------------|--------|----------------------|
| **Multiple Data Sources** | No single version of truth | All departments |
| **Manual Data Entry** | High error rate, delays | Operations, Finance |
| **No Standard Definitions** | Apples-to-oranges comparisons | Management, Board |
| **Delayed Reporting** | Decisions based on stale data | C-Level, Planning |
| **Reconciliation Overhead** | 20-30% of analyst time wasted | Finance, Operations |
| **Audit Challenges** | Cannot trace data lineage | Internal Audit, External Auditor |

### 6.2 Target State: Single Source of Truth (SSOT)

#### 6.2.1 SSOT Definition

**Single Source of Truth (SSOT)** is the practice of structuring data so that every data element is mastered in only one place. For water volume data, this means:

> *"One number, one source, one truth - regardless of who asks or when they ask."*

#### 6.2.2 Target Architecture

![SSOT Architecture](./diagrams/07_ssot_architecture.drawio.svg)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TARGET STATE: SINGLE SOURCE OF TRUTH                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐            │
│  │Production│   │Operations│   │  SCADA   │   │ Billing  │            │
│  │  System  │   │  System  │   │  System  │   │  System  │            │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘            │
│       │              │              │              │                   │
│       └──────────────┴──────┬───────┴──────────────┘                   │
│                             │                                          │
│                             ▼                                          │
│              ┌────────────────────────────────┐                        │
│              │     DATA INTEGRATION LAYER      │                        │
│              │  • ETL/ELT Pipelines            │                        │
│              │  • Data Validation Rules        │                        │
│              │  • Automated Quality Checks     │                        │
│              └──────────────┬─────────────────┘                        │
│                             │                                          │
│                             ▼                                          │
│              ┌────────────────────────────────┐                        │
│              │   ⭐ GOLDEN RECORD: WATER      │                        │
│              │      VOLUME MASTER DATA        │                        │
│              │  ─────────────────────────────  │                        │
│              │  • Single authoritative source  │                        │
│              │  • Validated & reconciled       │                        │
│              │  • Audit trail maintained       │                        │
│              │  • Version controlled           │                        │
│              └──────────────┬─────────────────┘                        │
│                             │                                          │
│       ┌─────────────────────┼─────────────────────┐                    │
│       │                     │                     │                    │
│       ▼                     ▼                     ▼                    │
│  ┌──────────┐         ┌──────────┐         ┌──────────┐              │
│  │ Executive│         │Operational│         │ Finance  │              │
│  │Dashboard │         │ Reports  │         │ Reports  │              │
│  └──────────┘         └──────────┘         └──────────┘              │
│                                                                         │
│  ✅ SAME NUMBER EVERYWHERE = CONSISTENT DECISIONS                       │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Golden Record Framework for Water Volume

#### 6.3.1 What is a Golden Record?

A **Golden Record** is the single, authoritative version of a data entity created by consolidating and reconciling data from multiple sources. It represents the "best version of the truth."

#### 6.3.2 Water Volume Data Elements

| Data Element | Definition | Unit | Source System | Capture Frequency |
|--------------|------------|------|---------------|-------------------|
| **Raw Water Intake** | Volume of raw water entering treatment | m³ | SCADA | Real-time (hourly aggregated) |
| **Treated Water Production** | Volume of water after treatment | m³ | SCADA | Real-time (hourly aggregated) |
| **Water Distribution** | Volume delivered to distribution network | m³ | SCADA | Real-time (hourly aggregated) |
| **Water Sales** | Volume billed to customers | m³ | Billing System | Monthly |
| **Non-Revenue Water (NRW)** | Water lost (leakage, theft, unbilled) | m³ | Calculated | Monthly |
| **Water Quality Compliance** | % meeting quality standards | % | Lab System | Daily/Weekly |

#### 6.3.3 Golden Record Creation Rules (Survivorship)

| Scenario | Rule | Rationale |
|----------|------|-----------|
| **SCADA vs Manual Reading** | SCADA wins (if variance < 5%) | Automated is more accurate |
| **SCADA vs Manual (variance > 5%)** | Flag for investigation | May indicate meter issue |
| **Billing vs SCADA** | SCADA for volume, Billing for revenue | Different purposes |
| **Multiple SCADA readings** | Latest valid reading | Most current |
| **Missing SCADA data** | Interpolation from adjacent periods | Maintain continuity |
| **Conflicting sources** | Escalate to Data Steward | Human decision required |

### 6.4 Data Consolidation Roadmap

![Data Consolidation Roadmap](./diagrams/08_data_consolidation_roadmap.drawio.svg)

#### 6.4.1 Phase 1: Foundation (Month 1-2)

| Activity | Deliverable | Owner |
|----------|-------------|-------|
| **Data Source Inventory** | Complete list of all water data sources | Data Steward |
| **Data Element Mapping** | Mapping of fields across systems | IT + Business |
| **Quality Assessment** | Baseline data quality metrics | Data Analyst |
| **Stakeholder Alignment** | Agreed definitions and ownership | CDO + Business |
| **Technology Assessment** | Tool selection for integration | IT Architecture |

#### 6.4.2 Phase 2: Integration (Month 3-4)

| Activity | Deliverable | Owner |
|----------|-------------|-------|
| **ETL/ELT Pipeline Development** | Automated data extraction | IT/Data Engineering |
| **Validation Rules Implementation** | Quality gates in pipelines | Data Engineering |
| **Master Data Repository Setup** | Golden record storage | IT Infrastructure |
| **Data Lineage Documentation** | End-to-end traceability | Data Governance |
| **Initial Data Load & Reconciliation** | Baseline golden record | Data Steward |

#### 6.4.3 Phase 3: Adoption (Month 5-6)

| Activity | Deliverable | Owner |
|----------|-------------|-------|
| **Dashboard Development** | Executive & operational dashboards | BI Team |
| **Report Migration** | Retire legacy reports | Finance + Operations |
| **Training & Change Management** | User adoption program | HR + Data Governance |
| **SOP Development** | Standard operating procedures | Data Steward |
| **Go-Live & Support** | SSOT operational | Project Team |

#### 6.4.4 Phase 4: Optimization (Ongoing)

| Activity | Deliverable | Owner |
|----------|-------------|-------|
| **Continuous Quality Monitoring** | Automated quality dashboards | Data Steward |
| **Feedback Loop** | Issue tracking & resolution | Data Governance |
| **Process Improvement** | Enhanced automation | IT + Business |
| **Audit Support** | Audit-ready documentation | Internal Audit |

### 6.5 Governance Model for Water Volume Data

#### 6.5.1 Roles & Responsibilities (RACI)

| Activity | CDO | Water Data Owner | Data Steward | IT Custodian | Users |
|----------|-----|------------------|--------------|--------------|-------|
| Define data standards | A | R | C | I | I |
| Approve data definitions | A | R | C | I | C |
| Maintain golden record | I | A | R | C | I |
| Implement data pipelines | I | C | C | R/A | I |
| Monitor data quality | I | A | R | C | I |
| Resolve data issues | C | A | R | C | C |
| Use data for reporting | I | I | I | I | R |

> **Legend:** R = Responsible, A = Accountable, C = Consulted, I = Informed

#### 6.5.2 Data Ownership Assignment

| Data Domain | Data Owner | Data Steward | Key Stakeholders |
|-------------|------------|--------------|------------------|
| **Raw Water Intake** | Head of Production | Production Data Analyst | Operations, Planning |
| **Water Treatment** | Head of Production | Production Data Analyst | Operations, Quality |
| **Water Distribution** | Head of Operations | Operations Data Analyst | Operations, Maintenance |
| **Water Sales** | Head of Commercial | Commercial Data Analyst | Finance, Marketing |
| **NRW (Non-Revenue Water)** | Head of Operations | NRW Analyst | Operations, Finance, Board |

### 6.6 Data Quality Framework

#### 6.6.1 Quality Dimensions for Water Data

| Dimension | Definition | Target | Measurement |
|-----------|------------|--------|-------------|
| **Completeness** | All required fields populated | > 99% | % non-null values |
| **Accuracy** | Data matches reality | > 99% | Variance vs physical audit |
| **Timeliness** | Data available when needed | Per SLA | Data age at query time |
| **Consistency** | Same value across all reports | 100% | Cross-system comparison |
| **Validity** | Data conforms to business rules | 100% | Validation pass rate |
| **Uniqueness** | No duplicate records | 100% | Duplicate detection |

#### 6.6.2 Quality Monitoring Dashboard

| Metric | Formula | Target | Alert |
|--------|---------|--------|-------|
| **Completeness Score** | (Non-null values / Total values) × 100 | > 99% | < 95% |
| **Accuracy Score** | 100 - (Variance % from audit) | > 99% | < 95% |
| **Freshness Score** | SLA compliance rate | > 99% | < 95% |
| **Consistency Score** | (Matching records / Total records) × 100 | 100% | < 100% |
| **Overall DQ Score** | Weighted average of above | > 98% | < 95% |

#### 6.6.3 Data Quality SLA

| Data Product | Freshness SLA | Accuracy SLA | Availability SLA |
|--------------|---------------|--------------|------------------|
| **Real-time Dashboard** | < 1 hour | > 99% | 99.9% |
| **Daily Reports** | < 24 hours | > 99% | 99.5% |
| **Monthly Reports** | < 3 working days | > 99.5% | 99.5% |
| **Board Reports** | < 5 working days | > 99.9% | 99.9% |

### 6.7 Technical Implementation

#### 6.7.1 Recommended Architecture Pattern

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      TECHNICAL ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  SOURCE LAYER          INTEGRATION LAYER         CONSUMPTION LAYER      │
│  ─────────────         ─────────────────         ─────────────────      │
│                                                                         │
│  ┌──────────┐         ┌─────────────────┐       ┌─────────────────┐    │
│  │  SCADA   │────────▶│                 │       │  Executive BI   │    │
│  └──────────┘         │                 │──────▶│  (Power BI)     │    │
│                       │                 │       └─────────────────┘    │
│  ┌──────────┐         │  DATA WAREHOUSE │                              │
│  │ Billing  │────────▶│  (Golden Record)│       ┌─────────────────┐    │
│  │ System   │         │                 │──────▶│  Operational    │    │
│  └──────────┘         │  • Staging      │       │  Reports        │    │
│                       │  • Cleansing    │       └─────────────────┘    │
│  ┌──────────┐         │  • Master Data  │                              │
│  │  ERP     │────────▶│  • Data Mart    │       ┌─────────────────┐    │
│  └──────────┘         │                 │──────▶│  API Services   │    │
│                       │                 │       │  (Integration)  │    │
│  ┌──────────┐         └─────────────────┘       └─────────────────┘    │
│  │ Manual   │                │                                         │
│  │ Entry    │────────────────┘                                         │
│  └──────────┘                                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 6.7.2 Key Technical Components

| Component | Purpose | Recommended Tools |
|-----------|---------|-------------------|
| **ETL/ELT** | Data extraction and transformation | Azure Data Factory, SSIS, dbt |
| **Data Warehouse** | Golden record storage | Azure Synapse, Snowflake, SQL Server |
| **Data Quality** | Validation and monitoring | Great Expectations, dbt tests |
| **Master Data Hub** | Canonical data storage | Custom or MDM tools |
| **BI Platform** | Reporting and dashboards | Power BI, Tableau |
| **Data Catalog** | Metadata management | Azure Purview, Alation |

#### 6.7.3 Sample Data Model

```sql
-- Water Volume Master Data Schema

-- Dimension: Location (Water Facilities)
CREATE TABLE dim_location (
    location_id UUID PRIMARY KEY,
    location_code VARCHAR(20) NOT NULL UNIQUE,
    location_name VARCHAR(200) NOT NULL,
    location_type VARCHAR(50) NOT NULL, -- 'Treatment Plant', 'Distribution Zone', etc.
    parent_location_id UUID REFERENCES dim_location(location_id),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    is_active BOOLEAN DEFAULT TRUE,
    effective_from DATE NOT NULL,
    effective_to DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Meter
CREATE TABLE dim_meter (
    meter_id UUID PRIMARY KEY,
    meter_code VARCHAR(50) NOT NULL UNIQUE,
    meter_name VARCHAR(200),
    meter_type VARCHAR(50) NOT NULL, -- 'Flow', 'Level', 'Pressure'
    location_id UUID REFERENCES dim_location(location_id),
    unit_of_measure VARCHAR(20) NOT NULL, -- 'm3', 'm3/h', 'bar'
    calibration_date DATE,
    next_calibration_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact: Water Volume (Golden Record)
CREATE TABLE fact_water_volume (
    volume_id UUID PRIMARY KEY,
    location_id UUID NOT NULL REFERENCES dim_location(location_id),
    meter_id UUID REFERENCES dim_meter(meter_id),
    measurement_date DATE NOT NULL,
    measurement_hour INT, -- 0-23 for hourly data, NULL for daily

    -- Volume measurements
    raw_water_intake_m3 DECIMAL(15, 3),
    treated_water_m3 DECIMAL(15, 3),
    distributed_water_m3 DECIMAL(15, 3),
    billed_water_m3 DECIMAL(15, 3),
    nrw_m3 DECIMAL(15, 3),
    nrw_percentage DECIMAL(5, 2),

    -- Data quality indicators
    data_source VARCHAR(50) NOT NULL, -- 'SCADA', 'Manual', 'Billing', 'Calculated'
    quality_score DECIMAL(5, 2),
    is_validated BOOLEAN DEFAULT FALSE,
    is_estimated BOOLEAN DEFAULT FALSE,

    -- Audit trail
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP,
    updated_by VARCHAR(100),

    -- Ensure uniqueness per location/date/hour
    UNIQUE (location_id, measurement_date, measurement_hour)
);

-- Audit trail for all changes
CREATE TABLE water_volume_audit (
    audit_id UUID PRIMARY KEY,
    volume_id UUID NOT NULL REFERENCES fact_water_volume(volume_id),
    action VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_reason VARCHAR(500)
);
```

### 6.8 Change Management & Adoption

#### 6.8.1 Stakeholder Communication Plan

| Stakeholder Group | Key Message | Communication Channel | Frequency |
|-------------------|-------------|----------------------|-----------|
| **C-Level** | Strategic benefits, ROI | Executive briefing | Monthly |
| **Department Heads** | Process changes, ownership | Department meetings | Bi-weekly |
| **Data Users** | How to access, benefits | Email + Training | Weekly during rollout |
| **IT Team** | Technical requirements | Technical workshops | As needed |

#### 6.8.2 Training Program

| Training Module | Audience | Duration | Delivery |
|-----------------|----------|----------|----------|
| **SSOT Awareness** | All staff | 1 hour | E-learning |
| **Data Entry Standards** | Data entry staff | 2 hours | Workshop |
| **Dashboard Usage** | Managers, Analysts | 2 hours | Hands-on |
| **Data Stewardship** | Data Stewards | 4 hours | Workshop |
| **Technical Training** | IT Team | 8 hours | Technical lab |

#### 6.8.3 Success Metrics

| Metric | Baseline | Target (6 months) | Target (12 months) |
|--------|----------|-------------------|-------------------|
| **Report discrepancy rate** | High (unknown) | < 5% | 0% |
| **Time to produce reports** | 3-5 days | 1-2 days | < 1 day |
| **Analyst time on reconciliation** | 20-30% | < 10% | < 5% |
| **Data freshness** | Days old | < 24 hours | < 1 hour |
| **User satisfaction** | Unknown | > 70% | > 90% |

### 6.9 Quick Wins for Phase#0

| # | Quick Win | Effort | Impact | Owner |
|---|-----------|--------|--------|-------|
| 1 | **Define "Official" Water Volume** | Low | High | CDO + Business |
| 2 | **Identify authoritative source system** | Low | High | IT + Operations |
| 3 | **Create simple reconciliation report** | Medium | High | IT + Finance |
| 4 | **Establish monthly data review meeting** | Low | Medium | Data Governance |
| 5 | **Document current data flow** | Medium | Medium | Data Steward |

---

## 7. Reference Framework: DAMA-DMBOK

### 7.1 Overview

The **DAMA Data Management Body of Knowledge (DMBOK)** is the globally recognized standard for data management. It positions Data Governance at the center of 11 interconnected knowledge areas.

![DAMA Wheel](./diagrams/04_dama_wheel.drawio.svg)

### 7.2 The 11 Knowledge Areas

| # | Knowledge Area | Description | Key Deliverables |
|---|----------------|-------------|------------------|
| 1 | **Data Governance** | Central orchestrating function | Policies, standards, RACI |
| 2 | **Data Architecture** | Blueprint for data structures | Enterprise data model |
| 3 | **Data Modeling & Design** | Structured representations | Conceptual, logical, physical models |
| 4 | **Data Storage & Operations** | Availability and performance | Database management, backup |
| 5 | **Data Security** | Protection from threats | Access control, encryption |
| 6 | **Data Integration & Interoperability** | Combining data sources | ETL/ELT, APIs, data exchange |
| 7 | **Document & Content Management** | Unstructured data handling | Document lifecycle |
| 8 | **Data Warehousing & BI** | Analytical data management | Data warehouse, reporting |
| 9 | **Metadata Management** | Data about data | Data catalog, lineage |
| 10 | **Reference & Master Data Management** | Authoritative sources | MDM, reference data |
| 11 | **Data Quality Management** | Ensuring data fitness | Profiling, cleansing |

### 7.3 Governance-Centric Model

```
                    Data Quality
                         ↑
    Reference Data ←── GOVERNANCE ──→ Data Architecture
                         ↑
                    Data Security
```

Data Governance connects to and influences all other knowledge areas:

- **Governance → Quality**: Defines quality rules and thresholds
- **Governance → Security**: Sets access policies and controls
- **Governance → Architecture**: Approves architectural standards
- **Governance → Metadata**: Requires documentation standards

---

## 8. Implementation Roadmap

### 8.1 Phase#0 Work Packages

| WP# | Work Package | Deliverable | Duration | Owner |
|-----|--------------|-------------|----------|-------|
| WP1 | Current State Assessment | Maturity assessment report | Week 1-2 | Consultant |
| WP2 | Governance Structure Design | RACI matrix, governance charter | Week 2-3 | CDO |
| WP3 | Policy Framework Development | Draft policies (Quality, Security, Access) | Week 3-4 | Data Governance Lead |
| WP4 | Data Inventory | Critical data elements catalog | Week 3-5 | Data Stewards |
| WP5 | Timeliness Requirements | SLA definitions per data domain | Week 4-5 | Data Owners |
| WP6 | Quick Wins Identification | Prioritized improvement list | Week 5-6 | Project Team |

### 8.2 Key Questions for C-Level

#### Data Governance
- [ ] Who should own which data domains?
- [ ] What governance structure fits EWG's culture (centralized/federated)?
- [ ] How will governance decisions be escalated and resolved?
- [ ] What level of investment is available for governance tools?

#### Data Policy
- [ ] What regulatory requirements apply (PDPA, industry-specific)?
- [ ] How should data be classified? (How many levels?)
- [ ] What are the retention requirements by data type?
- [ ] Who has authority to approve data sharing externally?

#### Time of Data Capture
- [ ] What are the freshness requirements per business function?
- [ ] Where are the critical latency bottlenecks today?
- [ ] What timestamps are currently captured in source systems?
- [ ] What is the acceptable data delay for decision-making?

### 8.3 Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Stakeholder interviews completed | 100% of C-Level | Interview count |
| Critical data elements identified | Top 20 CDEs | Data inventory |
| Policy gaps documented | Complete assessment | Gap analysis document |
| Quick wins identified | Minimum 5 | Prioritized list |
| Governance structure approved | Signed charter | Executive sign-off |
| Timeliness SLAs defined | 80% of critical data | SLA document |

### 8.4 Implementation Best Practices

| Practice | Description | Benefit |
|----------|-------------|---------|
| **Start Small, Scale Fast** | Begin with high-value domains | Quick wins build momentum |
| **Embed, Don't Add** | Integrate into existing workflows | Higher adoption |
| **Tiered Governance** | Proportionate controls by risk | Efficient resource use |
| **Automate Controls** | Reduce manual enforcement | Consistency, scale |
| **Measure Outcomes** | Connect to business metrics | Demonstrate ROI |

---

## 9. Appendix: Diagrams

All diagrams are available in Draw.io format in the `./diagrams/` folder:

| # | Diagram | File | Description |
|---|---------|------|-------------|
| 1 | Data Governance 4 Pillars | `01_data_governance_4_pillars.drawio` | Four foundational pillars |
| 2 | Data Policy Hierarchy | `02_data_policy_hierarchy.drawio` | Policy document hierarchy |
| 3 | Time of Data Capture Flow | `03_time_of_data_capture_flow.drawio` | Data capture timeline |
| 4 | DAMA Wheel | `04_dama_wheel.drawio` | 11 knowledge areas |
| 5 | Period-End Close Timeline | `05_period_end_close_timeline.drawio` | Month/Quarter/Year-End timeline |
| 6 | Data Freeze Policy | `06_data_freeze_policy.drawio` | Data freeze levels and workflow |
| 7 | SSOT Architecture | `07_ssot_architecture.drawio` | Single Source of Truth architecture |
| 8 | Data Consolidation Roadmap | `08_data_consolidation_roadmap.drawio` | 4-Phase implementation roadmap |
| 9 | Data Close Cycle Policy | `09_data_close_cycle_policy.drawio` | Complete close cycle with freeze levels, quality gates, exceptions |

### PNG Exports

Pre-exported PNG files are available in `./diagrams/png/` folder for use in presentations and documents.

---

## References

### Data Governance & Policy
1. [DAMA International - DMBOK](https://dama.org/learning-resources/dama-data-management-body-of-knowledge-dmbok/)
2. [Atlan - Data Governance Framework 2026](https://atlan.com/data-governance-framework/)
3. [Atlan - DAMA DMBOK Framework Guide](https://atlan.com/dama-dmbok-framework/)
4. [Alation - Data Governance Best Practices](https://www.alation.com/blog/data-governance-best-practices/)

### Data Timeliness
5. [Anomalo - Data Freshness](https://www.anomalo.com/blog/defining-data-freshness-measuring-and-monitoring-data-timeliness/)
6. [DQOps - Data Timeliness](https://dqops.com/types-of-data-timeliness-checks/)
7. [Monte Carlo - Data Timeliness](https://www.montecarlodata.com/blog-what-is-data-timeliness/)

### SET/SEC Thailand Regulations
8. [SET - Periodic Disclosure Requirements](https://www.set.or.th/en/listing/listed-company/simplified-regulations/disclosure/periodic-disclosure)
9. [SET - Rules and Regulations for Listed Companies](https://www.set.or.th/en/rules-regulations/listed-companies)
10. [Baker McKenzie - SET Continuing Obligations](https://resourcehub.bakermckenzie.com/en/resources/cross-border-listings-guide/asia-pacific/stock-exchange-of-thailand/topics/continuing-obligationsperiodic-reporting)

### Financial Close Best Practices
11. [FinQuery - Accelerating Your Close](https://finquery.com/blog/best-practices-for-accelerating-your-close/)
12. [Numeric - Financial Close Process Framework](https://www.numeric.io/blog/financial-close-process)
13. [HighRadius - Month-End Close Process](https://www.highradius.com/resources/Blog/what-is-month-end-close-process/)

### Single Source of Truth (SSOT) & Master Data Management
14. [Atlan - Single Source of Truth](https://atlan.com/single-source-of-truth/)
15. [Informatica - What is a Golden Record](https://www.informatica.com/resources/articles/what-is-a-golden-record.html)
16. [Gartner - Master Data Management](https://www.gartner.com/en/information-technology/glossary/master-data-management-mdm)
17. [TDWI - Data Consolidation Best Practices](https://tdwi.org/articles/data-consolidation-best-practices)

---

## Document Downloads

| Format | File | Description |
|--------|------|-------------|
| **MS Word** | `EWG_Phase0_Data_Governance_Summary.docx` | Executive summary with diagrams |
| **Markdown** | `EWG_Phase0_Data_Governance_Framework.md` | Full technical documentation |

---

> **Document Prepared by:** Angela AI
> **For:** EWG Phase#0 Data Governance Initiative
> **Date:** January 13, 2026
> **Version:** 1.1
