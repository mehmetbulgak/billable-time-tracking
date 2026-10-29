# Billable

Time tracking and invoicing for agencies. Team members track their hours against client projects, and managers turn each month's time into invoices based on the client's contract.

![Dashboard](docs/screenshots/dashboard.png)

## Public portfolio demo

The Render demo opens directly as the demo manager, with sample clients, contracts,
timesheets and invoices. Sign out to try the team-member account from the login page.

The deployment in `deploy/Dockerfile` runs the original Django API and PostgreSQL
alongside the built React app on one free Render web service. It uses a single
Daphne process with an in-memory Channels layer and eager Celery tasks; emails are
discarded. The normal production settings and Docker Compose stack remain available.

This is a disposable, shared demo: all sample data is recreated on startup and
changes are lost on service restarts. Do not enter real client or personal data.
Render's free service sleeps after inactivity, so the first visit can take about
a minute to start. See `render.yaml` for repeatable free-plan configuration.

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
