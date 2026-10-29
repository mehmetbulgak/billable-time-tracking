# Billable

A full-stack time tracking and invoicing app for agencies. Teams record work by client and project; managers turn those hours into monthly invoices.

**[Try the live demo](https://billable-time-tracking.onrender.com/)**

The demo opens as a manager with sample data. Sign out to try the team member view. The free server may need about a minute to wake up.

## Features

- Start/stop timers, weekly timesheets and live team activity.
- Hourly, retainer and fixed-fee contracts.
- Invoice previews, tax calculation, payment status and CSV exports.
- Dashboards for billable hours, revenue and retainer usage.
- Owner, manager and member permissions.

## Tech stack

**Frontend:** React, TypeScript, Redux Toolkit Query and Material UI.

**Backend:** Django, Django REST Framework, PostgreSQL, Redis, Celery and Channels.

Automated tests, type checks and security scans run in GitHub Actions.

The demo uses shared sample data that resets on restart. See [local setup and deployment](docs/SETUP.md) for installation instructions.
