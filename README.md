# AuditTrail — Field Audit Management Dashboard

AuditTrail is a web-based field audit management system designed to manage auditors, locations, audit assignments, checklist-based inspections, compliance scoring, flagged issues, and audit reporting.

The project models a real-world audit workflow where managers assign audits to auditors, auditors complete structured checklists, and managers can monitor compliance and audit status from a central dashboard.

## In Action
<img width="800" alt="image" src="https://github.com/user-attachments/assets/b946504c-7e6b-45ba-9e59-ea3480241190" />
<img width="800" alt="image" src="https://github.com/user-attachments/assets/cfc15848-099f-464a-8603-981cd910e546" />
<img width="800"  alt="image" src="https://github.com/user-attachments/assets/a53c99ea-54da-45c1-b534-6a95c85b2779" />
<img width="800"  alt="image" src="https://github.com/user-attachments/assets/dfe1e5af-7481-495a-ae7d-79ed8d54aec9" />
<img width="800"  alt="image" src="https://github.com/user-attachments/assets/108c3013-fb27-4a5c-8b23-cb9c90f4369f" />



## Features

### Manager Dashboard

- Overview of audit programme status
- Total, completed, in-progress, and pending audits
- Compliance score overview
- Flagged issue monitoring
- Audit activity table
- Auditor assignment overview

### Audit Management

- Assign auditors to locations
- Create and manage audits
- Track audit status
- View individual audit reports
- Track due dates and completion dates

### Audit Submission

- Checklist-based audit forms
- 1–5 scoring system
- Live compliance score calculation
- Automatic flagging of low-scoring items
- Remarks for audit findings
- Photo evidence support
- Save audits as drafts
- Submit completed audits

### Access Control

- Manager and auditor workflows
- Login and authentication
- Auditors can access their assigned audits
- Managers can manage the overall audit programme

## Tech Stack

- **Backend:** Python, Django
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript
- **Templating:** Django Templates

## Project Structure

The project is organized around a Django backend, templates, static frontend assets, and relational data models.

- `manage.py` — Django project entry point
- `audittrail/` — Django project configuration
- `audits/` — Audit application containing models, views, forms, URLs, and business logic
- `templates/` — HTML templates
- `static/` — CSS and JavaScript assets
- `requirements.txt` — Python dependencies

## Data Model

The application uses a relational model to represent the audit workflow.

User → UserProfile → Auditor

Auditor → Audit

Location → Audit

AuditTemplate → ChecklistItem

Audit → AuditResponse

The main entities are:

- **Auditor** — employee responsible for conducting audits
- **Location** — site being audited
- **AuditTemplate** — reusable audit/checklist template
- **ChecklistItem** — individual requirement within a template
- **Audit** — an assigned audit instance
- **AuditResponse** — score, remarks, and evidence associated with a checklist item

## Audit Workflow

1. Manager selects a location.
2. Manager selects an auditor.
3. Manager assigns an audit.
4. Auditor opens the assigned audit.
5. Auditor completes the checklist.
6. Auditor adds scores, remarks, and evidence.
7. Auditor saves the audit as a draft or submits it.
8. The completed audit becomes available for review.
9. Manager reviews compliance scores and flagged issues.

## Compliance Scoring

Each checklist item is scored on a 1–5 scale.

Low-scoring items are automatically flagged for attention.

The overall compliance score is calculated from the submitted checklist responses.

## Getting Started

### 1. Clone the repository

    git clone <repository-url>
    cd auditrail

### 2. Create a virtual environment

#### Windows

    python -m venv venv
    venv\Scripts\activate

#### macOS / Linux

    python3 -m venv venv
    source venv/bin/activate

### 3. Install dependencies

    pip install -r requirements.txt

### 4. Apply migrations

    python manage.py migrate

### 5. Start the development server

    python manage.py runserver

Open the local development server shown in the terminal.

## Project Status

**MVP / Development**

The core manager and auditor workflows are implemented. The project is intended as a practical demonstration of building a business-oriented web application with Django, relational data modelling, server-rendered interfaces, and JavaScript-based frontend interactions.

## Future Improvements

Potential future improvements include:

- PostgreSQL deployment
- More extensive automated testing
- Advanced audit filtering and reporting
- Data visualisation and historical compliance trends
- Improved API architecture
- Production deployment
- Enhanced file and photo management

## Author

**Aakrit Singh**

Built as a practical full-stack web development project.
