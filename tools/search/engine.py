"""Lexical and tag-based search engine for registered skills."""

from dataclasses import dataclass
from typing import Dict, List, Optional
from tools.core.models import RegistrySkill


@dataclass
class SearchResult:
    skill: RegistrySkill
    score: float
    matched_fields: List[str]

    def to_dict(self) -> Dict:
        return {
            "id": self.skill.id,
            "name": self.skill.name,
            "type": self.skill.type.value,
            "category": self.skill.category,
            "status": self.skill.status.value,
            "description": self.skill.description,
            "score": round(self.score, 2),
            "matched_fields": self.matched_fields,
            "tags": self.skill.tags,
        }


class SearchEngine:
    def __init__(self, registry: Dict[str, RegistrySkill]):
        self.registry = registry

    def search(
        self,
        query: str,
        skill_type: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[SearchResult]:
        q_tokens = [t.lower() for t in query.strip().split() if t.strip()]
        results: List[SearchResult] = []

        for skill in self.registry.values():
            if skill_type and skill.type.value != skill_type:
                continue
            if category and skill.category.lower() != category.lower():
                continue
            if status and skill.status.value != status.lower():
                continue

            if not q_tokens:
                # If query is empty, match all under filters
                results.append(SearchResult(skill=skill, score=1.0, matched_fields=["filter"]))
                continue

            score = 0.0
            matched_fields = []

            for token in q_tokens:
                # Exact ID match
                if token == skill.id.lower():
                    score += 10.0
                    matched_fields.append("id:exact")
                elif token in skill.id.lower():
                    score += 5.0
                    matched_fields.append("id:substring")

                # Name match
                if token in skill.name.lower():
                    score += 4.0
                    matched_fields.append("name")

                # Tags match
                if any(token == tag.lower() for tag in skill.tags):
                    score += 5.0
                    matched_fields.append("tags:exact")
                elif any(token in tag.lower() for tag in skill.tags):
                    score += 2.0
                    matched_fields.append("tags:substring")

                # Category match
                if token in skill.category.lower():
                    score += 3.0
                    matched_fields.append("category")

                # Description match
                if token in skill.description.lower():
                    score += 1.5
                    matched_fields.append("description")

            if score > 0:
                results.append(SearchResult(skill=skill, score=score, matched_fields=list(set(matched_fields))))

        results.sort(key=lambda r: r.score, reverse=True)
        return results
