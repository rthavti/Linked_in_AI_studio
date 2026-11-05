from pathlib import Path

import httpx

API_URL = "http://127.0.0.1:8001/campaigns/upload"
WORKBOOK = Path("data/campaign_career_advancement_100_topics.xlsx")


def main() -> None:
    if not WORKBOOK.exists():
        raise FileNotFoundError(f"Workbook not found: {WORKBOOK}")

    form_data = {
        "name": "Career Advancement Daily 100",
        "publish_time": "10:00",
        "timezone": "Asia/Kolkata",
        "description": "Daily career advancement tips across AI, DevOps, and general career growth.",
        "auto_approve": "true",
        "auto_publish": "true",
        "auto_generate_images": "true",
        "image_count": "1",
        "visual_style": "auto",
        "max_attempts": "3",
        "min_words": "130",
        "max_words": "160",
    }

    with WORKBOOK.open("rb") as fh:
        files = {
            "file": (
                WORKBOOK.name,
                fh,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }
        with httpx.Client(timeout=120.0) as client:
            response = client.post(API_URL, data=form_data, files=files)

    print("HTTP", response.status_code)
    print(response.text)


if __name__ == "__main__":
    main()
