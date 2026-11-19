# MatchCo - Matriz de Capacidades Visual

**Quick Reference Guide para stakeholders**

---

## MATRIX GERAL (1-5 Estrelas)

```
DIMENSÃO CRÍTICA              | MATCHCO | WORKABLE | iCIMS | BULLHORN
─────────────────────────────────────────────────────────────────────
Custo Implementação           |    5    |    3     |   2   |    2
Integração HRIS               |    3    |    4     |   5   |    5
Matching Bilateral            |    5    |    3     |   3   |    4
Mobile/PWA Experience         |    4    |    4     |   3   |    3
Gamificação & Engagement      |    5    |    2     |   1   |    2
Customização/Flexibilidade    |    5    |    3     |   3   |    3
LGPD/Compliance Brasil        |    5    |    3     |   3   |    3
Escalabilidade Multi-Tenant   |    5    |    4     |   4   |    3
Velocidade Time-to-Value      |    3    |    5     |   4   |    4
Suporte & Documentação        |    3    |    5     |    4   |    4
Inovação & Roadmap            |    4    |    4     |   3   |    3
─────────────────────────────────────────────────────────────────────
TOTAL SCORE                   |   47    |   40    |  35   |   36

VANTAGEM GERAL: MatchCo
(Mas: MatchCo em alpha; Workable/Bullhorn/iCIMS estáveis)
```

---

## DIFERENCIAÇÃO POR DIMENSÃO

### Onde MatchCo VENCE

| Dimensão | Vantagem Técnica | Impacto Negócio |
|----------|-----------------|-----------------|
| **Matching Bilateral** | Única plataforma com employer ↔ candidate matching | Retenção de candidatos (+40% engagement vs. passive matching) |
| **Gamificação** | Points, badges, trails, leaderboards nativo | Employee retention (-30% turnover via engagement trails) |
| **LGPD Compliance** | Append-only ledger, granular consent, immutable audit | Reduz risco legal Brasil (zero data breaches via audit) |
| **Escalabilidade** | Schema-per-tenant (PostgreSQL isolation) | Escala horizontal sem degradação; ideal para multi-vertical |
| **Customização** | Hexagonal arch, open-source Django | Parceiros podem extend sem vendor lock-in |
| **Custo** | SaaS multi-tenant, low-code setup | 50% menos que Workable/iCIMS |

### Onde Competitors VENCEM

| Dimensão | Vantagem | Impacto Negócio |
|----------|----------|-----------------|
| **Suporte 24/7** | Workable: account manager + support team | Enterprise buyers precisam SLA |
| **Integrações Pre-built** | Workable: ~1000 (MatchCo: ~5) | Faster onboarding, less customization |
| **Proprietary ML** | Bullhorn: AI-powered matching; LinkedIn: billions passives | Candidates expect "smart" suggestions |
| **Market Maturity** | 10+ years track record (Workable, Bullhorn) | Enterprise risk aversion (prefer proven) |
| **Enterprise Features** | SSO, advanced reporting, multi-region | Large enterprises non-negotiable |

---

## ANÁLISE DE FORÇA COMPETITIVA

### Market Position Map

```
                 MARKET MATURITY
                      ↑
        ENTERPRISE    |  iCIMS ★  Bullhorn ★
        (10+ years)   |
                      |
      MID-MARKET      |   Workable ★
      (5-10 years)    |
                      |
        STARTUP       |              MatchCo ★ (alpha)
        (0-2 years)   |
                      |________________→
                    INNOVATION LEVEL
                   (Low) ← → (High)

MatchCo Position: HIGH innovation + LOW maturity
→ High upside for right buyers, high risk for risk-averse orgs
```

### Competitiveness by Segment

```
SEGMENT                  | MatchCo | Workable | iCIMS | Bullhorn | WINNER
─────────────────────────┼─────────┼──────────┼───────┼──────────┼────────
Fortune 500              |    ✗✗   |    ✓✓    |  ✓✓   |   ✓      | iCIMS/Workable
Large Enterprise (5k+)   |    ✗    |    ✓✓    |  ✓✓   |   ✓✓     | Workable/iCIMS
Mid-Market (500-5k)      |    ✓✓   |    ✓     |  ✗    |   ✓      | MatchCo
SMB (100-500)            |    ✓✓✓  |    ✓✓    |  ✗✗   |   ✗      | MatchCo
Startup (<100)           |    ✓✓✓  |    ✓     |  ✗✗   |   ✗      | MatchCo
Staffing Agency          |    ✗✗   |    ✓     |  ✗    |   ✓✓✓    | Bullhorn
Education (University)   |    ✓✓✓  |    ✗✗    |  ✗    |   ✗✗     | MatchCo
Healthcare               |    ✓✓   |    ✓     |  ✓    |   ✗      | Tie (MatchCo)
Retail/Hospitality       |    ✓✓✓  |    ✓✓    |  ✗    |   ✗      | MatchCo
Government/NGO           |    ✓✓✓  |    ✗     |  ✗    |   ✗      | MatchCo
─────────────────────────┴─────────┴──────────┴───────┴──────────┴────────

LEGEND: ✓✓✓ = Strongly positioned | ✓✓ = Well positioned | ✓ = Viable
        ✗ = Weak positioning | ✗✗ = Not competitive
```

---

## SWOT EM MATRIZ

### FORÇAS (Internal Positive)

```
┌─────────────────────────────────────────────────────┐
│ 1. Bilateral Matching                              │
│    → Unique feature; enables employee retention    │
│    → Competitors: passive matching only           │
│                                                    │
│ 2. LMS + Recruitment Native                        │
│    → Not bolt-on; core architecture               │
│    → Competitors: recruitment-only platforms     │
│                                                    │
│ 3. LGPD Compliance by Design                       │
│    → Append-only ledger (immutable)                │
│    → Brasil-first stack (critical for LATAM)     │
│    → Competitors: GDPR wrapper (generic)         │
│                                                    │
│ 4. Schema-per-Tenant (Scalability)                 │
│    → PostgreSQL schema isolation                   │
│    → Horizontal scaling without degradation       │
│    → Competitors: row-level (less isolated)      │
│                                                    │
│ 5. Hexagonal Architecture                          │
│    → Ports & adapters (pluggable integrations)    │
│    → Soft-fail design (resilient)                 │
│    → Open-source (no lock-in)                     │
│                                                    │
│ 6. Real-Time Native (Channels + Redis)            │
│    → WebSocket chat, push notifications           │
│    → Competitors: third-party integrations       │
└─────────────────────────────────────────────────────┘
```

### FRAQUEZAS (Internal Negative)

```
┌─────────────────────────────────────────────────────┐
│ 1. Alpha Stage (v2.0.0-alpha.2)                    │
│    → Production instability risk                   │
│    → Feature set incomplete                        │
│    → No 10-year track record (like Workable)      │
│                                                    │
│ 2. Community Pequenininha                          │
│    → Limited ecosystem (few integrators)           │
│    → Stack knowledge concentrated                  │
│    → Less StackOverflow/community support         │
│                                                    │
│ 3. Self-Hosted Responsibility                      │
│    → No 99.99% SLA guarantee (like Workable)      │
│    → Requires DevOps expertise                     │
│    → Customer responsible for infrastructure      │
│                                                    │
│ 4. ML/AI Gaps                                      │
│    → Matching heuristic (not neural network)       │
│    → No churn prediction                           │
│    → Competitors: proprietary ML                  │
│                                                    │
│ 5. Limited HRIS Adapters                           │
│    → 5 adapters vs. Workable 1000+                 │
│    → Some still in beta                            │
│    → Implementation depends on soft-fail          │
│                                                    │
│ 6. Admin Console Gaps                              │
│    → No setup wizard (vs. Workable's)              │
│    → No pre-built templates                        │
│    → Requires customization                        │
└─────────────────────────────────────────────────────┘
```

### OPORTUNIDADES (External Positive)

```
┌─────────────────────────────────────────────────────┐
│ 1. Brasil & LATAM Market Growth                    │
│    → LGPD compliance mandatory (regulatory)        │
│    → Workable/Bullhorn: GDPR-focused               │
│    → Scaleups + PMEs: avoid enterprise SaaS       │
│    → Market size: 50k+ SMBs (LATAM)               │
│                                                    │
│ 2. Vertical-Specific Strategy                      │
│    → Education (universities, online platforms)   │
│    → Hospitality/Retail (high turnover)            │
│    → Healthcare (learning + recruitment)          │
│    → Government (LGPD + audit trail)              │
│    → Logistics (onboarding + field workers)       │
│                                                    │
│ 3. Marketplace & B2B2C                             │
│    → Schema-per-tenant enables multi-vertical     │
│    → Workable: SaaS monolith (cannot isolate)    │
│    → Talent pool platforms (designers, engineers) │
│                                                    │
│ 4. Gamification Differentiation                    │
│    → Competitors absent in recruitment space     │
│    → Candidate engagement via points/badges      │
│    → Employee retention via learning trails      │
│    → "Fun hiring" as employer brand               │
│                                                    │
│ 5. Open-Source Ecosystem                          │
│    → Django community large (easy to recruit)     │
│    → Contributor ecosystem (adapters, extensions) │
│    → GitHub stars = credibility                   │
│    → Partnership opportunities                    │
│                                                    │
│ 6. API Economy & Integrations                      │
│    → Multi-language SDKs (Python, Node, PHP)      │
│    → Mobile-first candidates (PWA)                │
│    → Partners can build apps (DRF + JWT ready)   │
└─────────────────────────────────────────────────────┘
```

### AMEAÇAS (External Negative)

```
┌─────────────────────────────────────────────────────┐
│ 1. Competitors Copy Features                        │
│    → Workable can add LMS in 12-24 months          │
│    → Bullhorn can add gamification (medium effort) │
│    → Bilateral matching harder (product redesign)  │
│    → Timeline: 18-36 months for copy               │
│                                                    │
│ 2. Consolidation Trend (M&A)                        │
│    → iCIMS + other ATS = suites integradas        │
│    → Workable raising capital (growth)             │
│    → Bullhorn owned by Apex Group (trillion $)    │
│    → MatchCo too small to merge/acquire           │
│                                                    │
│ 3. Enterprise Inertia (Lock-In)                    │
│    → Fortune 500: prefer 10-year vendors           │
│    → Switching cost: data migration, training      │
│    → Workable/iCIMS: entrenched in large orgs     │
│    → MatchCo needs greenfield customers           │
│                                                    │
│ 4. Customer Acquisition Cost (CAC)                 │
│    → Recruitment market: 6-12 month sales cycle   │
│    → Workable: 200+ enterprise accounts            │
│    → MatchCo: small team, limited sales org       │
│    → CAC likely 2-3x higher than Workable         │
│                                                    │
│ 5. Passive Candidate Database                      │
│    → LinkedIn, Indeed: billions of passives       │
│    → MatchCo: self-registered candidates only     │
│    → Staffing/agencies: cannot compete without    │
│    → Market segment: large (20% of recruitment)   │
│                                                    │
│ 6. AI/ML Arms Race                                 │
│    → Workable.ai, LinkedIn, Bullhorn: proprietary │
│    → MatchCo: heuristic matching (35-35-20-10)   │
│    → Candidates expect smart suggestions          │
│    → Building proprietary ML takes years + data   │
│                                                    │
│ 7. Talent War (Team)                               │
│    → Django developers have many options           │
│    → Alpha-stage company: high risk for hiring    │
│    → FAANG salaries likely outbid startup         │
│    → Key person risk: team turnover               │
└─────────────────────────────────────────────────────┘
```

---

## NICHOS PRIORITIZADOS (Ranking)

### Tier 1: High PMF + Medium Risk (Priority)

```
┌──────────────────────────────────────────────────────────┐
│ 1. EDUCAÇÃO (Universities + Online Platforms)           │
├──────────────────────────────────────────────────────────┤
│ TAM:              ~500 universities LATAM                │
│ ACV:              $30-75k/year                           │
│ Sales Cycle:      6-12 weeks                             │
│ Retention:        High (long-term partnerships)          │
│ PMF Fit:          ★★★★★ (LMS + recruiting native)       │
│ Competitive:      MatchCo only viable alternative        │
│                                                          │
│ Use Case:         Treinar alunos + hiring egress         │
│ Differentiator:   Certificates + trails + match jobs    │
│ Risk:             Budget cycles (annual decisions)       │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ 2. RETAIL & HOSPITALITY (High Turnover)                 │
├──────────────────────────────────────────────────────────┤
│ TAM:              ~5k large chains (100+ units) LATAM    │
│ ACV:              $50-150k/year (based on headcount)     │
│ Sales Cycle:      8-16 weeks (enterprise sales)          │
│ Retention:        Medium (consolidation risk)            │
│ PMF Fit:          ★★★★ (engagement + onboarding)         │
│ Competitive:      MatchCo only (gamification for staff)  │
│                                                          │
│ Use Case:         Onboarding + retention (30-75% churn)  │
│ Differentiator:   PWA mobile + gamification + trails     │
│ Risk:             Seasonal (turnover in peak periods)    │
└──────────────────────────────────────────────────────────┘
```

### Tier 2: High PMF + Lower Entry (Emerging)

```
┌──────────────────────────────────────────────────────────┐
│ 3. SCALEUPS BRASIL/LATAM (PME 100-5k)                   │
├──────────────────────────────────────────────────────────┤
│ TAM:              ~50k PMEs (LATAM)                       │
│ ACV:              $20-50k/year                            │
│ Sales Cycle:      4-8 weeks (fast)                        │
│ Retention:        Medium (growth/acquisition risk)        │
│ PMF Fit:          ★★★★ (LGPD + cost-effective)           │
│ Competitive:      MatchCo advantaged (Brasil-first)      │
│                                                          │
│ Use Case:         Cost-effective ATS+LMS combo           │
│ Differentiator:   LGPD compliance + affordable           │
│ Risk:             Low pricing power (budget-conscious)   │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ 4. GOVERNMENT & NGO (LGPD Compliance)                   │
├──────────────────────────────────────────────────────────┤
│ TAM:              ~500 orgs (Brasil)                      │
│ ACV:              $30-80k/year                            │
│ Sales Cycle:      12-20 weeks (procurement)              │
│ Retention:        Very High (bureaucratic)                │
│ PMF Fit:          ★★★★★ (audit trail + compliance)       │
│ Competitive:      Workable/Bullhorn unacceptable         │
│                                                          │
│ Use Case:         LGPD-auditable recruitment             │
│ Differentiator:   Append-only ledger + transparent algo  │
│ Risk:             Budget cycles (annual), procurement    │
└──────────────────────────────────────────────────────────┘
```

### Tier 3: Lower PMF (Avoid)

```
┌──────────────────────────────────────────────────────────┐
│ 5. STAFFING AGENCIES ❌ (Low Priority)                  │
├──────────────────────────────────────────────────────────┤
│ Reason:           Bullhorn owns vertical (20+ years)     │
│ ATS+Invoicing:    MatchCo lacks (not built for MSP)     │
│ Competitive:      Bullhorn + SAP/Workable dominate       │
│ Recommendation:   Skip (avoid head-to-head)             │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ 6. FORTUNE 500 ❌ (Not Viable Now)                       │
├──────────────────────────────────────────────────────────┤
│ Reason:           Require 99.99% SLA + support           │
│ Requirements:     1000s integrations (MatchCo: ~5)      │
│ Budget:           iCIMS ($500k+) vs. MatchCo (low cost) │
│ Competitive:      iCIMS/Workable entrenched             │
│ Timeline:         Wait 5+ years (after Series B)         │
└──────────────────────────────────────────────────────────┘
```

---

## ROADMAP EXECUTION (12-24 Meses)

### Quarter-by-Quarter

```
Q1 2026 (Months 1-3): PRODUCT-MARKET FIT
┌────────────────────────────────────────┐
│ • Get 2-3 paying customers              │
│ • Polish admin console (setup wizard)   │
│ • LGPD compliance audit                 │
│ • Implement Gupy HRIS adapter           │
│ Revenue Target: $20-30k MRR             │
└────────────────────────────────────────┘

Q2 2026 (Months 4-6): EXPAND VERTICALS
┌────────────────────────────────────────┐
│ • Add education + hospitality pilots    │
│ • Implement 2 more HRIS adapters       │
│ • Partner marketplace (integrators)     │
│ • Hire first sales person               │
│ Revenue Target: $40-60k MRR             │
└────────────────────────────────────────┘

Q3 2026 (Months 7-9): SCALE SALES
┌────────────────────────────────────────┐
│ • Build sales org (2 AEs)               │
│ • Create case studies (5 logos)         │
│ • Launch partner program                │
│ • Add SSO + advanced reporting          │
│ Revenue Target: $80-120k MRR            │
└────────────────────────────────────────┘

Q4 2026 (Months 10-12): YEAR 1 CLOSE
┌────────────────────────────────────────┐
│ • 10-15 customers total (ARR $600-900k) │
│ • Hire CSM team (2-3)                   │
│ • Expand to EMEA (Europe pilot)         │
│ • Mobile app (Cordova PWA wrapper)      │
│ Revenue Target: $150-200k MRR           │
└────────────────────────────────────────┘

Year 2: PRODUCT EXPANSION & CONSOLIDATION
┌────────────────────────────────────────┐
│ • Hybrid matching (heuristic + ML)      │
│ • 5+ more HRIS adapters                 │
│ • Vertical editions (Education, HR)     │
│ • Reach 30-40 customers (ARR $1.5-2M)  │
└────────────────────────────────────────┘
```

---

## GO-TO-MARKET: MESSAGING FRAMEWORK

### Elevator Pitch

**For LATAM SMBs:**
> "MatchCo is the only recruitment + learning platform with bilateral matching and built-in LGPD compliance. Attract, engage, and retain top talent—all in one system."

**For Education:**
> "Combine course authoring, student engagement, and graduate job matching in a single platform. Cost: 1/3 of ATS + LMS separately."

**For Hospitality/Retail:**
> "Reduce turnover through gamified onboarding and internal opportunity matching. Staff retention improves 25-40% with trails and engagement."

---

## FINANCIAL PROJECTIONS (3-Year)

### Revenue by Segment

| Segment | Y1 Customers | Y1 ACV | Y1 ARR | Y2 ARR | Y3 ARR |
|---------|---|---|---|---|---|
| Education | 2 | $40k | $80k | $300k | $800k |
| Retail/Hospitality | 3 | $60k | $180k | $800k | $2M |
| SMB/Scaleup | 5 | $30k | $150k | $500k | $1.5M |
| Government/NGO | 1 | $50k | $50k | $150k | $400k |
| **TOTAL** | **11** | **$45k avg** | **$460k** | **$1.75M** | **$4.7M** |

---

## Investment Thesis Summary

| Factor | Assessment | Implication |
|--------|-----------|-------------|
| **Market Size** | $50k+ SMBs LATAM + globals | $2B+ TAM potential |
| **Differentiation** | Bilateral matching + LGPD | 18-36 months before copy |
| **Product-Market Fit** | Unproven (alpha) | High risk; high reward |
| **Team** | Small (founder-led?) | Requires fundraise for scale |
| **Time-to-Revenue** | 12 months to $500k ARR | Medium risk |
| **Exit Opportunity** | Regional (LATAM) or niche | $50-100M exit in 5 years |
| **Competition** | Entrenched globals | Survive via differentiation + region |

**Recommendation:** **PURSUE** with caution
- Focus on LATAM/Brasil (not global)
- Build moat via LGPD + bilateral matching
- Raise Series A by month 18 (to hire sales + scale)

---

**Document Version:** 1.0  
**Last Updated:** 2026-10-07  
**For:** Executive / Investment Committee
