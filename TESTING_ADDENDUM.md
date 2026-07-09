# Testing Addendum

This addendum documents the most relevant tests and verification completed for the newly delivered features.

## 1. Targeted automated tests

### 1.1 Engagement service tests
- File: tests/test_engagement_service.py
- Coverage includes:
  - scan flow behavior
  - queueing logic
  - approval flow
  - invalid post URL or URN skip handling
- Result during delivery: passing

### 1.2 Generated images listing API test
- File: tests/test_content_generated_images_api.py
- Verifies:
  - generated image files are discoverable via topic images endpoint
- Result during delivery: passing

### 1.3 On-demand topic image generation API test
- File: tests/test_content_generate_topic_images_api.py
- Verifies:
  - generate-images endpoint contract
  - successful response shape
- Result during delivery: passing

### 1.4 Health sanity test
- File: tests/test_health.py
- Verifies:
  - service health endpoint is reachable and returns expected status
- Result during delivery: passing

## 2. Manual validation scenarios completed

### 2.1 Engagement fallback path
- Direct scan attempt from LinkedIn
- Collector fallback route invocation
- Manual JSON fallback behavior verification

### 2.2 Engagement queue actions
- Approve only
- Approve and post
- Post now
- Skip
- Validation and skip reasons behavior observed

### 2.3 OAuth and settings workflow
- OAuth readiness panel checks
- Connect flow and redirect validation
- Disconnect control exposed in UI

### 2.4 Generate tab behavior
- Pending topic dropdown render and selection
- Selected topic generation path
- Button disable behavior when no pending topics

### 2.5 Image generation behavior
- Template/size/style input support
- On-demand Generate Visual action
- Generated image listing and open-link behavior

## 3. Known environment warnings seen
- Starlette test client deprecation warning for httpx compatibility path
- UTC naive datetime deprecation warnings in legacy call sites
- These warnings do not currently block core functionality

## 4. Suggested regression suite for next run
1. Run full content, engagement, and publish API tests together
2. Add tests for generate tab selected-topic behavior at API integration layer
3. Add tests for disconnect and reconnect UI flow using browser automation
4. Add tests for collector source with non-empty fixture payload

## 5. Suggested pre-release checklist
1. Validate OAuth redirect URI exact match
2. Reconnect LinkedIn account after scope changes
3. Execute one real engagement post attempt with accessible target
4. Execute one selected-topic generation with image template and size override
5. Confirm queue processing and publish history updates
