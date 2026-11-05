from pathlib import Path

import pandas as pd

OUTPUT_PATH = Path("data/campaign_career_advancement_100_topics.xlsx")

AI_TOPICS = [
    "Build AI Portfolio Projects Recruiters Notice",
    "Prompt Engineering for Career Growth",
    "How To Explain LLM Work in Interviews",
    "AI Resume Keywords That Improve Screening",
    "Practical RAG Skills for Job Roles",
    "Showcasing AI Impact with Business Metrics",
    "From AI Demos to Production Thinking",
    "AI System Design Tips for Mid Level Engineers",
    "Creating AI Case Studies for LinkedIn Credibility",
    "Model Evaluation Habits Hiring Managers Respect",
    "How To Discuss AI Tradeoffs Clearly",
    "Responsible AI Talking Points for Interviews",
    "Building a Personal AI Learning Roadmap",
    "Using Open Source AI to Stand Out",
    "AI Product Thinking for Engineers",
    "How To Translate AI Work for Non Technical Stakeholders",
    "AI Failure Stories That Build Trust",
    "Choosing AI Certifications That Matter",
    "AI Project Scoping Tips for Career Growth",
    "Data Quality Mindset for AI Roles",
    "How To Build Reusable AI Components",
    "AI Performance Optimization in Career Stories",
    "Writing Better AI Post Mortems",
    "Career Lessons from AI Incident Response",
    "AI Feature Prioritization for Product Teams",
    "How To Prepare for AI Leadership Roles",
    "GenAI Security Basics for Career Advancement",
    "AI Communication Skills for Cross Functional Teams",
    "AI Experiment Tracking for Better Visibility",
    "Mentoring Juniors in AI Teams",
    "Career Growth Through AI Documentation",
    "AI Cost Awareness Skills That Impress Employers",
    "How To Build AI Proof of Concept Quickly",
    "AI Roadmap Alignment with Business Goals",
]

DEVOPS_TOPICS = [
    "DevOps Fundamentals That Accelerate Promotions",
    "CI CD Metrics That Prove Your Impact",
    "How To Present Deployment Improvements",
    "SRE Mindset for Career Advancement",
    "Incident Management Stories for Interviews",
    "Infrastructure as Code Portfolio Ideas",
    "DevOps Automation Wins Recruiters Understand",
    "Observability Skills for Senior Roles",
    "Kubernetes Topics To Learn for Career Growth",
    "Platform Engineering Basics for Engineers",
    "Reducing MTTR and Showing Leadership",
    "DevOps Security Practices for Better Roles",
    "Release Management Habits That Build Trust",
    "Cloud Cost Optimization in Career Narratives",
    "Building Reliable On Call Practices",
    "How To Document Operational Excellence",
    "DevOps Skills Matrix for Self Assessment",
    "Scaling CI Pipelines with Quality Gates",
    "DevOps Collaboration with Product Teams",
    "Root Cause Analysis Techniques for Growth",
    "Monitoring Dashboards That Highlight Impact",
    "Blue Green and Canary Strategy Career Value",
    "Secrets Management Best Practices for Engineers",
    "Resilience Engineering Lessons for Promotions",
    "Service Ownership and Career Progression",
    "Versioning Strategies That Reduce Risk",
    "DevOps Interview Preparation Checklist",
    "How To Lead Post Incident Reviews",
    "Building Internal Developer Platforms",
    "Golden Signals and Career Storytelling",
    "DevOps Governance for Growing Teams",
    "From Script Automation to Platform Thinking",
    "Runbook Quality and Team Effectiveness",
]

CAREER_TOPICS = [
    "Career Roadmap Planning for Engineers",
    "How To Set Quarterly Career Goals",
    "Building Executive Communication Skills",
    "Networking Strategies That Actually Work",
    "How To Ask for Better Projects",
    "Promotion Packet Essentials for Tech Roles",
    "Managing Stakeholders with Confidence",
    "Career Growth Through Mentorship",
    "Personal Branding on LinkedIn for Engineers",
    "Writing Achievement Focused Resume Bullets",
    "Job Search Pipeline Management Tips",
    "Interview Story Framework Using STAR",
    "Salary Negotiation Preparation for Professionals",
    "How To Build Credibility in New Teams",
    "Time Management for High Performers",
    "Conflict Resolution Skills for Career Progress",
    "How To Become a Better Technical Mentor",
    "Developing Leadership Without a Title",
    "Career Decisions Based on Learning Velocity",
    "How To Recover from Career Setbacks",
    "Building Confidence Through Small Wins",
    "Asking Better Questions in Meetings",
    "Cross Team Collaboration for Visibility",
    "Managing Up Without Losing Authenticity",
    "How To Prioritize Work That Matters",
    "Creating a Weekly Career Review Habit",
    "Public Speaking Tips for Engineers",
    "How To Build a Strong Professional Portfolio",
    "Finding the Right Career Community",
    "Career Advancement Through Writing",
    "Strategic Volunteering for Growth",
    "Transitioning from IC to Lead Roles",
    "Career Compass for Long Term Success",
]

ALL_TOPICS = AI_TOPICS + DEVOPS_TOPICS + CAREER_TOPICS
assert len(ALL_TOPICS) == 100
assert len(set(ALL_TOPICS)) == 100

HASHTAGS = "#Microsoft #Google #Amazon #LinkedIn #Indeed #Naukri #Glassdoor #Wellfound #Jobs #CareerGrowth"


def infer_category(topic: str) -> str:
    if topic in AI_TOPICS:
        return "AI"
    if topic in DEVOPS_TOPICS:
        return "DEVOPS"
    return "CAREER"


def build_rows() -> list[dict]:
    rows: list[dict] = []
    for idx, topic in enumerate(ALL_TOPICS, start=1):
        category = infer_category(topic)
        rows.append(
            {
                "Day": idx,
                "Series": "Career Advancement Mastery",
                "Phase": "Growth Sprint",
                "Category": category,
                "Topic": topic,
                "Primary Goal": "Save/Share",
                "Hook": "A practical tip that helps professionals grow faster.",
                "Story / Problem": "Common career blockers and what to do next.",
                "Teaching Points": "Actionable step, example, and takeaway.",
                "Enterprise / FDE Angle": "Focus on measurable business impact and communication.",
                "Suggested Visual": "Career framework card",
                "Code Demo": "",
                "Real-world Example": "Short workplace scenario with outcome.",
                "Opinion": "Career growth is a system, not luck.",
                "CTA": "What is one action you will take this week?",
                "Recommended Format": "Text + bullet points",
                "Difficulty": "Beginner" if idx % 3 == 0 else "Intermediate",
                "Audience": "Early and mid career professionals",
                "Keywords": "career advancement, promotion, interview prep, devops, ai",
                "Hashtags": HASHTAGS,
                "Estimated Read Time": "~1 minute",
                "AI Studio Prompt": (
                    "Write around 150 words (acceptable range: 130-170). "
                    "Keep language clear and practical. Include 4-6 relevant hashtags, "
                    "mixing company/job portal tags and skill tags."
                ),
                "Status": "planned",
            }
        )
    return rows


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = build_rows()
    df = pd.DataFrame(rows)

    config_df = pd.DataFrame(
        [
            ["Word Count", "Target ~150 words per post; keep concise and practical."],
            [
                "Hashtags",
                "Use 4-6 hashtags including company tags and job portals when relevant: #Microsoft #Google #Amazon #LinkedIn #Indeed #Naukri #Glassdoor #Wellfound",
            ],
            ["Tone", "Actionable, professional, no fluff, include one discussion question."],
        ],
        columns=["Setting", "Value"],
    )

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Campaign", index=False)
        config_df.to_excel(writer, sheet_name="AI_Studio_Config", index=False)

    print(f"Workbook created: {OUTPUT_PATH}")
    print(f"Total topics: {len(df)}")


if __name__ == "__main__":
    main()
