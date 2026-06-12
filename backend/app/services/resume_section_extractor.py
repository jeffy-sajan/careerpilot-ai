"""
Resume Section Extractor
========================
A deterministic, regex-based service to parse raw resume text into structured
sections (Contact, Summary, Skills, Experience, Projects, Education, Certifications).
"""

from __future__ import annotations

import re


class ResumeSectionExtractor:
    """
    Extracts structured data from raw resume text using regex and heuristics.
    """

    # ── regex patterns ──────────────────────────────────────────────────────

    EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)
    PHONE_RE = re.compile(
        r"""
        (?:(?:\+?\d{1,3}[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4})
        """,
        re.VERBOSE,
    )
    LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/([A-Za-z0-9_\-]+)/?", re.IGNORECASE)
    GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_\-]+)/?", re.IGNORECASE)

    # Patterns to match section headings.
    # The header should be on its own line (or padded by spaces/stars).
    SECTION_HEADERS = {
        "summary": re.compile(r"^\s*[\*\#\-\_]*\s*(?:SUMMARY|PROFESSIONAL SUMMARY|PROFILE|OBJECTIVE|ABOUT ME)\s*[\*\#\-\_]*\s*$", re.MULTILINE | re.IGNORECASE),
        "experience": re.compile(r"^\s*[\*\#\-\_]*\s*(?:EXPERIENCE|WORK EXPERIENCE|EMPLOYMENT|WORK HISTORY|PROFESSIONAL EXPERIENCE|CAREER HISTORY)\s*[\*\#\-\_]*\s*$", re.MULTILINE | re.IGNORECASE),
        "education": re.compile(r"^\s*[\*\#\-\_]*\s*(?:EDUCATION|ACADEMIC BACKGROUND|ACADEMICS|QUALIFICATIONS)\s*[\*\#\-\_]*\s*$", re.MULTILINE | re.IGNORECASE),
        "skills": re.compile(r"^\s*[\*\#\-\_]*\s*(?:SKILLS|TECHNICAL SKILLS|CORE COMPETENCIES|TECHNOLOGIES|EXPERTISE|IT SKILLS)\s*[\*\#\-\_]*\s*$", re.MULTILINE | re.IGNORECASE),
        "projects": re.compile(r"^\s*[\*\#\-\_]*\s*(?:PROJECTS|PERSONAL PROJECTS|ACADEMIC PROJECTS|OPEN SOURCE|PORTFOLIO)\s*[\*\#\-\_]*\s*$", re.MULTILINE | re.IGNORECASE),
        "certifications": re.compile(r"^\s*[\*\#\-\_]*\s*(?:CERTIFICATIONS|CERTIFICATES|LICENSES|AWARDS|ACHIEVEMENTS)\s*[\*\#\-\_]*\s*$", re.MULTILINE | re.IGNORECASE),
    }

    # Used to split text block into list items
    BULLET_RE = re.compile(r"^[\s]*[•\-\*\u2022\u2023\u25E6\u2043\u2219]+\s*", re.MULTILINE)

    def extract(self, text: str) -> dict:
        """
        Parses the raw text and returns a structured dictionary.
        """
        if not text or not text.strip():
            return {
                "contact": {},
                "summary": "",
                "skills": [],
                "experience": [],
                "projects": [],
                "education": [],
                "certifications": []
            }

        clean_text = text.replace("\u200b", "").replace("\xa0", " ")

        contact = self._extract_contact(clean_text)
        sections = self._extract_sections(clean_text)

        return {
            "contact": contact,
            "summary": self._format_text_block(sections.get("summary", "")),
            "skills": self._format_list_block(sections.get("skills", "")),
            "experience": self._format_list_block(sections.get("experience", "")),
            "projects": self._format_list_block(sections.get("projects", "")),
            "education": self._format_list_block(sections.get("education", "")),
            "certifications": self._format_list_block(sections.get("certifications", "")),
        }

    def _extract_contact(self, text: str) -> dict:
        contact = {}

        # First non-empty line without many numbers/symbols is likely the name
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        if lines:
            first_line = lines[0]
            # Simple heuristic: if it's not super long and looks like a name
            if len(first_line) < 50 and not self.EMAIL_RE.search(first_line) and not self.PHONE_RE.search(first_line):
                contact["name"] = first_line

        email_match = self.EMAIL_RE.search(text)
        if email_match:
            contact["email"] = email_match.group(0)

        phone_match = self.PHONE_RE.search(text)
        if phone_match:
            contact["phone"] = phone_match.group(0).strip()

        linkedin_match = self.LINKEDIN_RE.search(text)
        if linkedin_match:
            # Reconstruct clean url
            contact["linkedin"] = f"linkedin.com/in/{linkedin_match.group(1)}"

        github_match = self.GITHUB_RE.search(text)
        if github_match:
            contact["github"] = f"github.com/{github_match.group(1)}"

        return contact

    def _extract_sections(self, text: str) -> dict[str, str]:
        """
        Splits the text into blocks based on known section headers.
        """
        # Find all section headers and their start positions
        found_sections = []
        for sec_name, pattern in self.SECTION_HEADERS.items():
            for match in pattern.finditer(text):
                found_sections.append({
                    "name": sec_name,
                    "start": match.start(),
                    "end": match.end(),
                })

        # Sort by occurrence in text
        found_sections.sort(key=lambda x: x["start"])

        # Deduplicate headers that match the same location (edge cases)
        unique_sections = []
        last_start = -1
        for sec in found_sections:
            if sec["start"] > last_start:
                unique_sections.append(sec)
                last_start = sec["start"]

        extracted = {}

        # If no sections found, everything is just unclassified (maybe summary)
        if not unique_sections:
            return extracted

        # Extract content between headers
        for i, current_sec in enumerate(unique_sections):
            name = current_sec["name"]
            content_start = current_sec["end"]
            
            if i + 1 < len(unique_sections):
                content_end = unique_sections[i + 1]["start"]
            else:
                content_end = len(text)
                
            block = text[content_start:content_end].strip()
            # If a section appears twice (e.g. multiple "Experience"), append it
            if name in extracted:
                extracted[name] += "\n\n" + block
            else:
                extracted[name] = block

        return extracted

    def _format_text_block(self, text: str) -> str:
        """Cleans up a text block."""
        return re.sub(r'\n+', ' ', text).strip()

    def _format_list_block(self, text: str) -> list[str]:
        """
        Converts a raw section text block into a list of strings.
        Splits by double newlines to separate distinct blocks (like jobs),
        then by bullet points if they exist in the block.
        """
        if not text:
            return []

        # Split by empty lines (paragraphs) first to separate distinct blocks
        blocks = re.split(r'\n\s*\n', text)
        items = []

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            if self.BULLET_RE.search(block):
                parts = self.BULLET_RE.split(block)
                for p in parts:
                    clean = re.sub(r'\n+', ' ', p).strip()
                    if clean:
                        items.append(clean)
            else:
                # No bullets, treat each line as a potential item
                for ln in block.split('\n'):
                    clean = ln.strip()
                    if clean:
                        items.append(clean)

        return items

# Singleton
resume_section_extractor = ResumeSectionExtractor()
