# JCAP Construction Suite
# Architecture Decision Log

---

## Decision 001

Date:
2026-07-05

Title:
Permission Based Authorization

Decision

System authorization will be based on permissions instead of checking role names.

Reason

Allows flexible assignment of responsibilities without modifying application code.

Status

Accepted

---

## Decision 002

Date:
2026-07-05

Title:
Version 1 Procurement Workflow

Workflow

Material Request

↓

Supplier RFQ

↓

Supplier Quotation Repository

↓

Purchase Order

↓

Delivery Monitoring

↓

Invoice Monitoring

Reason

Matches the actual procurement workflow used by JCAP.

Status

Accepted

---

## Decision 003

Date:
2026-07-05

Title:
Supplier Comparison Deferred

Decision

Supplier comparison and analytics will not be included in Version 1.

Reason

Current purchasing workflow does not require quotation comparison.

Status

Accepted

---

## Decision 004

Date:
2026-07-05

Title:
Deployment Strategy

Decision

Deploy Version 1 after Supplier Quotation Repository is completed.

Reason

Allows real users to validate the system before expanding to Inventory and other modules.

Status

Accepted

# Coding Standards

## General

- PostgreSQL is the source of truth.
- Business logic belongs in services.
- UI never talks directly to PostgreSQL.
- Every business action is logged.
- Every feature requires permissions.
- Use UUID internally.
- Use generated document numbers externally.

## Git

Use Conventional Commits.

Examples

feat(quotation):

fix(core):

refactor(storage):

docs:

chore:

## Python

- One class per file whenever practical.
- Keep views focused on presentation.
- Services handle business rules.
- Components should be reusable.

## UI

Every module should contain

List View

Details View

Create/Edit View

Search

Refresh

Activity Timeline

Attachment Panel

# Release Strategy

## Version 1

Authentication

Dashboard

Material Request

Enterprise Document Framework

Supplier RFQ

Supplier Quotation Repository

Deploy to Purchasing Department

Collect Feedback

Bug Fixes

---

## Version 2

Purchase Orders

Delivery Monitoring

Invoice Monitoring

---

## Version 3

Inventory

Reports

Administration

---

## Version 4

Supplier Analytics

Executive Dashboard

KPI Reports

# Product Roadmap

Current Stage

Enterprise Procurement Platform

Mission

Digitize JCAP's procurement workflow.

Primary Goal

Reduce manual document handling.

Future Goal

Complete Procurement ERP.

Current Priority

Enterprise Document Framework

# Milestones

v0.1.0
Authentication

v0.2.0
Material Request Foundation

v0.3.0
Quotation Monitoring

v0.3.1
Permission Authorization

v0.4.0
Enterprise Document Framework

v0.5.0
Supplier RFQ

v0.6.0
Supplier Quotation Repository

Production Deployment

v0.7.0
Purchase Orders

v0.8.0
Delivery Monitoring

v0.9.0
Invoice Monitoring

# Changelog

## v0.3.1

Added

- ERP Design Document
- Permission Authorization
- Role Permission Mapping

Improved

- Project Architecture
- Navigation
- Material Request Details

Fixed

- Duplicate service functions