"""Explainable skill discovery and recommendation engine.

Analyzes natural language task descriptions, matches technology keywords,
detects engineering quality requirements, and applies governance policies.
"""

from dataclasses import dataclass
import re
from typing import Dict, List, Optional
from tools.core.models import RegistrySkill, SkillType


@dataclass
class Recommendation:
    id: str
    name: str
    confidence: float
    reasons: List[str]
    type: str
    category: str
    kind: str  # 'direct', 'recommended', 'governance'

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "confidence": round(self.confidence, 2),
            "reasons": self.reasons,
            "type": self.type,
            "category": self.category,
            "kind": self.kind,
        }


class DiscoveryEngine:
    # Rule mappings for domain keyword intents
    KEYWORD_INTENTS = {
        "mongodb": [r"\bmongo(db)?\b", r"\bnosql\b", r"\bmongoose\b", r"\batlas\b"],
        "nodejs": [r"\bnode(\.?js)?\b", r"\bexpress\b", r"\bnpm\b", r"\bjavascript\b"],
        "nextjs": [r"\bnext(\.?js)?\b", r"\breact\b", r"\bapp router\b", r"\bvercel\b"],
        "flutter": [r"\bflutter\b", r"\bdart\b", r"\bmobile app\b", r"\bwidgets?\b"],
        "go": [r"\bgolang\b", r"\bgo\b", r"\bgoroutines?\b"],
        "testing": [r"\btests?\b", r"\btesting\b", r"\bqa\b", r"\btdd\b", r"\bunit test\b", r"\btest coverage\b"],
        "observability-instrumentation": [r"\bopentelemetry\b", r"\botel\b", r"\btracing\b", r"\btelemetry\b", r"\bmetrics\b", r"\bspans?\b"],
        "observability-platform": [r"\bgrafana\b", r"\bprometheus\b", r"\bpromql\b", r"\bloki\b", r"\btempo\b", r"\balloy\b", r"\bmonitoring\b", r"\bdashboards?\b"],
    }

    # Governance policies triggered by production/architecture scope
    GOVERNANCE_KEYWORDS = [
        r"\bproduction\b",
        r"\barchitecture\b",
        r"\bmission[ -]critical\b",
        r"\bscale\b",
        r"\benterprise\b",
        r"\bapi\b",
        r"\brefactor\b",
        r"\bhigh[ -]concurrency\b",
    ]

    def __init__(self, registry: Dict[str, RegistrySkill]):
        self.registry = registry

    def discover(self, task_description: str) -> List[Recommendation]:
        text = task_description.lower()
        recommendations: Dict[str, Recommendation] = {}

        # 1. Direct technology/practice intent matching
        for skill_id, patterns in self.KEYWORD_INTENTS.items():
            if skill_id not in self.registry:
                continue
            skill = self.registry[skill_id]
            reasons = []
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    reasons.append(f"Explicit intent match: '{match.group(0)}'")

            if reasons:
                recommendations[skill_id] = Recommendation(
                    id=skill.id,
                    name=skill.name,
                    confidence=0.95 if skill.type == SkillType.TECHNOLOGY else 0.85,
                    reasons=reasons,
                    type=skill.type.value,
                    category=skill.category,
                    kind="direct" if skill.type == SkillType.TECHNOLOGY else "recommended",
                )

        # 2. Production Quality Policy: If 'production', 'api', or 'service' is mentioned, recommend testing
        if "testing" in self.registry and "testing" not in recommendations:
            if any(re.search(pat, text) for pat in [r"\bproduction\b", r"\bapi\b", r"\bbackend\b", r"\bservice\b"]):
                skill = self.registry["testing"]
                recommendations["testing"] = Recommendation(
                    id=skill.id,
                    name=skill.name,
                    confidence=0.85,
                    reasons=["Engineering Practice Policy: Production service/API tasks require automated testing"],
                    type=skill.type.value,
                    category=skill.category,
                    kind="recommended",
                )

        # 3. Observability Policy: If 'production' and any backend/runtime is selected, recommend observability
        has_backend = any(sid in recommendations for sid in ["nodejs", "go", "nextjs", "mongodb"])
        if has_backend and re.search(r"\bproduction\b", text):
            if "observability-instrumentation" in self.registry and "observability-instrumentation" not in recommendations:
                skill = self.registry["observability-instrumentation"]
                recommendations["observability-instrumentation"] = Recommendation(
                    id=skill.id,
                    name=skill.name,
                    confidence=0.80,
                    reasons=["Engineering Governance: Production backend deployments require observability instrumentation"],
                    type=skill.type.value,
                    category=skill.category,
                    kind="recommended",
                )

        # 4. Architectural Governance Policy: Architecture validator recommendation
        if "architecture.system-validator" in self.registry:
            validator_reasons = []
            for pattern in self.GOVERNANCE_KEYWORDS:
                match = re.search(pattern, text)
                if match:
                    validator_reasons.append(f"Keyword '{match.group(0)}' triggers architectural & edge-case governance")

            # Also trigger if 2 or more technology/backend skills are selected
            tech_count = sum(1 for r in recommendations.values() if r.type == "technology")
            if tech_count >= 2:
                validator_reasons.append(f"Multi-technology integration ({tech_count} components) requires cross-domain invariant validation")

            if validator_reasons:
                skill = self.registry["architecture.system-validator"]
                recommendations["architecture.system-validator"] = Recommendation(
                    id=skill.id,
                    name=skill.name,
                    confidence=0.90 if len(validator_reasons) > 1 else 0.80,
                    reasons=validator_reasons,
                    type=skill.type.value,
                    category=skill.category,
                    kind="governance",
                )

        # Sort recommendations: direct first, then highest confidence
        result_list = list(recommendations.values())
        result_list.sort(key=lambda r: (r.kind == "direct", r.confidence), reverse=True)
        return result_list
