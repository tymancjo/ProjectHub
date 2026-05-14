## Project: Website Redesign
**Short Desc:** Full redesign of the company marketing site.
---
#active #cat:product
**10-01-2026** Kickoff meeting with design team. Agreed on a modern, minimal direction.

**28-01-2026** First wireframes reviewed. Mobile-first approach confirmed.

**15-02-2026** Design handoff complete. Development sprint started.

**14-05-2026** Beta version deployed to staging environment.

## Key Goals
- Improve page load time by 40%
- Increase mobile conversion rate
- Refresh brand identity across all pages

## Tasks
TODO: [x] Stakeholder interviews
TODO: [x] Wireframes v1
TODO: [x] Design system tokens
TODO: [ ] Implement component library
TODO: [ ] SEO audit and fixes
TODO: [ ] Accessibility review (WCAG 2.1 AA)
TODO: [ ] Production launch

## Project: ML Pipeline Refactor
**Short Desc:** Rebuild the training and inference pipeline for scale.
---
#active #cat:engineering
**05-03-2026** Identified bottlenecks in the current preprocessing stage — 3× slower than needed.

**20-03-2026** New pipeline architecture agreed upon. Moving to streaming ingestion.

**10-04-2026** Training job parallelization complete. Reduced runtime from 6h to 45min.

**02-05-2026** Inference service containerized and deployed to staging.

## Architecture Notes
The old pipeline ran everything sequentially on a single worker. The new design uses a distributed queue with dedicated workers for each stage.

## Tasks
TODO: [x] Profile existing pipeline
TODO: [x] Design new architecture
TODO: [x] Migrate preprocessing module
TODO: [x] Parallelize training jobs
TODO: [ ] Migrate evaluation module
TODO: [ ] Load test inference service
TODO: [ ] Rollout to production (canary)

## Project: Mobile App v2
**Short Desc:** Major update to the iOS and Android apps.
---
#hold #cat:product
**12-02-2026** Scoping session done. Feature list prioritized with product team.

**01-03-2026** Design mockups for core screens delivered.

**18-03-2026** Development paused — waiting on API team to deliver new endpoints.

## Blocked By
API v3 endpoints are not ready yet. Expected delivery: June 2026.

## Tasks
TODO: [x] Feature scoping
TODO: [x] UX mockups
TODO: [ ] Implement new onboarding flow
TODO: [ ] Integrate push notifications v2
TODO: [ ] Beta testing with user panel
TODO: [ ] App store submission

## Project: Data Warehouse Migration
**Short Desc:** Move from legacy DWH to cloud-native solution.
---
#active #cat:infrastructure
**15-01-2026** Initial audit of existing tables and data volumes completed.

**10-02-2026** Vendor selected after evaluation of three options.

**05-03-2026** Schema mapping document finalized.

**22-04-2026** First 3 data domains migrated and validated.

**14-05-2026** Migration of remaining 7 domains in progress.

## Notes
Legacy system has ~120 tables. Estimated completion: end of Q2 2026.
Data quality checks must pass before each domain is decommissioned.

## Tasks
TODO: [x] Audit legacy schema
TODO: [x] Vendor selection
TODO: [x] Schema mapping
TODO: [x] Migrate domain: CRM
TODO: [x] Migrate domain: Finance
TODO: [x] Migrate domain: Inventory
TODO: [ ] Migrate domain: HR
TODO: [ ] Migrate domain: Logistics
TODO: [ ] Decommission legacy system
TODO: [ ] Final validation and sign-off

## Project: Security Audit Q1
**Short Desc:** Annual penetration test and vulnerability remediation.
---
#done #cat:infrastructure
**08-01-2026** Engaged external security firm. Scope agreed.

**20-01-2026** Pen test execution window (1 week). No critical findings.

**27-01-2026** Report received. 2 high, 5 medium, 12 low severity findings.

**14-02-2026** All high and medium findings remediated and verified.

**28-02-2026** Final sign-off received. Audit closed.

## Summary
Clean result overall. Main high-severity finding was an exposed internal API endpoint — patched within 48h of discovery.

## Tasks
TODO: [x] Kick off with security vendor
TODO: [x] Pen test execution
TODO: [x] Review findings report
TODO: [x] Remediate high severity issues
TODO: [x] Remediate medium severity issues
TODO: [x] Obtain sign-off

## Project: Team Onboarding Docs
**Short Desc:** Build a comprehensive onboarding guide for new engineers.
---
#backlog #cat:people
## Planned Content
- Development environment setup
- Architecture overview
- Coding standards and review process
- Deployment runbook
- Incident response guide

**03-04-2026** Initial outline drafted after feedback from last three new hires.

## Tasks
TODO: [x] Collect pain points from recent hires
TODO: [x] Draft outline
TODO: [ ] Write dev environment setup guide
TODO: [ ] Write architecture overview
TODO: [ ] Write deployment runbook
TODO: [ ] Review cycle with team leads
TODO: [ ] Publish to internal wiki
