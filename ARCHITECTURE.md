# System Architecture

## Layers

API

↓

Services

↓

Repositories

↓

Database

Business logic belongs ONLY inside Services.

Repositories never contain business logic.

API routes remain thin.

---

## Modules

AI

Publishing

Scheduler

OAuth

Generation

History

Review

Dashboard

Analytics (future)

---

## External Integrations

OpenAI

LinkedIn OAuth

LinkedIn REST APIs

---

## Future Integrations

Twitter

Medium

Substack

Slack

Microsoft Teams