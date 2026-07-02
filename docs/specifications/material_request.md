# Material Request Workspace Specification

## Purpose

The Material Request Workspace is used to create, view, edit, and manage material requests for supplier quotation processing.

## Main Business Rule

One Material Request belongs to one project only.

One Project can have many Material Requests.

One Material Request can contain many Material Items.

## Workflow

Dashboard
→ Quotation Monitoring
→ New Material Request
→ Material Request Workspace
→ Save
→ Return to Quotation Monitoring List

## Required Sections

### 1. Action Toolbar

Buttons:
- Save
- Back
- Cancel
- Delete
- Add Attachment

### 2. Request Information

Fields:
- Material Request No. — auto-generated
- Date Requested — auto-generated
- Requested By — logged-in user
- Project/Site — required
- Client — optional
- Assigned To — optional
- Priority — High / Medium / Low
- Status — New / Assigned / In Progress / Waiting Supplier Quote / Completed / Archived
- Due Date — required
- Remarks — optional

### 3. Material Items

Each Material Request can have multiple items.

Fields:
- Quantity
- Unit
- Material Description
- Brand
- Remarks

Actions:
- Add Item
- Edit Item
- Delete Item

### 4. Attachments

Files are stored in the shared folder.

Database stores only file metadata and file path.

Actions:
- Upload File
- Open File
- Open Folder
- Delete File

### 5. Activity Timeline

Track:
- Created
- Updated
- Status Changed
- Attachment Added
- Attachment Deleted
- Deleted

## Database Tables

- core.projects
- core.users
- quotation.material_requests
- quotation.material_request_items
- quotation.attachments
- core.activity_logs

## Validation Rules

- Project is required.
- Material Request Description is required.
- At least one Material Item is recommended before final completion.
- Due Date is required.
- Status defaults to New.
- Priority defaults to Medium.

## Future Extensions

- Supplier quotations
- Price comparison
- Approval workflow
- Purchase order generation
- Print preview
- PDF export