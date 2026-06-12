"""
Resume Classifier Service
=========================
A deterministic, heuristic-based classifier that analyses raw text to determine
whether a document is likely a resume *before* ATS scoring begins.

No external AI APIs are used — everything is regex + keyword matching.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ResumeClassificationResult:
    """Returned by ResumeClassifierService.classify()."""

    is_resume: bool
    confidence: int  # 0-100
    detected_sections: list[str] = field(default_factory=list)
    missing_sections: list[str] = field(default_factory=list)
    warning: str | None = None

    def to_dict(self) -> dict:
        result = {
            "is_resume": self.is_resume,
            "confidence": self.confidence,
            "detected_sections": self.detected_sections,
            "missing_sections": self.missing_sections,
        }
        if self.warning:
            result["warning"] = self.warning
        return result


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

class ResumeClassifierService:
    """
    Scores a document 0-100 based on structural signals common in resumes.

    Scoring breakdown (max 100 pts):
      Contact information  → up to 25 pts
        email              → 10 pts
        phone              → 7  pts
        linkedin / github  → 4  pts each
      Section headings     → up to 55 pts
        experience         → 15 pts
        education          → 12 pts
        skills             → 12 pts
        projects           → 6  pts
        summary/objective  → 5  pts
        certifications     → 5  pts
      Document length      → up to 10 pts
      Formatting patterns  → up to 10 pts
    """

    # ── section keyword maps ────────────────────────────────────────────────

    SECTION_PATTERNS: dict[str, tuple[list[str], int]] = {
        "experience": (
            [
                r"\bexperience\b",
                r"\bemployment\b",
                r"\bwork history\b",
                r"\bprofessional background\b",
                r"\bwork experience\b",
                r"\bcareer history\b",
            ],
            15,
        ),
        "education": (
            [
                r"\beducation\b",
                r"\bacademic background\b",
                r"\bqualifications\b",
                r"\buniversity\b",
                r"\bcollege\b",
                r"\bdegree\b",
                r"\bb\.?s\.?\b",
                r"\bb\.?e\.?\b",
                r"\bm\.?s\.?\b",
                r"\bm\.?b\.?a\.?\b",
                r"\bph\.?d\.?\b",
                r"\bbachelor\b",
                r"\bmaster\b",
            ],
            12,
        ),
        "skills": (
            [
                r"\bskills\b",
                r"\btechnical skills\b",
                r"\bcore competencies\b",
                r"\btechnologies\b",
                r"\btools\b",
                r"\bprogramming languages\b",
            ],
            12,
        ),
        "projects": (
            [
                r"\bprojects\b",
                r"\bpersonal projects\b",
                r"\bacademic projects\b",
                r"\bside projects\b",
                r"\bopen.?source\b",
            ],
            6,
        ),
        "summary": (
            [
                r"\bsummary\b",
                r"\bobjective\b",
                r"\bprofile\b",
                r"\babout me\b",
                r"\bprofessional summary\b",
                r"\bcareer objective\b",
                r"\bexecutive summary\b",
            ],
            5,
        ),
        "certifications": (
            [
                r"\bcertifications?\b",
                r"\bcertified\b",
                r"\blicen[sc]es?\b",
                r"\bawards?\b",
                r"\bachievements?\b",
                r"\bhonours?\b",
                r"\bhonors?\b",
            ],
            5,
        ),
    }

    # ── contact patterns ────────────────────────────────────────────────────

    EMAIL_RE = re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE
    )
    PHONE_RE = re.compile(
        r"""
        (?:
            \+?\d{1,3}[\s\-.]?          # optional country code
        )?
        \(?\d{3}\)?                      # area code
        [\s\-.]?
        \d{3}
        [\s\-.]?
        \d{4}
        """,
        re.VERBOSE,
    )
    LINKEDIN_RE = re.compile(r"linkedin\.com/in/", re.IGNORECASE)
    GITHUB_RE = re.compile(r"github\.com/[A-Za-z0-9_\-]+", re.IGNORECASE)

    # ── formatting patterns ─────────────────────────────────────────────────

    BULLET_RE = re.compile(r"^[\s]*[•\-\*\u2022\u2023\u25E6\u2043\u2219]", re.MULTILINE)
    DATE_RANGE_RE = re.compile(
        r"""
        (?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|
           jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|
           dec(?:ember)?|\d{1,2}\/\d{2,4})
        [\s,\-–—]+
        (?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|
           jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|
           dec(?:ember)?|\d{1,2}\/\d{2,4}|present|current|now|\d{4})
        """,
        re.VERBOSE | re.IGNORECASE,
    )

    # ── confidence thresholds ───────────────────────────────────────────────

    ACCEPT_THRESHOLD = 70
    WARN_THRESHOLD = 40

    # ── public API ──────────────────────────────────────────────────────────

    def classify(self, text: str) -> ResumeClassificationResult:
        """
        Analyse *text* and return a :class:`ResumeClassificationResult`.

        Parameters
        ----------
        text:
            Raw extracted text from the uploaded document.
        """
        if not text or not text.strip():
            return ResumeClassificationResult(
                is_resume=False,
                confidence=0,
                warning="The document does not appear to be a resume.",
            )

        clean = text.replace("\u200b", "").replace("\xa0", " ")
        lower = clean.lower()

        score = 0

        # 1. Contact information (25 pts max)
        score += self._score_contact(clean)

        # 2. Section headings (55 pts max)
        detected, missing = self._score_sections(lower)
        section_score = sum(
            self.SECTION_PATTERNS[s][1]
            for s in detected
            if s in self.SECTION_PATTERNS
        )
        score += section_score

        # 3. Document length (10 pts max)
        score += self._score_length(clean)

        # 4. Formatting patterns (10 pts max)
        score += self._score_formatting(clean)

        # Cap at 100
        confidence = max(0, min(100, score))

        return self._build_result(confidence, detected, missing)

    # ── private helpers ─────────────────────────────────────────────────────

    def _score_contact(self, text: str) -> int:
        pts = 0
        if self.EMAIL_RE.search(text):
            pts += 10
        if self.PHONE_RE.search(text):
            pts += 7
        if self.LINKEDIN_RE.search(text):
            pts += 4
        if self.GITHUB_RE.search(text):
            pts += 4
        return pts

    def _score_sections(self, lower_text: str) -> tuple[list[str], list[str]]:
        detected: list[str] = []
        missing: list[str] = []

        for section_name, (patterns, _pts) in self.SECTION_PATTERNS.items():
            found = any(
                re.search(p, lower_text) for p in patterns
            )
            if found:
                detected.append(section_name)
            else:
                missing.append(section_name)

        return detected, missing

    def _score_length(self, text: str) -> int:
        """
        Optimal resume length is roughly 200-800 words.
        Very short or very long documents get fewer points.
        """
        word_count = len(text.split())
        if word_count < 50:
            return 0
        if word_count < 150:
            return 4
        if word_count <= 800:
            return 10
        if word_count <= 1500:
            return 7
        # Very long document — likely not a resume
        return 3

    def _score_formatting(self, text: str) -> int:
        """
        Award points for patterns common in resumes:
          - Bullet points
          - Date ranges (employment / education periods)
        """
        pts = 0
        if len(self.BULLET_RE.findall(text)) >= 3:
            pts += 5
        if self.DATE_RANGE_RE.search(text):
            pts += 5
        return pts

    def _build_result(
        self,
        confidence: int,
        detected: list[str],
        missing: list[str],
    ) -> ResumeClassificationResult:
        if confidence >= self.ACCEPT_THRESHOLD:
            return ResumeClassificationResult(
                is_resume=True,
                confidence=confidence,
                detected_sections=detected,
                missing_sections=missing,
            )

        if confidence >= self.WARN_THRESHOLD:
            return ResumeClassificationResult(
                is_resume=True,  # still proceed, but with a warning
                confidence=confidence,
                detected_sections=detected,
                missing_sections=missing,
                warning=(
                    "This document may not be a resume. "
                    "ATS results may be unreliable."
                ),
            )

        # Below WARN_THRESHOLD → reject
        return ResumeClassificationResult(
            is_resume=False,
            confidence=confidence,
            detected_sections=detected,
            missing_sections=missing,
            warning="The uploaded document does not appear to be a resume.",
        )


# Singleton for use across the application
resume_classifier = ResumeClassifierService()
