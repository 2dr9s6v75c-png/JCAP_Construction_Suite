# JCAP Construction Suite ERP Design Document

## Version
v1.0 Draft

## Purpose
JCAP Construction Suite is a desktop ERP-style system for managing construction procurement workflows.

## Core Architecture
- Python
- CustomTkinter
- PostgreSQL
- Shared network document storage
- Git/GitHub version control

## Core Modules
- Authentication
- Dashboard
- Quotation Monitoring
- Supplier RFQ
- Purchase Orders
- Inventory
- Invoice Monitoring
- Reports
- Administration

## Development Standards
Every module should follow this structure:

modules/module_name/
- views/
- components/
- services/
- dialogs/
- models/
- validators/
- utils/

## Standard Workflow
Material Request
→ Supplier RFQ
→ Supplier Quotation
→ Quotation Comparison
→ Purchase Order
→ Delivery Receipt
→ Inventory / Receiving
→ Invoice Monitoring
→ Payment Monitoring

## UI Standard
Each major module should have:
- List View
- Details View
- Create/Edit Workspace
- Search
- Refresh
- Status badges
- Activity timeline
- Attachment panel

## Database Standard
- PostgreSQL is the source of truth.
- UUIDs are used as internal primary keys.
- User-facing document numbers are generated separately.
- Example: MR-2026-000001

## Document Storage Standard
Documents are stored in the shared network folder.

Root path:
\\192.168.50.39\JCAP Main Office Shared Folder\JCAP Purchasing\JCAP Quotation for Project Bidding

Project folders should follow:

Project Code - Project Name/
- 01 Material Requests
- 02 Supplier RFQ
- 03 Supplier Quotations
- 04 Quotation Evaluation
- 05 Purchase Orders
- 06 Delivery Receipts
- 07 Invoices
- 08 Supporting Documents
- 09 Archive

## Material Request Rules
- One Material Request belongs to one Project only.
- One Project can have many Material Requests.
- Material Request content is mainly supported by uploaded attachments.
- Material Request Description is required.
- At least one attachment is required.
- MR numbers are generated automatically.

## Git Standard
Use Conventional Commits.

Examples:
- feat(quotation): add material request details view
- fix(storage): correct attachment folder path
- refactor(core): centralize document path handling
- docs: update ERP design document

## Current Completed Foundation
- Authentication
- Dashboard shell
- Navigation framework
- Master data for projects and users
- Material Request creation
- Material Request monitoring cards
- Material Request details view
- Attachment upload
- Project-based shared folder storage
- Activity log foundation