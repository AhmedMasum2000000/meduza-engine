# CLAUDE.md: meduza-engine

The **Workers** of Project Medusa: Scout, Brief, Create, Publisher, Analyst.

## ⚠️ This repository is PUBLIC

- Never commit secrets, tokens, client names, campaign data, page lists or strategy documents.
- Configuration comes only from environment variables (`.env` is git-ignored; keep `.env.example` with placeholders).
- Plans and strategy live in the private hub repo `project-Medusa`. Link to it; never copy from it.

## Read first (in the private hub `project-Medusa`)

- `CLAUDE.md`: hard rules for every agent
- `docs/03-system/architecture.md` and `docs/03-system/repo-map.md`: job contract with `medusa-backend`
- `docs/BACKLOG.md`: cards F-05 to F-07, F-09, F-10 belong here
- `data/tools.yaml`: which tool does which job

## Rules for this repo

1. Workers never publish directly to a platform with stored tokens. They ask `medusa-backend` for a short-lived publish action after Guard has passed.
2. Scrape **public** data only, rate-limited, respecting robots.txt and platform terms.
3. Create original assets: remake ideas, never re-upload someone else's video.
4. Mark every AI-generated realistic asset with `ai_generated: true` so Guard can add platform labels.
5. Jobs must be idempotent and safe to retry (the GPU machine can lose power mid-job).
