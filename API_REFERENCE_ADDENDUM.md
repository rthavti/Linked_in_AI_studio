# API Reference Addendum

This document captures APIs and behavior added or clarified during the latest delivery cycle.

Base URL
- Local: http://127.0.0.1:8001

## 1. Engagement APIs

### 1.1 Get settings
- Method: GET
- Path: /engagement/settings
- Response: engagement settings payload including topic configs

### 1.2 Update settings
- Method: PUT
- Path: /engagement/settings
- Body: partial settings payload
- Response: updated settings

### 1.3 Scan with explicit candidates
- Method: POST
- Path: /engagement/scan
- Body:
  - candidates: array of candidate posts
  - style: optional
  - auto_post: boolean
- Response:
  - searched
  - relevant
  - queued_for_review
  - posted
  - skipped

### 1.4 Direct scan from LinkedIn
- Method: POST
- Path: /engagement/scan-direct
- Body:
  - topics: optional array of topic config
- Response:
  - searched
  - relevant
  - queued_for_review
  - posted
  - skipped
  - searched_by_topic
- Note: availability depends on LinkedIn app access and token permissions

### 1.5 Collector scan fallback
- Method: POST
- Path: /engagement/scan-collector
- Body:
  - topics: optional array of topic config
- Response:
  - searched
  - relevant
  - queued_for_review
  - posted
  - skipped

### 1.6 Run daily engagement scan
- Method: POST
- Path: /engagement/run-daily
- Response:
  - searched
  - relevant
  - queued_for_review
  - posted
  - skipped

### 1.7 List comments
- Method: GET
- Path: /engagement/comments
- Query:
  - status: optional
  - limit: optional
- Response: array of engagement comment records

### 1.8 Approve comment
- Method: POST
- Path: /engagement/comments/{history_id}/approve
- Body:
  - edited_comment: optional
  - post_now: boolean
- Response: updated comment record

### 1.9 Skip comment
- Method: POST
- Path: /engagement/comments/{history_id}/skip
- Body:
  - reason: optional
- Response: updated comment record

### 1.10 Analytics
- Method: GET
- Path: /engagement/analytics
- Query:
  - days: optional
- Response: aggregate engagement analytics

## 2. Content and image generation APIs

### 2.1 Generate content
- Method: POST
- Path: /content/generate
- Body options include:
  - generate_images
  - image_count
  - image_style_hint
  - visual_template
  - image_size
- Response: generated topic payload

### 2.2 List generated images for topic
- Method: GET
- Path: /content/{topic_id}/images
- Response:
  - topic_id
  - image_urls
  - image_error

### 2.3 Generate images for an existing topic
- Method: POST
- Path: /content/{topic_id}/generate-images
- Body:
  - image_count
  - image_style_hint
  - visual_template
  - image_size
- Response:
  - topic_id
  - image_urls
  - image_error

### 2.4 Enhance content
- Method: POST
- Path: /content/{topic_id}/enhance
- Body:
  - engagement_type
  - extra_keywords
  - hashtag_count
- Response: optimized post and suggestions

## 3. Topic generation targeting API behavior

### 3.1 Regenerate selected topic
- Method: POST
- Path: /topics/{topic_id}/regenerate
- Body supports:
  - template_name
  - prompt_version
  - generate_images
  - image_count
  - image_style_hint
  - visual_template
  - image_size
- Used by Generate tab dropdown-based selected topic flow

## 4. OAuth and publish APIs

### 4.1 Start OAuth
- Method: GET
- Path: /publish/connect
- Response: authorize_url, state

### 4.2 OAuth callback
- Method: GET
- Path: /publish/callback
- Query:
  - code
  - state
- Response: account_id on success

### 4.3 OAuth health
- Method: GET
- Path: /publish/oauth/health
- Response: configuration and connection status details

### 4.4 Disconnect account
- Method: POST
- Path: /publish/disconnect
- Response: success boolean

### 4.5 Publish now
- Method: POST
- Path: /publish/topics/{topic_id}/now
- Response: publish result

### 4.6 Queue and history
- GET /publish/queue
- POST /publish/queue
- POST /publish/queue/{queue_id}/retry
- GET /publish/history

## 5. Error and access notes
- Direct LinkedIn search can return access errors if product-level permission is unavailable
- Post validation can skip inaccessible targets with explicit skip reason
- OAuth redirect URI must match exactly between app and LinkedIn Developer settings
