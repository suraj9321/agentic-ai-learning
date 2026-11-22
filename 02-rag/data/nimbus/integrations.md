---
title: Integrations and API
updated: 2026-08-11
---
# Integrations and API

## Meeting platforms

- **Zoom**: available on Starter and above. Nimbus joins as a participant called
  "Nimbus Notetaker".
- **Google Meet**: available on all plans, including Free.
- **Microsoft Teams**: beta, Pro and Enterprise only. Recording of Teams webinars is not
  supported yet.

## Calendars

Google Calendar and Microsoft Outlook calendars are supported. Nimbus only reads events that
contain a meeting link and never edits your calendar.

## Slack

Available on Starter and above. After each meeting Nimbus can post the summary and action
items to a Slack channel. Choose the channel per meeting series in Settings → Integrations →
Slack. Action items can be sent as Slack reminders to the person they are assigned to.

## Notion and other exports

Pro and Enterprise can export summaries to Notion automatically (one page per meeting in a
database you choose). All plans can export a transcript as TXT, DOCX or SRT subtitles.

## CRM

HubSpot and Salesforce integrations are Enterprise-only. They attach the summary of sales
calls to the matching deal or contact, matched by attendee email address.

## Public API

The REST API is available on Pro and Enterprise. Create an API key in Settings → Developer.
Base URL: https://api.nimbus.example/v2. Main endpoints:
- `GET /meetings`: list meetings, newest first, 50 per page
- `GET /meetings/{id}/transcript`: the full transcript with speaker labels
- `GET /meetings/{id}/summary`: summary and action items as JSON
- `POST /uploads`: upload an audio or video file for processing

The default rate limit is 60 requests per minute per workspace (see error ERR-2201).
Webhooks can notify your server when a summary is ready (event: `summary.completed`).
