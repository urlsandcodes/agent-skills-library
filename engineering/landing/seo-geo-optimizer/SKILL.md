---
name: landing.seo-geo-optimizer
description: Systematically audits and optimizes web landing pages for Technical SEO, Generative Engine Optimization (GEO), and Answer Engine Optimization (AEO).
version: 1.0.0
type: intelligence
status: internal
---

# Landing Page SEO & GEO/AEO Optimizer

## 1. Role and Core Purpose
The **Landing Page SEO & GEO/AEO Optimizer** (`landing.seo-geo-optimizer`) operates as an elite technical search strategist, growth engineer, and AI search visibility auditor.

Its purpose is to:
- Evaluate landing pages against the **4 Core Optimization Pillars**:
  1. **Technical SEO**: Metadata, canonicals, OpenGraph, Twitter cards, semantic hierarchy.
  2. **Generative Engine Optimization (GEO)**: Princeton KDD '24 benchmark techniques (quantitative evidence/statistics, expert citations, technical vocabulary density, anti-keyword-stuffing).
  3. **Answer Engine Optimization (AEO)**: Direct-answer framing (BLUF: 40–60 words), question-framed H2/H3 headers, skimmable chunking.
  4. **Structured Data & AI Context**: Schema.org JSON-LD (`SoftwareApplication`, `Organization`, `FAQPage`) and `llms.txt`.
- Perform deterministic scoring (0–100) before and after changes.
- Apply guaranteed optimizations directly to landing page source code.

---

## 2. When to Activate This Skill
Agents should trigger this skill whenever:
- The user requests: `/audit-landing-page`, `/optimize-landing-page`, `/verify-seo-geo`, or asks to "improve landing page SEO", "optimize for AI search engines", "add GEO/AEO", or "make our landing page rank in Perplexity / SearchGPT / Google AI Overviews".
- Building or modifying a web landing page or homepage in a web project (Next.js, React, HTML, Astro, etc.).

---

## 3. Command Specifications

### 3.1 `/audit-landing-page [path-to-page]`

Audits a landing page and calculates a deterministic 0–100 score across all 4 pillars.

#### Plan & File Auto-Discovery Protocol
If no explicit path is passed, search the project in order:
1. `app/page.jsx` or `app/page.tsx` (Next.js App Router)
2. `pages/index.jsx` or `pages/index.tsx` (Next.js Pages Router)
3. `index.html` or `src/index.html`
4. Associated layout file: `app/layout.jsx` or `app/layout.tsx`

#### 4-Pillar Evaluation Criteria:
1. **Technical SEO (0–25 points)**:
   - Page title (50–60 characters) (+5)
   - Meta description (140–160 characters) (+5)
   - OpenGraph tags (`og:title`, `og:description`, `og:image`, `og:url`) (+5)
   - Twitter card metadata (`summary_large_image`) (+5)
   - Canonical URL, viewport, and robots directives (+5)
2. **GEO: Generative Engine Optimization (0–25 points)**:
   - Statistics & numerical data points present (e.g. percentages, quantifiable benchmarks) (+8)
   - Authoritative domain terminology & semantic triples (+7)
   - Verified factual claims without keyword stuffing (+5)
   - Credible citations or social proof attributions (+5)
3. **AEO: Answer Engine Optimization (0–25 points)**:
   - BLUF (Bottom Line Up Front): Immediate 40–60 word answer to main search intent (+10)
   - Natural language conversational question headings (`How does X work?`, `What is Y?`) (+8)
   - Information chunking: Bullet lists, feature comparison tables (+7)
4. **Structured Data & AI Context (0–25 points)**:
   - Schema.org JSON-LD for `SoftwareApplication` / `Product` (+8)
   - Schema.org JSON-LD for `FAQPage` (+8)
   - Schema.org JSON-LD for `Organization` (+4)
   - Presence of `public/llms.txt` (+5)

---

### 3.2 `/optimize-landing-page [path-to-page]`

Directly enhances the landing page with guaranteed optimizations:
1. Injects complete OpenGraph, Twitter, and canonical metadata in the root layout/head.
2. Embeds Schema.org JSON-LD script blocks (`SoftwareApplication`, `Organization`, `FAQPage`).
3. Refines value proposition copy using Princeton GEO statistics (injecting quantifiable proof).
4. Formats FAQs with conversational H3 question tags and direct BLUF answers.
5. Generates `public/llms.txt` and `public/llms-full.txt`.

---

### 3.3 `/verify-seo-geo [path-to-page]`

Re-runs the audit engine, verifies the score lift, and outputs a complete before-and-after audit report saved to `.agents/seo-geo-audit-report.md`.
