# INMC Chatbot Verification

- Timestamp: `2026-06-02T19:15:26.424588+00:00`
- Overall OK: `False`

## Checks

- `PASS` env has INMC token and location: `{"has_token": true, "token_length": 40, "location_id": "x8il6XPJdeSXlgJFFiCJ"}`
- `PASS` live pages embed expected widget: `{"pages": [{"route": "/", "status": 200, "widget_present": true, "loader_present": true}, {"route": "/about.html", "status": 200, "widget_present": true, "loader_present": true}, {"route": "/testimonials.html", "status": 200, "widget_present": true, "loader_present": true}, {"route": "/blog.html", "status": 200, "widget_present": true, "loader_present": true}]}`
- `PASS` GHL location is INMC: `{"status": 200, "name": "Integrative Natural Medical Center"}`
- `PASS` public widget config belongs to INMC: `{"status": 200, "location_id": "x8il6XPJdeSXlgJFFiCJ"}`
- `PASS` widget is AI capable: `{"chat_type": "allInOneChat", "chat_types": ["liveChat", "emailChat"]}`
- `FAIL` widget branding is INMC or disabled: `{"show_agency_branding": true, "agency_name": "Care Connect"}`
- `FAIL` widget acknowledgement copy is clean: `{"live_chat_ack_msg": "Your chat has ende"}`
- `FAIL` token has private chat widget scope: `{"status": 401, "error": "The token is not authorized for this scope."}`
- `PASS` Agent Studio production agent exists: `{"status": 200, "agent_name": "Lead Qualification Agent", "agent_status": "active", "prod_version_id": "de7b59b9-5313-4589-93d3-ee9c40212ad5", "prod_is_published": true}`
- `FAIL` production chat trigger enabled: `{"triggers": [{"nodeId": "14a173a7-bab5-46f6-82eb-9a85b297595f", "display": "Chat message", "type": "chat", "enabled": false}]}`
- `FAIL` production prompt is INMC specific: `{"prompt_count": 8, "has_company_word": true}`
- `FAIL` runtime variable keys are non empty: `{"runtime_keys": ["leadQuality", "", ""]}`
- `FAIL` Website Leads pipeline uses clinic intake stages: `{"status": 200, "pipeline_id": "rjCeIQeulTJy5B8laSfm", "current_stages": ["New Lead", "Contacted", "Proposal Sent", "Closed"]}`

## Required Before Complete

- Widget must expose or use an AI capable chat path, not live/email chat only.
- Widget branding must be INMC or agency branding must be disabled.
- Widget acknowledgement typo must be fixed.
- Production chat trigger must be enabled.
- Production agent prompt must be INMC medical concierge specific.
- Runtime variable keys must be non empty.
- Website Leads pipeline must use clinic intake stages.
