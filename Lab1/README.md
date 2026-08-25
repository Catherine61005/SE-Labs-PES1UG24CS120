# Lab 1: Requirements Engineering & UML Use-Case Modelling

**Problem Statement #53 | Media, Events & Community**
**Freelance Content Creator Escrow Platform**

## Overview

A freelance contract management system that allows content creators and client sponsors to define deliverable milestones, review watermarked draft assets, and trigger secure milestone payment releases.

**Stakeholders / Actors:**
- **Content Creator** — submits draft deliverables, defines milestones
- **Client Sponsor** — reviews drafts, approves/rejects, releases payment
- **Payment Gateway** — external system that processes escrow transfers

## Repository Contents

| File | Description |
|---|---|
| `Requirements_Table.docx` | Requirements Specification Table — 5 Functional Requirements (FR-001–FR-005) and 2 Nonfunctional Requirements (NFR-001, NFR-002), each with Req ID, Type, Description, Priority, Acceptance Criteria, and Rationale. |
| `usecase_diagram.pdf` | UML Use-Case Diagram — 3 actors and 9 use cases, including `<<include>>` relationships (Submit Draft → Apply Watermark; Approve Milestone → Release Payment; Release Payment → Process Payment) and one `<<extend>>` relationship (Request Revision → Review Draft Deliverable). |
| `UseCase_Flow.docx` | Use-Case Flow Specification (1 page) — Preconditions, Postconditions, Main Success Scenario, and Alternate/Exception Flows for the core "Submit Draft Deliverable & Release Milestone Payment" use case. |

## Requirements Summary

| Req ID | Type | Priority | Summary |
|---|---|---|---|
| FR-001 | Functional | High | Submit draft for review; release milestone payment on sponsor sign-off *(given)* |
| FR-002 | Functional | High | Define a deliverable milestone (title, due date, amount) |
| FR-003 | Functional | High | Sponsor records explicit approve/reject decision |
| FR-004 | Functional | Medium | Sponsor requests revision with a reason |
| FR-005 | Functional | Medium | Notify creator/sponsor on milestone status change |
| NFR-001 | Nonfunctional | High | Automated watermarking completes in under 5s *(given)* |
| NFR-002 | Nonfunctional | High | Financial/milestone data encrypted (AES-256) in transit and at rest |

## Core Use Case: Submit Draft Deliverable & Release Milestone Payment

**Actors:** Content Creator (primary), Client Sponsor, Payment Gateway

**Main flow (summary):** Creator submits draft → system watermarks it → sponsor reviews and approves → system releases escrow payment via the Payment Gateway → creator is credited and both parties are notified.

**Alternate/Exception flows:**
- Sponsor requests revision instead of approving
- Payment Gateway declines the transfer
- Watermarking fails on an unsupported file

## Tools Used

- UML diagram modelling: generated programmatically (equivalent output to Draw.io/Lucidchart)
- Documents: Microsoft Word (.docx)

## How to View

- Open `.docx` files in Microsoft Word, Google Docs, or LibreOffice Writer.
- Open `usecase_diagram.pdf` in any PDF viewer.
