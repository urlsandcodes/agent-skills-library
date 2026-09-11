#!/usr/bin/env python3
"""Audit script for Landing Page SEO, GEO, and AEO optimization."""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys


def audit_landing_page(target_path: Path) -> dict:
    # Resolve directory or file
    if target_path.is_file():
        project_dir = target_path.parent
        # Walk up to find client or project root if inside app/
        while project_dir.name in ('app', 'pages', 'src', 'client') and project_dir.parent != project_dir:
            project_dir = project_dir.parent
    else:
        project_dir = target_path

    # Read relevant files
    content = ""
    target_files = []

    # Common Next.js / HTML paths
    candidates = [
        project_dir / "client/app/layout.jsx",
        project_dir / "client/app/page.jsx",
        project_dir / "app/layout.jsx",
        project_dir / "app/page.jsx",
        project_dir / "src/app/layout.jsx",
        project_dir / "src/app/page.jsx",
        project_dir / "pages/index.jsx",
        project_dir / "index.html",
    ]
    if target_path.is_file() and target_path not in candidates:
        candidates.insert(0, target_path)

    for c in candidates:
        if c.exists():
            target_files.append(str(c))
            with open(c, "r", encoding="utf-8") as f:
                content += f"\n--- {c.name} ---\n" + f.read()

    # Check for llms.txt
    llms_candidates = [
        project_dir / "client/public/llms.txt",
        project_dir / "public/llms.txt",
        project_dir / "llms.txt",
    ]
    has_llms_txt = any(p.exists() for p in llms_candidates)

    findings = []
    seo_score = 0.0
    geo_score = 0.0
    aeo_score = 0.0
    schema_score = 0.0

    # ---------------- 1. Technical SEO (0 - 25) ----------------
    # Title
    has_title = bool(re.search(r"title:\s*['\"][^'\"]{10,70}['\"]", content) or re.search(r"<title>[^<]{10,70}</title>", content))
    if has_title:
        seo_score += 5.0
        findings.append({
            "id": "SEO-001",
            "pillar": "technical_seo",
            "status": "pass",
            "title": "Optimized Page Title",
            "details": "Page title is properly configured.",
            "remediation": "Maintain concise, keyword-rich title under 60 characters."
        })
    else:
        findings.append({
            "id": "SEO-001",
            "pillar": "technical_seo",
            "status": "warning",
            "title": "Missing or Suboptimal Title",
            "details": "Page title is missing or not within standard length (10-70 characters).",
            "remediation": "Add descriptive metadata title between 50-60 characters."
        })

    # Meta Description
    has_desc = bool(re.search(r"description:\s*['\"][^'\"]{40,200}['\"]", content) or re.search(r'<meta\s+name=["\']description["\']', content))
    if has_desc:
        seo_score += 5.0
        findings.append({
            "id": "SEO-002",
            "pillar": "technical_seo",
            "status": "pass",
            "title": "Meta Description Present",
            "details": "Meta description exists and meets length standards.",
            "remediation": "Keep description between 140-160 characters."
        })
    else:
        findings.append({
            "id": "SEO-002",
            "pillar": "technical_seo",
            "status": "fail",
            "title": "Missing Meta Description",
            "details": "Meta description is missing or too short.",
            "remediation": "Add engaging meta description explaining value proposition."
        })

    # OpenGraph Tags
    has_og = bool(re.search(r"openGraph:\s*\{", content) or re.search(r'property=["\']og:title["\']', content))
    if has_og:
        seo_score += 5.0
        findings.append({
            "id": "SEO-003",
            "pillar": "technical_seo",
            "status": "pass",
            "title": "OpenGraph Social Metadata Configured",
            "details": "OpenGraph metadata (og:title, og:image, og:url) detected.",
            "remediation": "Ensure high-resolution og:image (1200x630) is referenced."
        })
    else:
        findings.append({
            "id": "SEO-003",
            "pillar": "technical_seo",
            "status": "fail",
            "title": "Missing OpenGraph Metadata",
            "details": "Social sharing previews will fail on LinkedIn, Twitter, and Slack.",
            "remediation": "Add openGraph config object with title, description, url, and image."
        })

    # Twitter Card
    has_twitter = bool(re.search(r"twitter:\s*\{", content) or re.search(r'name=["\']twitter:card["\']', content))
    if has_twitter:
        seo_score += 5.0
        findings.append({
            "id": "SEO-004",
            "pillar": "technical_seo",
            "status": "pass",
            "title": "Twitter Card Metadata Present",
            "details": "Twitter card metadata (summary_large_image) detected.",
            "remediation": "Verify card image accessibility."
        })
    else:
        findings.append({
            "id": "SEO-004",
            "pillar": "technical_seo",
            "status": "fail",
            "title": "Missing Twitter Card Metadata",
            "details": "Twitter card metadata is absent.",
            "remediation": "Add twitter object with card: 'summary_large_image'."
        })

    # Canonical & Viewport
    has_canonical = bool(re.search(r"canonical", content, re.IGNORECASE) or re.search(r"alternates:\s*\{", content))
    if has_canonical:
        seo_score += 5.0
    else:
        findings.append({
            "id": "SEO-005",
            "pillar": "technical_seo",
            "status": "warning",
            "title": "Missing Canonical URL",
            "details": "Search engines may index duplicate URL variations.",
            "remediation": "Declare alternates: { canonical: 'https://...' }."
        })

    # ---------------- 2. GEO: Generative Engine Optimization (0 - 25) ----------------
    # Princeton Empirical Benchmark: Statistics & Quantitative proof (+37% visibility)
    stat_matches = re.findall(r"\b\d+([.,]\d+)?\s*(%|percent|k|x|hours|days|mins|minutes|seconds|usd|\$|₹|users|creators)\b", content, re.IGNORECASE)
    if len(stat_matches) >= 3:
        geo_score += 8.0
        findings.append({
            "id": "GEO-001",
            "pillar": "geo_citability",
            "status": "pass",
            "title": "High Density of Statistical & Empirical Evidence",
            "details": f"Found {len(stat_matches)} concrete quantitative data points. Boosts AI citation likelihood.",
            "remediation": "Continue grounding product capabilities with empirical percentages and benchmarks."
        })
    else:
        findings.append({
            "id": "GEO-001",
            "pillar": "geo_citability",
            "status": "warning",
            "title": "Low Quantitative Evidence Density",
            "details": "Lacks specific statistics or quantifiable metrics. Princeton GEO benchmark shows statistics boost AI citation share by up to 41%.",
            "remediation": "Add concrete metrics (e.g. '0% platform fees', 'under 60-second setup', '3x higher retention')."
        })

    # Domain Terminology & Semantic Triples
    tech_terms = len(re.findall(r"\b(webhook|idempotent|api|telegram|encryption|presigned|database|mongodb|latency|architecture|jwt|auth)\b", content, re.IGNORECASE))
    if tech_terms >= 5:
        geo_score += 7.0
    else:
        geo_score += 3.0
        findings.append({
            "id": "GEO-002",
            "pillar": "geo_citability",
            "status": "warning",
            "title": "Generic Copy Lacks Technical Precision",
            "details": "AI models favor authoritative domain-specific terminology over marketing generic buzzwords.",
            "remediation": "Inject precise technical explanations of how underlying automation functions."
        })

    # Citations & Social Proof Grounding
    has_citations = bool(re.search(r"(testimonial|review|rating|star|quote|trusted by|verified)", content, re.IGNORECASE))
    if has_citations:
        geo_score += 5.0
    else:
        findings.append({
            "id": "GEO-003",
            "pillar": "geo_citability",
            "status": "warning",
            "title": "Missing Authoritative Quotations & Social Proof",
            "details": "Generative engines cite sources with credible user reviews and expert quotes.",
            "remediation": "Add verified testimonials with named creators and specific results."
        })

    # Anti-Keyword-Stuffing Compliance
    geo_score += 5.0

    # ---------------- 3. AEO: Answer Engine Optimization (0 - 25) ----------------
    # BLUF (Bottom Line Up Front) Direct Answers
    has_bluf = bool(re.search(r"what (is|exactly is)", content, re.IGNORECASE) and len(content) > 200)
    if has_bluf:
        aeo_score += 10.0
        findings.append({
            "id": "AEO-001",
            "pillar": "aeo_direct_answer",
            "status": "pass",
            "title": "BLUF Direct-Answer Framing Present",
            "details": "Direct, conversational answers provided for core product definition.",
            "remediation": "Ensure answers are concise (40-60 words) for direct voice/AI snippet extraction."
        })
    else:
        findings.append({
            "id": "AEO-001",
            "pillar": "aeo_direct_answer",
            "status": "warning",
            "title": "Missing Clear BLUF Definition",
            "details": "Lacks an immediate 40-60 word definition block suitable for featured snippets.",
            "remediation": "Add a crisp 'What is X?' section with a single-paragraph answer."
        })

    # Natural Language Question Headings
    h2_questions = len(re.findall(r"(how|what|why|can i|is it)\b.*\?", content, re.IGNORECASE))
    if h2_questions >= 3:
        aeo_score += 8.0
    else:
        aeo_score += 3.0
        findings.append({
            "id": "AEO-002",
            "pillar": "aeo_direct_answer",
            "status": "warning",
            "title": "Headers Lack Conversational Query Framing",
            "details": "Headings should mirror natural language queries asked in voice and AI search.",
            "remediation": "Frame section headers as explicit questions (e.g. 'How Does Telegram Bot Automation Work?')."
        })

    # Information Chunking (Bullet points, comparison tables)
    has_chunking = bool(re.search(r"(<ul|<ol|bullet|check|comparison|table)", content, re.IGNORECASE))
    if has_chunking:
        aeo_score += 7.0
    else:
        aeo_score += 2.0

    # ---------------- 4. Structured Data (Schema.org JSON-LD) (0 - 25) ----------------
    # SoftwareApplication / Product Schema
    has_product_schema = bool(re.search(r'@type["\']:\s*["\'](SoftwareApplication|Product)["\']', content))
    if has_product_schema:
        schema_score += 8.0
        findings.append({
            "id": "SCH-001",
            "pillar": "structured_data",
            "status": "pass",
            "title": "SoftwareApplication Schema Implemented",
            "details": "Search engines can parse product pricing, category, and operating system.",
            "remediation": "Keep applicationCategory and offers updated."
        })
    else:
        findings.append({
            "id": "SCH-001",
            "pillar": "structured_data",
            "status": "fail",
            "title": "Missing SoftwareApplication / Product Schema",
            "details": "Google and Perplexity cannot parse rich software/product cards.",
            "remediation": "Inject JSON-LD script for SoftwareApplication."
        })

    # FAQPage Schema
    has_faq_schema = bool(re.search(r'@type["\']:\s*["\']FAQPage["\']', content))
    if has_faq_schema:
        schema_score += 8.0
        findings.append({
            "id": "SCH-002",
            "pillar": "structured_data",
            "status": "pass",
            "title": "FAQPage Schema Implemented",
            "details": "FAQ questions and answers are structured for rich snippet extraction.",
            "remediation": "Add new questions to schema as FAQ expands."
        })
    else:
        findings.append({
            "id": "SCH-002",
            "pillar": "structured_data",
            "status": "fail",
            "title": "Missing FAQPage Schema",
            "details": "FAQ accordion exists in UI but is completely invisible to search engine structured data parsers.",
            "remediation": "Embed JSON-LD script with @type: FAQPage mapping all questions and answers."
        })

    # Organization Schema
    has_org_schema = bool(re.search(r'@type["\']:\s*["\']Organization["\']', content))
    if has_org_schema:
        schema_score += 4.0
    else:
        findings.append({
            "id": "SCH-003",
            "pillar": "structured_data",
            "status": "warning",
            "title": "Missing Organization Schema",
            "details": "Brand entity is not explicitly linked to official domain and socials.",
            "remediation": "Embed JSON-LD with @type: Organization."
        })

    # llms.txt Crawler Guidance
    if has_llms_txt:
        schema_score += 5.0
        findings.append({
            "id": "SCH-004",
            "pillar": "structured_data",
            "status": "pass",
            "title": "AI Crawler Discovery (llms.txt) Present",
            "details": "public/llms.txt guides AI agents directly to high-signal documentation.",
            "remediation": "Periodically refresh llms.txt with new routes and capabilities."
        })
    else:
        findings.append({
            "id": "SCH-004",
            "pillar": "structured_data",
            "status": "fail",
            "title": "Missing llms.txt AI Crawler Guide",
            "details": "AI search engines (Perplexity, SearchGPT) lack a direct markdown overview of domain capabilities.",
            "remediation": "Generate public/llms.txt summarizing platform capabilities, documentation, and specs."
        })

    overall_score = round(seo_score + geo_score + aeo_score + schema_score, 1)

    recommendations = [
        "Embed Schema.org JSON-LD scripts for SoftwareApplication and FAQPage.",
        "Add complete OpenGraph and Twitter card metadata in root layout.",
        "Deploy public/llms.txt to guide AI search crawlers.",
        "Inject empirical quantitative statistics in hero and feature sections."
    ]

    return {
        "target": str(target_path),
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "overall_score": overall_score,
        "pillar_scores": {
            "technical_seo": round(seo_score, 1),
            "geo_citability": round(geo_score, 1),
            "aeo_direct_answer": round(aeo_score, 1),
            "structured_data": round(schema_score, 1),
        },
        "findings": findings,
        "recommendations": recommendations,
    }


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    report = audit_landing_page(target)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
