"""
ATS Feedback Generator
======================
Generates strengths, weaknesses, and recommendations using deterministic
rule-based logic based on the raw metrics from the section quality scorer
and formatting checks.
"""

from __future__ import annotations


class ATSFeedbackGenerator:
    """
    Evaluates scoring details and maps them to human-readable feedback using templates.
    """

    def generate(self, formatting_details: dict, quality_details: dict) -> dict:
        """
        Combines formatting details and quality details to produce final feedback.
        """
        strengths = []
        weaknesses = []
        recommendations = []

        # ── Formatting Feedback ──────────────────────────────────────────────

        if formatting_details.get("has_email"):
            strengths.append("Contact information (email) is present.")
        else:
            weaknesses.append("Missing email address.")
            recommendations.append("Add a professional email address for contact.")

        if formatting_details.get("has_phone"):
            strengths.append("Contact information (phone number) is present.")
        else:
            weaknesses.append("Missing phone number.")
            recommendations.append("Add a phone number so recruiters can reach you easily.")

        if formatting_details.get("has_linkedin"):
            strengths.append("Professional profile (LinkedIn) included.")
        else:
            weaknesses.append("Missing LinkedIn profile link.")
            recommendations.append("Include a link to your LinkedIn profile.")

        word_count = formatting_details.get("word_count", 0)
        if word_count < 150:
            weaknesses.append("Resume is too short (under 150 words).")
            recommendations.append("Expand on your experience with more detailed descriptions.")
        elif word_count > 1000:
            weaknesses.append("Resume might be too long (over 1000 words).")
            recommendations.append("Consider condensing to highlight the most relevant points.")

        if formatting_details.get("has_bullets"):
            strengths.append("Good use of bullet points for readability.")
        else:
            weaknesses.append("Lack of bullet points makes it hard to scan.")
            recommendations.append("Use bullet points rather than long paragraphs.")

        if formatting_details.get("has_summary"):
            strengths.append("Professional summary or objective statement present.")
        else:
            weaknesses.append("Missing professional summary or objective.")
            recommendations.append("Add a brief professional summary at the top of your resume.")

        if formatting_details.get("has_consistent_dates"):
            strengths.append("Consistent date formatting detected in experience entries.")
        else:
            weaknesses.append("Dates are missing or inconsistently formatted.")
            recommendations.append("Use consistent date formatting (e.g., 'Jan 2023 - Present').")

        if formatting_details.get("has_portfolio_links"):
            strengths.append("Technical profile links included (GitHub/Portfolio).")
        else:
            recommendations.append("Include links to your GitHub or portfolio to showcase your work.")

        # ── Experience Feedback ──────────────────────────────────────────────
        exp_section = quality_details.get("experience", {})
        exp_details = exp_section.get("details", {})
        exp_count = exp_details.get("entry_count", 0)

        if exp_count == 0:
            weaknesses.append("No experience entries detected.")
            recommendations.append("Add a 'Work Experience' section with at least 2-3 roles.")
        elif exp_count >= 3:
            strengths.append(f"Solid experience section with {exp_count} entries.")
        else:
            recommendations.append("Consider adding more detail to each experience entry with bullet points.")

        verbs = exp_details.get("action_verbs_found", [])
        if len(verbs) >= 4:
            strengths.append(f"Strong action verbs used ({', '.join(verbs[:5])}).")
        elif len(verbs) == 0 and exp_count > 0:
            weaknesses.append("No action verbs detected in experience.")
            recommendations.append("Start bullet points with strong action verbs like 'Developed', 'Managed', 'Optimized'.")
        elif exp_count > 0:
            recommendations.append("Use a wider variety of action verbs to strengthen your experience descriptions.")

        metrics_count = exp_details.get("metrics_count", 0)
        if metrics_count >= 3:
            strengths.append("Excellent use of quantifiable metrics to demonstrate impact.")
        elif metrics_count == 0 and exp_count > 0:
            weaknesses.append("No measurable achievements found.")
            recommendations.append("Quantify your impact with numbers, percentages, or dollar amounts.")
        elif exp_count > 0:
            recommendations.append("Add more quantifiable metrics to showcase your achievements.")

        bullet_ratio = exp_details.get("good_bullet_ratio", 0)
        if exp_count > 0:
            if bullet_ratio >= 0.6:
                strengths.append("Well-structured bullet points with appropriate detail.")
            elif bullet_ratio < 0.3:
                weaknesses.append("Experience bullets lack detail or are too short.")
                recommendations.append("Expand your bullet points to provide more context (ideal length: 8-30 words).")

        # ── Skills Feedback ──────────────────────────────────────────────────
        skills_section = quality_details.get("skills", {})
        skills_details = skills_section.get("details", {})
        skill_count = skills_details.get("skill_count", 0)

        if skill_count == 0:
            weaknesses.append("No skills section detected.")
            recommendations.append("Add a 'Skills' section listing your technical and soft skills.")
        elif skill_count >= 10:
            strengths.append(f"Comprehensive list of {skill_count} skills.")
        else:
            recommendations.append("Consider adding more relevant skills to your profile.")

        cat_entries = skills_details.get("categorized_entries", 0)
        if cat_entries >= 2:
            strengths.append("Skills are well-categorized for readability.")
        elif skill_count >= 10:
            recommendations.append("Categorize your skills (e.g., 'Languages: Python, Java') to improve readability.")

        # ── Projects Feedback ────────────────────────────────────────────────
        proj_section = quality_details.get("projects", {})
        proj_details = proj_section.get("details", {})
        proj_count = proj_details.get("project_count", 0)

        if proj_count == 0:
            weaknesses.append("No projects section detected.")
            recommendations.append("Add a 'Projects' section showcasing 2-3 personal or academic projects.")
        elif proj_count >= 2:
            strengths.append(f"Strong projects section with {proj_count} highlighted projects.")

        tech_mentioned = proj_details.get("technologies_mentioned", [])
        if len(tech_mentioned) >= 3:
            strengths.append("Projects explicitly mention the technologies used.")
        elif proj_count > 0:
            recommendations.append("Explicitly state which technologies and tools you used in each project.")

        avg_words = proj_details.get("avg_words_per_project", 0)
        if proj_count > 0:
            if avg_words >= 12:
                strengths.append("Project descriptions are detailed and informative.")
            elif avg_words >= 6:
                recommendations.append("Expand project descriptions with more detail about your role and impact.")
            else:
                weaknesses.append("Project descriptions are too brief.")
                recommendations.append("Write 1-2 sentences per project explaining what you built, what technologies you used, and what the outcome was.")

        # ── Education Feedback ───────────────────────────────────────────────

        edu_section = quality_details.get("education", {})
        edu_details = edu_section.get("details", {})
        degrees = edu_details.get("degrees_found", [])
        institutions = edu_details.get("institution_signals", [])

        if degrees == [] and institutions == []:
            weaknesses.append("No recognizable education section detected.")
            recommendations.append("Add an 'Education' section with your degree and institution.")
        else:
            if degrees:
                strengths.append(f"Degree(s) detected: {', '.join(degrees[:3])}.")
            else:
                weaknesses.append("No recognizable degree found.")
                recommendations.append("Clearly state your degree (e.g., 'B.S. in Computer Science').")

            if institutions:
                strengths.append("Educational institution clearly identified.")
            else:
                weaknesses.append("No recognizable institution name found.")
                recommendations.append("Include the full name of your university or college.")

        return {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
        }

# Singleton
ats_feedback_generator = ATSFeedbackGenerator()
