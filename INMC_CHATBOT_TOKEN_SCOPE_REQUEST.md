# INMC Chatbot Token Scope Request

## Current Blocker

No local GHL token can update or attach the INMC private chat widget.

Latest proof:

- `reports/inmc-ghl-scope-probe-20260602T191850214460Z.json`
- `privateWidgetTokenFound: false`
- `GHL_INMC_PIT` can read INMC Agent Studio but returns `401 The token is not authorized for this scope` for private `chat-widget` APIs.
- `GHL_AGENCY_API_KEY` can read the INMC location but also returns `401` for private `chat-widget` APIs and Agent Studio.

## Needed Token Change

In the INMC sub-account Private Integrations settings, create or update a PIT for location:

`x8il6XPJdeSXlgJFFiCJ`

Required access:

- Chat Widget read access
- Chat Widget write access
- Agent Studio read access
- Agent Studio write access
- Opportunities or pipelines read/write access if pipeline stages should be updated by script
- Contacts, conversations, and notes read/write access for final live QA

Preferred env var name:

`GHL_INMC_CHATBOT_PIT`

After adding it to `/Users/danielaroustamian/.env`, test with:

```bash
python3 scripts/probe_inmc_ghl_scopes.py --write-report
python3 scripts/prepare_inmc_chatbot_repair.py --token-env GHL_INMC_CHATBOT_PIT --write-report
python3 scripts/verify_inmc_chatbot.py --token-env GHL_INMC_CHATBOT_PIT --write-report
```

## Live Repair Approval

Even with the scoped token, do not run live apply until explicitly approved because these changes affect patient-facing chat behavior.

