# Daily Opportunity Dashboard

A personal dashboard that collects and displays public-sector jobs, internships, and youth support programs in one place.

## What It Does

This project is a daily-updated information dashboard focused on:
- public-sector recruitment posts
- internship openings
- youth support and grant programs

The site is designed to reduce manual searching by aggregating opportunity data into a single searchable view.

## Core Features

- Daily automated data updates
- Category filters for jobs, internships, and support programs
- Search by posting title or organization name
- Deadline and region visibility at a glance
- Simple dashboard-style UI for quick scanning

## Stack

- Next.js
- React
- TypeScript
- Tailwind CSS
- custom scraper and data update pipeline
- GitHub Actions for scheduled updates

## Repository Structure

```text
daily-opportunity-dashboard/
├─ .github/workflows/
├─ data/
├─ scraper/
├─ src/app/
├─ package.json
└─ tailwind.config.ts
```

## How It Works

1. Scraper jobs collect source data from supported opportunity sites.
2. Processed results are stored in the repository data layer.
3. GitHub Actions updates the data on a schedule.
4. The Next.js frontend renders the latest opportunities into a searchable dashboard.

## Local Development

```bash
npm install
npm run dev
```

## Deployment

The project is deployed as a web app and currently links to:
- https://chijun.vercel.app/

## Use Case

Useful if you want a focused dashboard for tracking hiring, internship, and support opportunities without checking multiple sites manually every day.
