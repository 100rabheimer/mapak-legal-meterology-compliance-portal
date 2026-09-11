# Legal Metrology Compliance Portal

A React + TypeScript + Tailwind CSS frontend prototype for an AI-assisted packaged-commodity compliance workflow.

## Features

- Responsive enforcement dashboard
- New product inspection and image upload interface
- Mock OCR/extraction progress workflow
- Editable mandatory declaration review screen
- Compliance report with Pass, Warning, and Violation statuses
- Product repository, reports, legal-rules, analytics, and settings placeholder pages
- Structured TypeScript domain models ready for FastAPI integration

## Run locally

```bash
npm install
npm run dev
```

Open the local Vite URL shown in the terminal.

## Backend integration

Set `VITE_API_BASE_URL` in `.env` when the FastAPI backend is available. The application currently uses realistic mock data so the UI can be demonstrated independently.

## Important

This project is a decision-support UI prototype. Before operational use, connect it to a versioned legal-rule repository, preserve source citations and OCR/image evidence, implement secure authentication, audit logging, and ensure final compliance decisions are approved by an authorized officer.
