---
title: Security, privacy and data retention
updated: 2026-07-20
---
# Security, privacy and data retention

## Certifications

Nimbus is SOC 2 Type II certified (renewed every year) and GDPR compliant. We sign a Data
Processing Agreement (DPA) with any paid customer on request. HIPAA compliance is not
offered, so Nimbus should not be used to record meetings that contain patient health data.

## Encryption

All data is encrypted in transit with TLS 1.3 and at rest with AES-256. Encryption keys are
managed in a cloud key management service and rotated every 90 days. Enterprise customers
can bring their own key (BYOK).

## Where data is stored

By default all data is stored in the United States (us-east). Enterprise customers can choose
EU data residency (Frankfurt), in which case recordings, transcripts and summaries never
leave the EU. Data residency cannot be changed after a workspace is created.

## Data retention

How long recordings and transcripts are kept depends on the plan:
- Free: 30 days
- Starter: 90 days
- Pro: 1 year
- Enterprise: configurable, from 7 days to forever

Deleted data is removed from backups within 35 days.

## AI and your data

Nimbus uses third-party large language models to write summaries. Your meeting content is
never used to train any AI model, ours or our providers'. Model providers process data
under zero-data-retention agreements.

## Access control

Pro and Enterprise workspaces can restrict who sees each recording (private, team, or whole
workspace). Enterprise adds SAML SSO with Okta, Azure AD and Google Workspace, plus SCIM for
automatic user provisioning, and an audit log of every access to a recording.

## Reporting a vulnerability

Email security@nimbus.example. We run a responsible-disclosure programme and reply within
2 business days.
