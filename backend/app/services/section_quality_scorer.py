"""
Section Quality Scorer
======================
Evaluates the quality of individual resume sections using deterministic
heuristics. Consumes the structured output from ResumeSectionExtractor
and returns per-section scores with feedback.

Score Budget (total = 60 out of 100):
  experience_score:  max 25
  skills_score:      max 15
  projects_score:    max 12
  education_score:   max  8
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ── Constants ────────────────────────────────────────────────────────────────

ACTION_VERBS: set[str] = {
    # Leadership / Management
    "managed", "led", "directed", "supervised", "coordinated", "spearheaded",
    "oversaw", "headed", "mentored", "guided",
    # Creation / Development
    "developed", "created", "designed", "built", "engineered", "architected",
    "implemented", "launched", "established", "initiated", "introduced",
    # Improvement / Optimization
    "improved", "enhanced", "optimized", "streamlined", "accelerated",
    "boosted", "increased", "reduced", "decreased", "minimized",
    "consolidated", "revamped", "modernized", "refactored",
    # Analysis / Research
    "analyzed", "evaluated", "assessed", "researched", "investigated",
    "identified", "diagnosed", "resolved", "troubleshot",
    # Communication / Collaboration
    "presented", "communicated", "collaborated", "negotiated",
    "facilitated", "advocated",
    # Technical
    "deployed", "configured", "automated", "integrated", "migrated",
    "maintained", "tested", "debugged", "monitored", "provisioned",
    "containerized", "orchestrated",
}

METRICS_RE = re.compile(
    r"""
    \d+\s*%                  |   # percentages: 20%, 30 %
    \$\s*[\d,.]+[KMBkmb]?    |   # dollar amounts: $1,000, $2M
    \d+x                     |   # multipliers: 3x, 10x
    \b\d{2,}\+?\b                # significant numbers: 50, 100+
    """,
    re.VERBOSE,
)

DEGREE_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(?:B\.?S\.?|B\.?A\.?|Bachelor(?:'?s)?)\b", re.IGNORECASE),
    re.compile(r"\b(?:M\.?S\.?|M\.?A\.?|Master(?:'?s)?|MBA)\b", re.IGNORECASE),
    re.compile(r"\b(?:Ph\.?D\.?|Doctorate|Doctor)\b", re.IGNORECASE),
    re.compile(r"\b(?:Associate(?:'?s)?)\b", re.IGNORECASE),
    re.compile(r"\b(?:Diploma|Certificate)\b", re.IGNORECASE),
]

INSTITUTION_SIGNALS: list[str] = [
    "university", "college", "institute", "school",
    "polytechnic", "academy", "iit", "mit", "stanford",
    "harvard", "cambridge", "oxford",
]

# Common tech skills for categorization
SKILL_CATEGORIES: dict[str, set[str]] = {
    "languages": {
        "python", "java", "javascript", "typescript", "c++", "c#", "go",
        "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
        "perl", "lua", "dart", "elixir", "haskell", "sql", "html", "css",
        "bash", "shell", "powershell",
    },
    "frameworks": {
        "react", "angular", "vue", "next.js", "nextjs", "nuxt", "svelte",
        "django", "flask", "fastapi", "spring", "express", "nest",
        "rails", "laravel", ".net", "asp.net", "flutter", "react native",
        "electron", "gatsby", "remix",
    },
    "databases": {
        "postgresql", "postgres", "mysql", "mongodb", "redis", "sqlite",
        "oracle", "dynamodb", "cassandra", "elasticsearch", "neo4j",
        "firebase", "supabase", "mariadb", "cockroachdb",
    },
    "devops_cloud": {
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "jenkins", "github actions", "ci/cd", "ansible", "circleci",
        "linux", "nginx", "apache", "vercel", "netlify", "heroku",
        "cloudflare",
    },
    "tools": {
        "git", "jira", "confluence", "figma", "postman", "webpack",
        "vite", "babel", "eslint", "prettier", "npm", "yarn",
        "maven", "gradle",
    },
    "concepts": {
        "rest", "graphql", "microservices", "agile", "scrum", "kanban",
        "tdd", "ci/cd", "devops", "machine learning", "deep learning",
        "data science", "nlp", "computer vision",
    },
}


@dataclass
class SectionScore:
    """Score result for a single section."""
    score: int
    max_score: int
    details: dict = field(default_factory=dict)


@dataclass
class QualityResult:
    """Aggregated quality evaluation across all sections."""
    experience: SectionScore
    skills: SectionScore
    projects: SectionScore
    education: SectionScore

    @property
    def total_score(self) -> int:
        return self.experience.score + self.skills.score + self.projects.score + self.education.score

    @property
    def max_total(self) -> int:
        return self.experience.max_score + self.skills.max_score + self.projects.max_score + self.education.max_score

    def to_dict(self) -> dict:
        def _sec(s: SectionScore) -> dict:
            return {
                "score": s.score,
                "max_score": s.max_score,
                "details": s.details,
            }
        return {
            "experience_score": self.experience.score,
            "skills_score": self.skills.score,
            "projects_score": self.projects.score,
            "education_score": self.education.score,
            "total_section_quality_score": self.total_score,
            "max_section_quality_score": self.max_total,
            "breakdown": {
                "experience": _sec(self.experience),
                "skills": _sec(self.skills),
                "projects": _sec(self.projects),
                "education": _sec(self.education),
            },
        }


class SectionQualityScorer:
    """
    Evaluates the quality of each resume section deterministically.
    """

    # ── Experience (max 25) ──────────────────────────────────────────────────

    def score_experience(self, entries: list[str]) -> SectionScore:
        """
        Scoring breakdown (max 25):
          - Number of entries:      up to 7 pts (1pt per entry, cap 7)
          - Action verb usage:      up to 8 pts
          - Measurable achievements up to 6 pts
          - Bullet quality:         up to 4 pts
        """
        result = SectionScore(score=0, max_score=25)

        if not entries:
            result.details["entry_count"] = 0
            result.details["action_verbs_found"] = []
            result.details["metrics_count"] = 0
            result.details["good_bullet_ratio"] = 0.0
            return result

        # ── entry count (max 7) ──
        entry_pts = min(len(entries), 7)
        result.score += entry_pts
        result.details["entry_count"] = len(entries)

        # ── action verbs (max 8) ──
        combined_lower = " ".join(entries).lower()
        found_verbs = [v for v in ACTION_VERBS if v in combined_lower]
        verb_pts = min(len(found_verbs) * 2, 8)
        result.score += verb_pts
        result.details["action_verbs_found"] = sorted(found_verbs)

        # ── measurable achievements (max 6) ──
        metrics_count = len(METRICS_RE.findall(combined_lower))
        metric_pts = min(metrics_count * 2, 6)
        result.score += metric_pts
        result.details["metrics_count"] = metrics_count

        # ── bullet quality (max 4) ──
        # Good bullets are 8-25 words long
        good_bullets = sum(
            1 for e in entries if 8 <= len(e.split()) <= 30
        )
        bullet_ratio = good_bullets / len(entries) if entries else 0
        if bullet_ratio >= 0.6:
            bullet_pts = 4
        elif bullet_ratio >= 0.3:
            bullet_pts = 2
        else:
            bullet_pts = 0
            
        result.score += bullet_pts
        result.details["good_bullet_ratio"] = round(bullet_ratio, 2)

        result.score = min(result.score, result.max_score)
        return result

    # ── Skills (max 15) ──────────────────────────────────────────────────────

    def score_skills(self, skills: list[str]) -> SectionScore:
        """
        Scoring breakdown (max 15):
          - Number of skills:       up to 5 pts
          - Skill diversity:        up to 5 pts (categories covered)
          - Categorization clarity: up to 5 pts
        """
        result = SectionScore(score=0, max_score=15)

        if not skills:
            result.details["skill_count"] = 0
            result.details["categories_covered"] = []
            result.details["categorized_entries"] = 0
            return result

        # Flatten: skills may come as "Python, Java, C++" in a single entry
        flat_skills: list[str] = []
        for s in skills:
            # Split by commas, pipes, semicolons
            parts = re.split(r"[,|;]", s)
            flat_skills.extend(p.strip() for p in parts if p.strip())

        skill_count = len(flat_skills)
        result.details["skill_count"] = skill_count

        # ── count (max 5) ──
        count_pts = min(skill_count, 5)
        result.score += count_pts

        # ── diversity (max 5) ──
        skills_lower = {s.lower() for s in flat_skills}
        categories_found: set[str] = set()
        for cat_name, cat_skills in SKILL_CATEGORIES.items():
            if skills_lower & cat_skills:
                categories_found.add(cat_name)

        diversity_pts = min(len(categories_found), 5)
        result.score += diversity_pts
        result.details["categories_covered"] = sorted(categories_found)

        # ── categorization (max 5) ──
        categorized_entries = sum(1 for s in skills if ":" in s)
        if categorized_entries >= 2:
            cat_pts = 5
        elif categorized_entries == 1:
            cat_pts = 3
        else:
            cat_pts = 1  # At least they have a skills section
        result.score += cat_pts
        result.details["categorized_entries"] = categorized_entries

        result.score = min(result.score, result.max_score)
        return result

    # ── Projects (max 12) ────────────────────────────────────────────────────

    def score_projects(self, projects: list[str]) -> SectionScore:
        """
        Scoring breakdown (max 12):
          - Number of projects:     up to 4 pts
          - Technologies mentioned: up to 4 pts
          - Description quality:    up to 4 pts
        """
        result = SectionScore(score=0, max_score=12)

        if not projects:
            result.details["project_count"] = 0
            result.details["technologies_mentioned"] = []
            result.details["avg_words_per_project"] = 0.0
            return result

        project_count = len(projects)
        result.details["project_count"] = project_count

        # ── count (max 4) ──
        count_pts = min(project_count, 4)
        result.score += count_pts

        # ── technologies (max 4) ──
        combined = " ".join(projects).lower()
        all_known_techs = set()
        for cat_skills in SKILL_CATEGORIES.values():
            all_known_techs |= cat_skills

        techs_found = {t for t in all_known_techs if t in combined}
        tech_pts = min(len(techs_found) * 2, 4)
        result.score += tech_pts
        result.details["technologies_mentioned"] = sorted(techs_found)

        # ── description quality (max 4) ──
        avg_words = sum(len(p.split()) for p in projects) / len(projects) if projects else 0
        if avg_words >= 12:
            desc_pts = 4
        elif avg_words >= 6:
            desc_pts = 2
        else:
            desc_pts = 0
            
        result.score += desc_pts
        result.details["avg_words_per_project"] = round(avg_words, 1)

        result.score = min(result.score, result.max_score)
        return result

    # ── Education (max 8) ────────────────────────────────────────────────────

    def score_education(self, education: list[str]) -> SectionScore:
        """
        Scoring breakdown (max 8):
          - Degree detection:     up to 4 pts
          - Institution detection up to 4 pts
        """
        result = SectionScore(score=0, max_score=8)

        if not education:
            result.details["degrees_found"] = []
            result.details["institution_signals"] = []
            return result

        combined = " ".join(education)
        combined_lower = combined.lower()

        # ── degree (max 4) ──
        degrees_found: list[str] = []
        for pattern in DEGREE_PATTERNS:
            matches = pattern.findall(combined)
            degrees_found.extend(matches)

        if degrees_found:
            degree_pts = min(len(degrees_found) * 2, 4)
        else:
            degree_pts = 0
            
        result.score += degree_pts
        result.details["degrees_found"] = degrees_found

        # ── institution (max 4) ──
        institutions = [
            sig for sig in INSTITUTION_SIGNALS if sig in combined_lower
        ]
        if institutions:
            inst_pts = min(len(institutions) * 2, 4)
        else:
            inst_pts = 0
            
        result.score += inst_pts
        result.details["institution_signals"] = institutions

        result.score = min(result.score, result.max_score)
        return result

    # ── Public API ───────────────────────────────────────────────────────────

    def evaluate(self, structured_sections: dict) -> QualityResult:
        """
        Takes the output of ResumeSectionExtractor.extract() and returns
        a full quality evaluation.
        """
        return QualityResult(
            experience=self.score_experience(structured_sections.get("experience", [])),
            skills=self.score_skills(structured_sections.get("skills", [])),
            projects=self.score_projects(structured_sections.get("projects", [])),
            education=self.score_education(structured_sections.get("education", [])),
        )


# Singleton
section_quality_scorer = SectionQualityScorer()
