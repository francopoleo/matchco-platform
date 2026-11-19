# MatchCo - Execution Playbook

**Roadmap Operacional: 12 Meses para PMF + Tração**

---

## Fase 1: Meses 0-4 — Build PMF (Product-Market Fit)

### Objetivo: Validar que existe mercado dispostos a pagar

**Métricas de Sucesso:**
- 3-5 paying customers (closed deals)
- NPS > 30
- Retention > 85%
- Churn < 10% (monthly)

---

### Sprint 1 (Semanas 1-4): Preparar Product & Docs

**Deliverables:**
1. **Setup Wizard** (admin console)
   - [ ] Domain provisioning (tenant creation)
   - [ ] Organization hierarchy (Org → Company → BU → OU)
   - [ ] User bulk import (CSV)
   - [ ] HRIS integration selector (Gupy, Kenoby, Workday)
   - [ ] Initial course template (e.g., "Onboarding 101")
   - Est. effort: 40 hours

2. **Admin Dashboard**
   - [ ] Analytics overview (users, courses, recruitment funnel)
   - [ ] LGPD compliance status (audit trail viewer)
   - [ ] Integration status (health checks)
   - Est. effort: 30 hours

3. **Getting Started Guide** (HTML + video)
   - [ ] 5-minute setup video (PT-BR + EN)
   - [ ] Step-by-step guide (PDF + web)
   - [ ] FAQ (top 20 questions)
   - Est. effort: 20 hours

4. **Demo Data Script**
   - [ ] Pre-populated tenant (users, courses, positions)
   - [ ] Script for creating demo orgs
   - [ ] Use cases: education, retail, startup
   - Est. effort: 15 hours

**Total Effort:** ~100 hours (2 devs, 2-3 weeks)

---

### Sprint 2 (Semanas 5-8): Validar & Refine

**Objective:** Primeiro customer pilot

**Activities:**
1. **Outbound Prospecting** (BD lead + 1 co-founder)
   - [ ] Create target list (30 companies)
     - 5 universities (education vertical)
     - 10 retail chains (100-500 employees)
     - 5 startups (LATAM, 50-200 employees)
     - 10 HR consultants (potential partners)
   - [ ] LinkedIn + cold email campaign (personalized)
   - [ ] Target response rate: 10-15%
   - Est. effort: 80 hours (outreach + meetings)

2. **Customer Discovery Calls** (2 founder + 1 PM)
   - [ ] 10-15 conversations (30 mins each)
   - [ ] Questions: "What's the #1 HR problem you face?"
   - [ ] Record problems + willingness to pay
   - [ ] Document in Airtable
   - Est. effort: 20 hours

3. **Product Refinement** (PM + 2 devs)
   - [ ] Fix top 10 bugs found in calls
   - [ ] Prioritize features based on feedback
   - [ ] Update roadmap
   - Est. effort: 40 hours

**Expected Output:**
- 3-5 prospects qualified (willing to pilot)
- Feature roadmap validated against customer problems
- 1-2 pilot contracts signed

---

### Sprint 3 (Semanas 9-12): Pilot Customers

**Objective:** Get first 1-2 paying customers (minimal implementation)

**Playbook per Customer Type:**

#### Tipo A: Universidade (Education Pilot)

```
Customer: XYZ University (1000 students, 100 professors)

Week 1 (Setup):
  • Setup tenant (university domain)
  • Create 3 demo courses (Python 101, Management 101, Soft Skills)
  • Import users (100 professors, 500 student sample)
  • Enable LGPD consent for students
  • Estimated hours: 30 (dev) + 10 (BD)

Week 2 (Integration):
  • Connect to university LDAP (for SSO)
  • Import existing courses (from Moodle/Blackboard)
  • Setup recruitment (job postings for internships)
  • Training (30 mins webinar)
  • Estimated hours: 20 (dev) + 5 (BD)

Week 3 (Validation):
  • Pilot launch with 50 students
  • Collect feedback (NPS survey)
  • Bug fixes daily
  • Estimated hours: 15 (support)

Week 4 (Contract):
  • Sign 12-month deal ($30-50k ACV)
  • Plan Phase 2 (full migration)
  • Estimated hours: 5 (BD)

Contract Terms:
  - Implementation: $5-10k
  - Software: $2.5-4k/month
  - Commitment: 12 months
```

#### Tipo B: Retail Chain (Hospitality Pilot)

```
Customer: ABC Retail (500 employees, 30 stores)

Week 1 (Setup):
  • Setup tenant (retail domain)
  • Import employee list (500 headcount)
  • Create onboarding course (Store Procedures)
  • Enable gamification (points for store, badges for achievement)
  • Estimated hours: 25 (dev) + 10 (BD)

Week 2 (Integration):
  • Connect to HR system (Gupy or Kenoby if available)
  • Upload store locations (for location-based matching)
  • Setup internal job board (50 open positions across stores)
  • Estimated hours: 25 (dev) + 5 (BD)

Week 3 (Pilot):
  • Launch with 50 employees (2 stores)
  • Collect onboarding feedback
  • Measure: training completion time, quiz pass rate, engagement
  • Estimated hours: 10 (support)

Week 4 (Expand):
  • Expand to all 30 stores
  • Monthly business review (KPIs)
  • Contract signed
  • Estimated hours: 5 (BD)

Contract Terms:
  - Implementation: $10-15k
  - Software: $3-5k/month (headcount-based)
  - Commitment: 12 months
  - Success metric: 20% reduction in onboarding time
```

#### Tipo C: Startup LATAM (SMB Pilot)

```
Customer: DEF Startup (150 employees, series B)

Week 1 (Setup):
  • Setup tenant (fast, 4 hours)
  • Import users from G Suite (automático)
  • Create 1 sample course
  • Enable LMS + recruitment (both modules)
  • Estimated hours: 15 (dev) + 5 (BD)

Week 2 (Integration):
  • No HRIS (too small)
  • Setup recruitment (job board, candidate matching)
  • Estimated hours: 10 (dev)

Week 3 (Pilot):
  • Use for hiring (1-2 open positions)
  • Collect feedback on matching quality
  • Estimated hours: 5 (support)

Week 4 (Close):
  • Quick contract ($20-30k ACV)
  • Estimated hours: 3 (BD)

Contract Terms:
  - No implementation fees
  - Software: $1.5-2.5k/month
  - Commitment: 6-12 months
  - Startup-friendly (flexible)
```

---

### Results Target (Semanas 1-12)

| Metric | Target |
|--------|--------|
| **Customers Signed** | 1-2 |
| **Implementation Revenue** | $15-25k |
| **Monthly Recurring Revenue** | $4-8k |
| **Annual Recurring Revenue** | $48-96k |
| **NPS** | 30+ |
| **Retention** | 85%+ |
| **Churn** | <5% (monthly) |

---

## Fase 2: Meses 4-8 — Scale Traction

### Objetivo: 5-10 customers, $40-60k MRR

**Parallel Workstreams:**

### Workstream A: Sales & Marketing

**Hiring:**
- [ ] Hire 1 Chief Revenue Officer (or Sales Director)
  - Profile: 10+ years enterprise sales, recruitment market experience
  - Responsibility: Sales org, revenue targets, partnerships
  - Timeline: Month 4
  - Budget: $120-150k/year

- [ ] Hire 2 Account Executives
  - Profile: 5+ years SaaS enterprise sales
  - Territory: LATAM + EMEA (split)
  - Timeline: Month 5-6
  - Budget: $60-80k each + commission

- [ ] Hire 1 Customer Success Manager
  - Profile: 3+ years SaaS customer success
  - Responsibility: Onboarding, retention, upsell
  - Timeline: Month 6
  - Budget: $50-60k/year

**GTM Activities:**
- [ ] Content marketing (blog + SEO)
  - 2 posts/month: "LGPD compliance," "employee retention," "onboarding workflows"
  - Target: Rank in Google for "recruitment software Brasil"
  - Effort: 30 hours/month (external contractor or internal)

- [ ] Partner development
  - 5 strategic partnerships (HR consultants, system integrators)
  - Referral agreements (20% commission on ACV)
  - Co-marketing (webinars, case studies)
  - Effort: 40 hours/month (BD lead)

- [ ] Paid advertising
  - LinkedIn ads: $2-3k/month (target HR buyers)
  - Google Ads: $2-3k/month (brand + keywords)
  - Goal: 100+ MQLs/month
  - Effort: 20 hours/month (marketing)

- [ ] Customer references
  - 3-5 case studies (customer + MatchCo co-created)
  - Video testimonials (5 mins each)
  - Reference calls (sales enablement)
  - Effort: 40 hours/month

**Expected Output:**
- 100+ marketing qualified leads (MQLs)
- 20+ sales qualified leads (SQLs)
- 5-10 new customer logos
- $40-60k MRR

---

### Workstream B: Product Development

**Sprint Goals:**

**Sprint 1 (Weeks 1-2): HRIS Integrations**
- [ ] Implement Kenoby adapter (LATAM popular)
  - Test with 2+ customers
  - Effort: 30 hours (dev) + 10 hours (testing)

- [ ] Implement Workday adapter (enterprise requirement)
  - Scoped to core fields (names, job titles, departments)
  - Effort: 40 hours (dev) + 10 hours (testing)

- [ ] Setup marketplace (admin UI to browse adapters)
  - Simple list + enable/disable toggles
  - Documentation link to each
  - Effort: 15 hours

**Sprint 2 (Weeks 3-4): Advanced Reporting**
- [ ] Analytics dashboard (recruitment funnel)
  - Positions created → Applications → Matched → Hired
  - Drill-down by department, location, job function
  - Effort: 40 hours (dev) + 10 hours (design)

- [ ] Analytics dashboard (learning metrics)
  - Courses created → Enrollments → Completions → Certificates
  - Quiz pass rates, time to completion, engagement
  - Effort: 30 hours

- [ ] Export functionality (CSV/PDF)
  - Reports → Download button
  - Compliance: LGPD data export
  - Effort: 20 hours

**Sprint 3 (Weeks 5-6): Security & Compliance**
- [ ] SSO (SAML 2.0)
  - Support Okta, Azure AD, Google Workspace
  - Effort: 50 hours (dev) + 20 hours (testing)

- [ ] Advanced permissions
  - Role-based access control (RBAC)
  - Department-based visibility
  - Effort: 30 hours

- [ ] Audit logging (LGPD)
  - All admin actions logged
  - User access reports
  - Effort: 25 hours

**Sprint 4 (Weeks 7-8): Mobile & PWA**
- [ ] PWA offline mode improvements
  - Offline candidate applications
  - Sync when online
  - Effort: 40 hours

- [ ] Mobile app (Cordova wrapper)
  - Wrap PWA in native app shell
  - App store submission (iOS + Android)
  - Effort: 60 hours

**Total Dev Effort (Months 4-8):** ~400 hours (2 full-time devs)

---

### Workstream C: Operations & Finance

**Setup:**
- [ ] Hire Finance/Operations lead (part-time consultant, month 4)
  - Accounting, billing, HR admin
  - $5-10k/month

- [ ] Implement billing system
  - Stripe integration
  - Recurring invoices (monthly)
  - Usage-based pricing (if needed)
  - Effort: 20 hours

- [ ] Customer data security
  - Backup + disaster recovery plan
  - Incident response playbook
  - Effort: 20 hours

- [ ] Legal & Compliance
  - Customer data processing agreement (DPA)
  - LGPD compliance statement (customer-facing)
  - Terms of service + privacy policy review
  - Effort: 40 hours (external lawyer)

---

### Results Target (Months 4-8)

| Metric | Target |
|--------|--------|
| **Customer Count** | 5-10 |
| **MRR** | $40-60k |
| **ARR** | $480-720k |
| **Churn Rate** | <5% |
| **NPS** | 40+ |
| **Marketing MQLs** | 100+ |
| **Sales-Qualified Leads (SQLs)** | 20+ |
| **Win Rate** | 30-40% |
| **Sales Cycle (avg)** | 8-12 weeks |

---

## Fase 3: Meses 8-12 — Validate Scale

### Objetivo: 10-15 customers, $60-100k MRR, Year 1 close strong

**Parallel Workstreams:**

### Workstream A: Sales Acceleration

**Team:** CRO + 2 AEs + 1 CSM + 1 Marketing lead

**Activities:**
- [ ] Expand AE team (add 1 more AE for North America)
- [ ] Build sales playbooks (pitch deck, demo, contract templates)
- [ ] Attend 2-3 conferences (HR Tech, recruitment events)
- [ ] Build partner channel (10+ certified partners)
- [ ] Launch "MatchCo for [Vertical]" editions

**Expected:** 5-10 new customer logos, $60-100k MRR

---

### Workstream B: Product Polish

**Sprints:**
1. **Mobile App Launch**
   - iOS + Android apps in app stores
   - Push notifications
   - Offline-first candidate applications

2. **Hybrid ML Matching**
   - Begin collecting matching data (outcomes)
   - Design ML pipeline (python + TensorFlow)
   - Soft-launch with 2-3 customers

3. **Vertical Editions**
   - "MatchCo for Education" (pre-built templates, workflows)
   - "MatchCo for Retail" (onboarding + gamification focus)
   - "MatchCo for Government" (compliance focus)

4. **Partner Ecosystem**
   - Partner SDK (write docs for building on MatchCo APIs)
   - App marketplace (launch in admin console)
   - Partner program (certification, revenue share)

---

### Workstream C: Year 1 Recap & Planning

**Activities:**
- [ ] Year 1 board review (investors, if any)
  - Metrics: customer count, ARR, churn, NPS, burn rate
  - Wins & learnings
  - Year 2 roadmap

- [ ] Prepare Series A conversation (if raising)
  - Deck: 20 slides (market, traction, team, ask)
  - Metrics: revenue, growth rate, unit economics
  - Use of funds: 70% sales, 20% product, 10% operations

- [ ] Team expansion planning
  - Engineering: hire 2-3 more devs
  - Sales: hire 2-3 more AEs
  - Operations: hire CFO (part-time → full-time)

---

### Results Target (Months 8-12)

| Metric | Year 1 Target |
|--------|--------|
| **Customer Count** | 10-15 |
| **ARR** | $600-900k |
| **MRR** | $50-75k |
| **Churn Rate** | <5% |
| **NPS** | 45+ |
| **Retention** | 90%+ |
| **Employee Count** | 12-15 |
| **Burn Rate** | $50-80k/month |
| **Runway** | 12+ months (if bootstrapped) or fresh funding |

---

## Detailed Action Items by Role

### Chief Product Officer (PM Lead)

**Months 1-4:**
- [ ] Month 1: Create product requirements document (PRD) for setup wizard
- [ ] Month 2: Conduct 15+ customer discovery calls
- [ ] Month 3: Prioritize features based on customer feedback
- [ ] Month 4: Ship setup wizard + admin dashboard

**Months 4-8:**
- [ ] Month 5: Lead HRIS integration sprint (Kenoby + Workday)
- [ ] Month 6: Ship advanced analytics + reporting
- [ ] Month 7: Lead SSO + RBAC feature sprint
- [ ] Month 8: Plan vertical editions (Education, Retail, Government)

**Months 8-12:**
- [ ] Month 9: Launch mobile app (Cordova)
- [ ] Month 10: Begin ML matching pilot design
- [ ] Month 11: Ship 1st vertical edition (Education)
- [ ] Month 12: Plan Year 2 roadmap (Series A pitch deck)

---

### Chief Revenue Officer (CRO) / Sales Lead

**Months 1-4:**
- [ ] Month 1: Build target account list (30 companies)
- [ ] Month 2: Launch outbound campaign (cold email + LinkedIn)
- [ ] Month 3: Close 1st pilot customer
- [ ] Month 4: Hire first AE

**Months 4-8:**
- [ ] Month 5: Build sales playbook + pitch deck
- [ ] Month 6: Launch partner program (5 initial partners)
- [ ] Month 7: Hire 2nd AE (EMEA territory)
- [ ] Month 8: Hit $40-60k MRR target

**Months 8-12:**
- [ ] Month 9: Attend HR Tech conference (networking + lead gen)
- [ ] Month 10: Hire 3rd AE (North America pilot)
- [ ] Month 11: Build case studies (3-5 logos)
- [ ] Month 12: Prep for Series A (customer reference calls)

---

### Head of Customer Success

**Months 1-4:**
- [ ] Month 2-3: Support 1st-2nd customer pilots
- [ ] Month 3: Create customer success playbook
- [ ] Month 4: Establish NPS + retention tracking

**Months 4-8:**
- [ ] Month 5-8: Support 8+ customer implementations
- [ ] Month 6: Create onboarding video series
- [ ] Month 7: Establish customer advisory board (2-3 customers)
- [ ] Month 8: Document success metrics per customer

**Months 8-12:**
- [ ] Month 9: Launch customer community (Slack)
- [ ] Month 10: Create 3-5 case studies (customer co-authored)
- [ ] Month 11: Plan customer user conference (Year 2)
- [ ] Month 12: Build retention playbook (minimize churn)

---

### Head of Engineering

**Months 1-4:**
- [ ] Month 1: Stabilize codebase (bug fixes, tech debt)
- [ ] Month 2: Implement setup wizard (40h)
- [ ] Month 3: Ship admin dashboard (30h)
- [ ] Month 4: Support customer pilots (troubleshooting)

**Months 4-8:**
- [ ] Month 5: Lead HRIS integration sprint (70h)
- [ ] Month 6: Lead reporting/analytics sprint (70h)
- [ ] Month 7: Lead SSO/RBAC sprint (80h)
- [ ] Month 8: Begin mobile app (Cordova) spike (20h)

**Months 8-12:**
- [ ] Month 9: Ship mobile app (Cordova + app stores) (80h)
- [ ] Month 10: Design ML matching architecture
- [ ] Month 11: Begin ML matching implementation (in parallel with sprint work)
- [ ] Month 12: Stabilize infrastructure (multi-region, disaster recovery)

**Hiring Plan:**
- Month 4: +1 mid-level backend dev
- Month 6: +1 mid-level frontend dev
- Month 10: +1 DevOps/SRE

---

### Head of Marketing

**Months 1-4:**
- [ ] Month 1: Set up blog (WordPress or static site)
- [ ] Month 2: Publish 2 posts (LGPD, onboarding)
- [ ] Month 3: Setup analytics (Google Analytics, PostHog)
- [ ] Month 4: Create social media presence (LinkedIn, Twitter)

**Months 4-8:**
- [ ] Month 5: Launch LinkedIn ads campaign ($2-3k/month)
- [ ] Month 6: Launch Google Ads campaign ($2-3k/month)
- [ ] Month 7: Create case study #1 (1st customer)
- [ ] Month 8: Prepare partner marketing materials

**Months 8-12:**
- [ ] Month 9: Attend HR Tech conference (booth + speaking slot)
- [ ] Month 10: Create vertical-specific marketing campaigns
- [ ] Month 11: Launch webinar series (1x/month)
- [ ] Month 12: Prepare Series A pitch materials

---

## Budget & Burn Rate

### Monthly Operating Budget

**Months 1-4 (MVP Stage):**
```
Salaries (3 people):              $30k
  - 1 CEO/Founder
  - 1 CTO/Dev lead
  - 1 PM/Product lead (part-time)

Infrastructure:
  - AWS (compute, RDS, Redis):     $3k
  - S3/file storage:               $1k
  - PostHog analytics:             $0.5k
  - Monitoring (DataDog):          $0.5k

Contractor/Consulting:
  - Sales/BD contractor:           $3k
  - Legal (compliance):            $1k
  - Marketing:                     $1k

Marketing/Ads:                      $1k
Tools (Airtable, Slack, etc):     $1k

TOTAL MONTHLY BURN:               $42.5k
```

**Months 4-8 (Scale Stage):**
```
Salaries (8 people):              $80k
  - 1 CRO
  - 2 Account Executives
  - 1 CSM
  - 1 Marketing lead
  - 3 Engineers

Infrastructure:                    $5k
Contractors/Consulting:            $3k
Marketing/Ads:                     $5k
Tools & SaaS:                      $2k

TOTAL MONTHLY BURN:               $95k
```

**Months 8-12 (Optimization Stage):**
```
Salaries (12-15 people):          $120k
  - C-suite (CEO, CRO, CTO)
  - 3 Sales (AE + SDR)
  - 2 CSM
  - 1 Marketer
  - 4 Engineers

Infrastructure:                    $7k
Contractors/Consulting:            $5k
Marketing/Ads:                     $8k
Tools & SaaS:                      $3k

TOTAL MONTHLY BURN:               $143k
```

### Funding Requirements

**Scenario 1: Bootstrapped**
```
Year 1 Burn:         $800k (avg)
Customer Revenue:    $300-500k (ramp)
Self-funding Gap:    $300-500k

Feasible if:
- Founder has savings ($300k+)
- Hits revenue targets early
- Delays hiring
```

**Scenario 2: Seed Funding**
```
Raise:               $500k-$1M (seed round)
Burn:                $800k Year 1
Revenue:             $300-500k
Runway:              12+ months

Use of funds:
  - 60% Salaries (CRO + AEs)
  - 20% Product development
  - 10% Infrastructure
  - 10% Marketing
```

**Scenario 3: Pre-Series A**
```
Raise:               $2-3M (Series A)
Runway:              24+ months
Hire:                15-20 people
Target:              $2M+ ARR by end Year 2
```

---

## Success Metrics Dashboard (Quarterly Reviews)

### Product Metrics

| Metric | Q1 | Q2 | Q3 | Q4 |
|--------|-----|-----|------|-------|
| Active Customers | 1-2 | 5-7 | 8-12 | 10-15 |
| Feature Adoption | 60% | 70% | 75% | 80% |
| NPS Score | 30+ | 35+ | 40+ | 45+ |
| Uptime | 98% | 99% | 99.5% | 99.5% |

### Revenue Metrics

| Metric | Q1 | Q2 | Q3 | Q4 |
|--------|-----|-----|------|-------|
| MRR | $4-8k | $20-30k | $40-60k | $50-75k |
| ARR | $50-96k | $240-360k | $480-720k | $600-900k |
| ACV | $50k | $40-50k | $40-60k | $50-75k |
| Sales Cycle | 10-12w | 10-12w | 8-10w | 8-10w |
| Win Rate | 30% | 35% | 40% | 40%+ |

### Customer Metrics

| Metric | Q1 | Q2 | Q3 | Q4 |
|--------|-----|-----|------|-------|
| Customer Retention | 85% | 90% | 92% | 93% |
| Churn Rate | <10% | <8% | <5% | <5% |
| Logo Churn | 0% | 0% | 0% | <5% |
| Expansion Revenue | 0% | 5% | 10% | 15% |

### Team Metrics

| Metric | Q1 | Q2 | Q3 | Q4 |
|--------|-----|-----|------|-------|
| Headcount | 3 | 5 | 8 | 12-15 |
| Dev Team | 2 | 2 | 4 | 4-5 |
| Sales Team | 0 | 1 | 3 | 3-4 |
| CS Team | 0 | 0 | 1 | 2 |
| Burn Rate | $42k | $70k | $95k | $120-140k |

---

## Risk Mitigation

### Critical Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|---|---|---|
| **Cannot get 1st customer** | Medium | High | Offer free pilot; target vertical with pain; BD networking |
| **Product instability** | Medium | High | Hire DevOps/SRE month 4; infrastructure hardening |
| **Sales too slow** | High | High | Hire CRO month 3-4; partner channel; focus on verticals |
| **Competitor copies features** | Low-Med | Medium | Build moat: LGPD + bilateral; focus on LATAM |
| **Key person leaves** | Medium | High | Document processes; cross-train team; equity retention |
| **Runway runs out** | Medium-High | High | Start fundraising month 6; hit revenue targets; trim costs |
| **Feature scope creep** | High | Medium | Strict roadmap prioritization; say no to non-core features |
| **LGPD compliance fails** | Low | High | Third-party security audit Q2; legal review monthly |

---

## Success Stories Target

### By Month 12, MatchCo should have:

**3-5 Reference Customers:**
1. **University Case Study** (Education vertical)
   - "Reduced hiring time 30% with bilateral matching"
   - 50+ graduates hired per semester
   - ARR: $30-50k

2. **Retail Chain Case Study** (Hospitality vertical)
   - "Onboarding time cut 25% via learning trails"
   - Turnover reduction 15% (gamification engagement)
   - ARR: $50-80k

3. **Startup Case Study** (SMB vertical)
   - "All-in-one recruitment + learning for 150-person team"
   - Cost: 40% less than Workable + LMS separately
   - ARR: $20-30k

4. **Government/NGO Case Study** (Compliance vertical)
   - "LGPD-compliant recruitment (immutable audit trail)"
   - Passed regulatory audit
   - ARR: $30-50k

5. **Partner Case Study** (Integrator success)
   - "Built 3 integrations on MatchCo platform"
   - Revenue: $X from partner referrals
   - ARR: $10-20k

---

## Key Decisions & Milestones

### Decisions to Make

1. **Month 1:** Focus on 1 vertical first (education, retail, or SMB)?
   - Recommendation: **Education** (strong PMF) + **Retail** (high volume)

2. **Month 3:** Build or buy HRIS integrations?
   - Recommendation: **Build first 2** (Gupy, Kenoby); buy/partner after

3. **Month 5:** Raise funding or bootstrap?
   - Recommendation: **Raise if hitting revenue targets** ($20k+ MRR); bootstrap if conservative

4. **Month 8:** Which vertical edition to launch first?
   - Recommendation: **"MatchCo for Education"** (highest demand signal)

5. **Month 10:** Build proprietary ML or continue heuristic?
   - Recommendation: **Start research; pilot with 1-2 customers; soft-launch**

### Milestones

```
Month 1:   Setup wizard shipped
Month 2:   First pilot customer engaged
Month 3:   First customer signed (contract)
Month 4:   Hire CRO; 2nd customer signed
Month 5:   Partner program launched; 3rd-4th customers
Month 6:   Analytics dashboard shipped; $20k MRR target
Month 8:   5-10 customers; $40-60k MRR target
Month 10:  Mobile app in app stores
Month 12:  10-15 customers; $60-100k MRR; ready for Series A
```

---

## Communication Plan

### Weekly Sync
- **Internal:** Tuesday 10am (30 mins)
  - Product: shipped features, blockers
  - Sales: pipeline, opportunities, lost deals
  - CS: customer feedback, churn signals
  - Ops: financials, burn rate, hiring

### Monthly Board/Investor Update
- KPIs: customers, MRR, churn, burn, headcount
- Wins: customer logos, partnerships, product launches
- Challenges: sales velocity, product gaps, competition
- Plan: next month priorities

### Quarterly Strategic Review
- Year-to-date performance vs. plan
- Roadmap adjustments
- Team feedback (morale, retention risks)
- Investor/board discussion (if raising)

---

**Document Version:** 1.0  
**Last Updated:** 2026-10-07  
**For:** MatchCo Leadership Team
