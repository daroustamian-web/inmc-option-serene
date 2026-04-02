# INMC Website — Project Context

## Live URLs
- **Homepage**: https://inmc-option-1.vercel.app
- **About**: https://inmc-option-1.vercel.app/about.html
- **Testimonials**: https://inmc-option-1.vercel.app/testimonials.html
- **Blog**: https://inmc-option-1.vercel.app/blog.html

## Current State
Single-file static site (HTML + Tailwind CDN + Iconify) deployed on Vercel with a serverless API route for contact form → GHL integration. 4 pages total. GHL chat widget embedded on all pages.

## What Was Built This Session

### Pages
- **Homepage** (index.html) — Hero, philosophy section, clinical care section, promo video (Wistia), 14 service cards with AI-generated images, Google Reviews widget (Elfsight), FAQ accordion, social connect section, contact form, footer
- **About** (about.html) — Dr. Santiago bio, clinic mission, professional headshot, consultation photos, credentials bar
- **Testimonials** (testimonials.html) — Elfsight Google Reviews widget, "Leave a Review" CTA
- **Blog** (blog.html) — 9 blog post cards linking back to WordPress originals

### Integrations
- **GHL Contact Form** — `/api/contact.js` serverless function creates contacts in INMC sub-account (location: `x8il6XPJdeSXlgJFFiCJ`, token: `pit-903b...0178`) with tags `website lead` + `contact form`, adds note with message
- **GHL Email Notification** — Workflow triggered by `website lead` tag sends email to `info@dramaliyasantiago.com`
- **GHL Chat Widget** — Elfsight widget ID `69cc91e086ec4f5dc6900723` on all pages
- **Elfsight Google Reviews** — Widget ID `bcda75e8-99ac-4823-81aa-59029b5d8bd0` on homepage + testimonials page
- **GHL MCP** — Added `inmc-ghl-mcp` to `.claude.json` (needs session restart to activate)

### SEO Implemented
- Keyword-optimized meta titles + descriptions on all 4 pages
- Open Graph + Twitter Card tags on all pages
- Canonical URLs on all pages
- Schema markup: MedicalClinic + Physician + WebSite (homepage)
- robots.txt (blocks /api/, tracking params)
- sitemap.xml (4 pages)
- vercel.json security headers + cache rules

### Copy Overhaul (Affluent Positioning Framework)
All copy rewritten to emphasize outcomes, expertise, customization, exclusivity, and long-term results:
- "Precision medicine for patients who've outgrown conventional answers"
- "Most doctors treat what's wrong. We rebuild what's right."
- "One clinic. Fourteen protocols. Zero guesswork."
- "Root-cause medicine. By appointment only."
- Service descriptions lead with outcomes, not process
- See `/Users/danielaroustamian/.claude/plans/dreamy-giggling-bunny.md` for full copy plan

### Images
- **Logo**: `images/logo.webp` — actual INMC blue flower logo
- **Dr. headshot**: `images/dr-headshot.jpg` — professional portrait (black blazer)
- **Consultation**: `images/consultation-2.png` — Dr. Santiago with patients + ozone machine
- **11 service images**: `images/services/*.png` — generated via Nano Banana Pro (Google AI Studio)

### Design Decisions
- Solid white nav bar (not glassmorphic) — logo has white background, transparency looked bad
- Hamburger mobile menu on all pages
- All CTAs go to `#contact-form` (not tel: links) per client request
- Removed: 4.5 star rating (client didn't like it), fake "Limited Spots" urgency bar, testimonial slider (replaced with Elfsight widget), consultation.jpg broken image
- 14 services: original 11 + Peptide Therapy, Medical Weight Loss, Pain Management

## Client Info
- **Business**: Integrative Natural Medical Clinic (INMC)
- **Doctor**: Dr. Amaliya Santiago, ND
- **Address**: 301 S Fair Oaks Ave #401, Pasadena, CA 91105
- **Phone**: (626) 714-7400 / (833) 269-3526
- **Email**: info@dramaliyasantiago.com
- **GHL Location ID**: x8il6XPJdeSXlgJFFiCJ
- **Google Place ID**: ChIJ1UCoYPbDwoARoKG5Lno8QOA

## Next Steps
- [ ] Point real domain (`integrativenaturalmedicalclinic.com`) to Vercel — then swap all canonical URLs and add the 50+ 301 redirects from `~/inmc-seo-package/vercel.json`
- [ ] Submit sitemap to Google Search Console
- [ ] Set up GHL Conversation AI bot (trained on clinic info, connected to web chat)
- [ ] Set up GHL missed call text-back workflow
- [ ] Set up GHL automated review request workflow (post-appointment)
- [ ] Set up GHL pipeline: New Lead → Discovery Call → Consultation → Active Patient
- [ ] Create individual service pages for SEO (each service = separate URL = separate ranking)
- [ ] Compress service images to WebP (~7MB → ~1.5MB)
- [ ] Replace AI-generated service images with real clinic photos when available
- [ ] Verify social media handles are correct (Facebook, Instagram, Yelp URLs)
- [ ] Update GBP website URL to point to new site

## Key Gotchas
- GHL MCP tokens are location-scoped. `prod-ghl-mcp` = Care Connect parent, `adhc-ghl-mcp` = ADHC, `inmc-ghl-mcp` = INMC. Can't cross-query.
- GHL Agent Studio and Conversation AI have NO API — UI-only setup
- GHL `/conversations/messages` sends TO contacts, not internal notifications. Use workflows for clinic notifications.
- Contact form tags are lowercase (`website lead` not `Website Lead`) — GHL workflow trigger must match case
- Elfsight widget is on their free plan — may show "powered by Elfsight" branding
- Blog posts link to WordPress originals — will need redirect mapping when domain moves

## SEO Package Reference
Full SEO package at `~/inmc-seo-package/`:
- `meta-tags.json` — optimized tags for 18 pages (including individual services)
- `schema-homepage.json` — MedicalClinic + WebSite schema
- `schema-physician.json` — Dr. Santiago credentials schema
- `schema-service-template.json` — FAQPage schemas for all services (rich snippets)
- `robots.txt` — production version with WP blocks
- `sitemap-config.json` — full sitemap with 21 URLs and priority notes
- `vercel.json` — 50+ redirects + security headers (deploy when domain is pointed)
