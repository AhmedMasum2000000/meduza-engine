# meduza-engine

Workers for an automated content pipeline: **Scout → Brief → Create → Publish → Learn**.

> Status: **planned, not built yet.**

## What the workers do

| Worker | Job |
|---|---|
| **Scout** | Finds trending and outlier content from public sources (YouTube, Google Trends, TikTok Creative Center) and scores it |
| **Brief** | Turns signals into content briefs: hook, angle, format, languages |
| **Create** | Produces assets: template videos (Remotion), faceless shorts (MoneyPrinterTurbo), captions (Whisper), voice-overs (Edge TTS), images (ComfyUI) |
| **Publisher** | Sends approved assets to the scheduler (Postiz API) |
| **Analyst** | Pulls post metrics back for scoring |

Workers are stateless. They pull jobs from a Redis queue, call tools, and report results back to the API. Heavy jobs (video, image, local LLM) can run on a separate GPU machine that only needs queue access.

## Planned stack

Python 3.12 workers · FFmpeg · Remotion (Node) · faster-whisper · Edge TTS · ComfyUI and Ollama clients · Redis.

## Public repository

This repo is public. It contains **code only**: no API keys, no tokens, no client data. Configuration comes from environment variables at runtime (see `.env.example`).

## Presentation

`presentation/index.html` is the Project Medusa pitch page, published here so it has a public link.
Live preview: https://htmlpreview.github.io/?https://github.com/AhmedMasum2000000/meduza-engine/blob/ccr-8f04d111-vqbro0/presentation/index.html
