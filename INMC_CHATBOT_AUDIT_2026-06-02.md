# INMC Chatbot Audit - 2026-06-02

## Verdict

The INMC website has a HighLevel chat widget embedded, but the visitor-facing widget is not currently set up as an AI chatbot.

## Evidence

- Live site pages checked: `/`, `/about.html`, `/testimonials.html`, `/blog.html`
- All four pages return `200` and include widget ID `69cc91e086ec4f5dc6900723`.
- Public widget config returns `location-id: x8il6XPJdeSXlgJFFiCJ`.
- Public widget config shows `chat-type: allInOneChat`.
- Public widget config shows `all-in-one-chat-types: ["liveChat","emailChat"]`.
- Public widget config does not expose an attached AI agent.
- Public widget config shows `agency-name: Care Connect` and `show-agency-branding: true`.
- Public widget config has typo: `live-chat-ack-msg: "Your chat has ende"`.
- INMC GHL has one active Agent Studio agent: `Lead Qualification Agent`.
- Agent ID: `df35e393-0714-4603-8999-bbc80784aac4`.
- Production version exists: `Lead Qualification Agent v1`, version ID `de7b59b9-5313-4589-93d3-ee9c40212ad5`, `state: prod`, `isPublished: true`.
- Production agent chat trigger is disabled: `triggerType: chat`, `enabled: false`.
- Agent prompt is generic B2B qualification using company/need fields, not INMC medical concierge intake.
- Agent runtime variables include an empty key, which is a setup defect.

## What Is Working

- INMC GHL token has read access to location, contacts, workflows, conversations, calendars, custom fields, Agent Studio, and public widget config.
- Location verified as `Integrative Natural Medical Center`.
- Published GHL workflows exist, including `INMC General Concierge` and `Website Lead Notification`.
- Website embeds the same widget ID across all current pages.
- Website lead pipeline exists.

## What Is Not Properly Set Up

- The website widget is live chat/email chat, not AI chat.
- The Agent Studio production chat trigger is disabled.
- The current agent is not trained or prompted for INMC.
- The widget branding is wrong for INMC.
- The widget acknowledgement copy has a typo.
- The existing PIT lacks private chat-widget scopes; private widget list/update APIs returned `401 The token is not authorized for this scope`.

## Required Fix

1. Create or update an INMC-specific AI agent with medical-concierge guardrails.
2. Enable the chat trigger on the production agent or promote a corrected staging version.
3. Attach the agent to the widget used on the website.
4. Update widget branding from `Care Connect` to INMC or disable agency branding.
5. Fix widget acknowledgement copy.
6. Confirm contact collection requires at least name and phone; email should be optional or required depending on clinic preference.
7. Run a live widget test from the website and verify the new conversation lands in the INMC Conversations inbox.

## Approval Gate

Do not mutate the live GHL chatbot/widget without explicit approval. These changes affect real patient-facing chat behavior.
