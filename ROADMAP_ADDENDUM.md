# Roadmap Addendum

This addendum captures near-term delivery priorities based on what is already implemented.

## 1. Immediate stabilization priorities

### 1.1 OAuth reliability and diagnostics
- Add explicit token scope visibility endpoint and UI panel
- Add clearer redirect URI mismatch hints in settings
- Add reconnect helper flow in UI guidance

### 1.2 Engagement execution reliability
- Add optional toggle to bypass accessibility pre-check for controlled troubleshooting
- Add explicit reason categories for skipped records
- Add cleaner queue filtering by status and date

### 1.3 Collector maturity
- Add standardized collector input file contract and schema example
- Add sample fixture under data path for out-of-box fallback runs
- Add topic matching quality metrics in collector mode

## 2. Product capability expansion

### 2.1 Mobile compatibility
- Responsive layout for all major panels and forms
- Mobile-friendly table to card conversion for dense screens
- Drawer/modal interaction polish for touch devices

### 2.2 Cross-platform publishing scale-up
- Phase 1: X and Medium adapters
- Phase 2: Instagram visual-first workflows
- Phase 3: Threads and Substack expansion
- Phase 4: short-video pipeline for YouTube Shorts

### 2.3 Advanced content operations
- Multi-platform variant generation from one topic
- Per-platform scheduling windows and constraints
- Performance feedback loop to tune prompts automatically

## 3. Testing roadmap
1. Expand integration tests around engagement skip and approval outcomes
2. Add regression tests for selected pending topic generate flow
3. Add automated browser tests for OAuth connect/disconnect controls
4. Add collector-mode test fixtures and edge-case coverage

## 4. API and docs roadmap
1. Merge addendum references into canonical API docs once stable
2. Publish candidate JSON schema examples in developer docs
3. Add troubleshooting section for LinkedIn access and 403 scenarios

## 5. Suggested milestone framing

### Milestone A
- OAuth diagnostics
- Collector schema hardening
- Engagement operational observability

### Milestone B
- Mobile pass for all tabs
- UX polish and high-priority responsive fixes

### Milestone C
- Multi-platform publish adapters for X and Medium
- Unified content variant workflow

### Milestone D
- Analytics-driven optimization and quality scoring expansion
- Deeper automation for trend-to-post pipelines
