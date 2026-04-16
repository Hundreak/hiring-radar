# Hiring Radar Frontend Scaffold — 13A-1A

This package is the first frontend foundation phase.

## What is included
- Next.js App Router foundation
- Multilingual routing with `next-intl` (`tr`, `en`, `de`)
- Theme system with `next-themes`
- Public landing shell
- Auth shells (`/login`, `/signup`)
- App shells (`/jobs`, `/matches`, `/saved`)
- Settings route shells
- Profile completion card
- Education + phone placeholders in profile settings

## What is deliberately not included yet
- Real backend API integration
- Signup API
- Password / magic-link backend wiring
- Real jobs API
- Saved jobs persistence
- Explainable matching
- Profile form persistence

## Suggested placement
Put this folder at:

```text
~/projects/hiring-radar/frontend
```

## Install
```bash
cd frontend
npm install
npm run dev
```

## Route examples
- `/tr`
- `/tr/login`
- `/tr/signup`
- `/tr/jobs`
- `/tr/matches`
- `/tr/settings/profile`
