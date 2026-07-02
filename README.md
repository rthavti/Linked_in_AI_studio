# LinkedIn AI Studio

Production-grade AI-powered LinkedIn Content Studio.

## Latest Feature Slice

- Rich LinkedIn preview with editable drafts, draft saving, and approve-from-preview support.
- Optional global auto scheduling defaults with a manual per-topic scheduler as the primary workflow.
- LinkedIn OAuth readiness checks and connect helper block in Settings.
- Shared pytest fixture isolation for reliable regression coverage across scheduler, settings, and preview flows.

## LinkedIn OAuth Setup

To connect LinkedIn, configure the app in the LinkedIn Developer Portal and then mirror those values in your local `.env` file.

For safer multi-user deployments, keep credentials out of the browser UI and maintain one `.env` per environment or deployment.

Required values:

- `LINKEDIN_CLIENT_ID`
- `LINKEDIN_CLIENT_SECRET`
- `LINKEDIN_REDIRECT_URI` must be `http://127.0.0.1:8000/publish/callback` for local development.
- `LINKEDIN_SCOPES` should include the scopes enabled in your LinkedIn app.
- `LINKEDIN_TOKEN_SECRET`

The app does not generate LinkedIn credentials. It reads them from environment variables and uses the LinkedIn API for the OAuth handshake, token exchange, and publishing requests.

## Release v0.5.0

- Added review workflow and manual review endpoints.
- Added generation history tracking with prompt/version metadata.
- Added Swagger response documentation for topic and content endpoints.
- Fixed regeneration persistence so generated content is stored in topic and history records.

## Commit 6 (scaffold): LinkedIn OAuth & publishing

This commit adds scaffolding for LinkedIn OAuth-based publishing. To complete OAuth end-to-end you must provide the following environment variables (see `app/config/settings.py`):

- `LINKEDIN_CLIENT_ID`
- `LINKEDIN_CLIENT_SECRET`
- `LINKEDIN_REDIRECT_URI` (must match your LinkedIn app settings)
- `LINKEDIN_TOKEN_SECRET`

Local testing notes:
- Database will store LinkedIn accounts in the `linkedin_accounts` table.
- Use the `/publish/connect` and `/publish/callback` endpoints to complete the OAuth flow during manual testing.
- Use `/publish/queue` for scheduled publish attempts and `/publish/topics/{topic_id}/now` for manual publishing.
