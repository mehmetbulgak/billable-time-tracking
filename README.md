# Billable

[Open the live demo](https://billable-time-tracking.onrender.com/)

Time tracking and invoicing for agencies. Team members track their hours against client projects, and managers turn each month's time into invoices based on the client's contract.

![Dashboard](docs/screenshots/dashboard.png)

## Features

- Start/stop timer and a weekly timesheet
- Live "who's working now" view over WebSockets
- Hourly, monthly retainer (with overage and rollover) and fixed-fee contracts
- Monthly invoice generation with preview, tax, sequential numbering and CSV export
- Dashboard with tracked vs billable hours, retainer usage and revenue
- Owner, manager and member roles

## Tech stack

**Backend:** Python 3.13, Django 6, Django REST Framework, Django Channels, Celery, PostgreSQL, Redis, JWT authentication, OpenAPI (drf-spectacular), pytest

**Frontend:** React 19, TypeScript, Vite, Redux Toolkit Query, Material UI, React Hook Form, Zod, Vitest

**Tooling:** Docker Compose, nginx, GitHub Actions, Ruff, mypy, ESLint, Prettier
