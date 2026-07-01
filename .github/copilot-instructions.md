# LinkedIn AI Studio - AI Development Instructions

## Project Overview

This repository contains a production-grade LinkedIn AI Content Automation Platform built using FastAPI.

The project is developed incrementally using versioned commits.

Current Stable Version:

v0.5.0

Current Development Target:

Commit 6 — LinkedIn Integration

Do NOT redesign the architecture.

Always extend the existing architecture.

---

# Architecture

This project follows strict layered architecture.

API
↓

Services
↓

Repositories
↓

SQLAlchemy Models
↓

Database

Business logic MUST remain inside Services.

Repositories MUST only access the database.

API routers MUST remain thin.

Never place business logic inside API routes.

---

# Technology Stack

Python 3.12

FastAPI

SQLAlchemy ORM

Pydantic

Alembic

SQLite (development)

OpenAI API

APScheduler

Jinja2

pytest

---

# Folder Structure

app/

api/

services/

repositories/

db/

models/

schemas/

core/

config/

utils/

ai/

tests/

migrations/

prompt_templates/

Never introduce unnecessary folders.

Follow the existing structure.

---

# Coding Standards

Use type hints everywhere.

Use dependency injection.

Keep functions small.

Avoid duplicate logic.

Prefer composition over inheritance.

Never hardcode secrets.

Never hardcode URLs.

Never hardcode API keys.

Read configuration from Settings.

---

# Repository Layer Rules

Repositories perform ONLY database operations.

Repositories must never call external APIs.

Repositories must never contain AI logic.

Repositories must never contain scheduling logic.

Repositories return ORM objects.

---

# Service Layer Rules

Services contain all business logic.

Services coordinate repositories.

Services call OpenAI.

Services call LinkedIn APIs.

Services perform validation.

Services perform retries.

Services may call multiple repositories.

---

# API Layer Rules

API routes should:

Validate request

Call service

Return response

Nothing else.

Never perform database operations directly.

---

# Database Rules

Always use SQLAlchemy ORM.

Never use raw SQL unless absolutely necessary.

Prefer relationships over manual joins.

Always create migrations for schema changes.

Never drop existing tables.

Maintain backward compatibility.

---

# Error Handling

Raise HTTPException only inside API layer.

Raise custom exceptions inside Services.

Log every unexpected exception.

Never swallow exceptions silently.

---

# Logging

Use the project logger.

Every external API call should be logged.

Every publish attempt should be logged.

OAuth flow should be logged.

Scheduler actions should be logged.

Never use print().

---

# Security

Never expose:

Access Tokens

Refresh Tokens

API Keys

Secrets

Passwords

Encrypt LinkedIn tokens before storing.

Use environment variables.

Validate OAuth state.

Implement CSRF protection.

---

# Testing

Every new feature should include:

Repository tests

Service tests

API tests

Regression tests

Do not break existing tests.

---

# Documentation

Update Swagger for every endpoint.

Update request models.

Update response models.

Update README when introducing major features.

---

# Versioning

Current Stable Version:

v0.5.0

Next Target:

v0.6.0

Never modify frozen Commit 5 functionality unless fixing a bug.

---

# Commit 6 Scope

Commit 6 implements LinkedIn integration.

Included:

OAuth 2.0

Token Storage

Token Refresh

LinkedIn Account

Profile Retrieval

Publishing

Media Upload

Publish Queue

Retry Logic

Scheduler Integration

Publish Dashboard

Publish History

Connection Status

Manual Publish

Scheduled Publish

Do not implement analytics.

Do not implement AI Studio features.

---

# Commit 7 Scope

Commit 7 begins AI Studio.

Includes:

Prompt Templates

Personas

Brand Voice

Content Calendar

Analytics

Bulk Generation

Image Generation

Quality Score

Do NOT implement Commit 7 while working on Commit 6.

---

# Code Quality

Prefer readability over cleverness.

Avoid long methods.

Avoid duplicated code.

Reuse services.

Reuse repositories.

Maintain consistent naming.

Follow PEP8.

---

# Dependency Rules

Never add a new dependency unless required.

Prefer built-in Python modules.

Document every new dependency.

---

# AI Behavior Rules

Before modifying code:

Understand existing architecture.

Search for similar implementations.

Reuse existing patterns.

Do not rewrite working modules.

Modify the minimum number of files.

Explain planned changes before implementation.

If unsure:

Ask for clarification.

Never guess API contracts.

Never invent database schema.

Never fabricate LinkedIn API responses.

---

# Output Rules

When implementing a feature:

1. Explain the design.

2. List files to modify.

3. Apply changes.

4. Explain why each change was made.

5. Suggest tests.

6. Wait for user verification before continuing.

---

# General Principle

The goal is not merely to generate code.

The goal is to build a maintainable, production-quality LinkedIn AI platform that follows consistent architecture across every commit.Always follow the frozen architecture and coding standards.