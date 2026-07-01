# LinkedIn AI Studio

Production-grade AI-powered LinkedIn Content Studio.

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
