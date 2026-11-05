from collections import Counter

from sqlalchemy import create_engine
from sqlalchemy import text

from app.config.settings import settings


def main() -> None:
    db_path = settings.DATABASE_URL.replace("sqlite:///", "", 1)
    engine = create_engine(f"sqlite:///{db_path}", future=True)

    with engine.connect() as conn:
        topic_status = conn.execute(
            text("SELECT status, COUNT(*) AS count FROM topics GROUP BY status ORDER BY count DESC")
        ).fetchall()

        item_status = conn.execute(
            text(
                "SELECT status, COUNT(*) AS count "
                "FROM learning_campaign_items "
                "GROUP BY status ORDER BY count DESC"
            )
        ).fetchall()

        failed_items = conn.execute(
            text(
                "SELECT campaign_id, day_number, status, attempts, last_error "
                "FROM learning_campaign_items "
                "WHERE status IN ('FAILED','RETRY') "
                "ORDER BY campaign_id, day_number"
            )
        ).fetchall()

        failed_topics = conn.execute(
            text(
                "SELECT id, topic, status, error_message, updated_at "
                "FROM topics WHERE status='FAILED' ORDER BY updated_at DESC"
            )
        ).fetchall()

    print("TOPIC_STATUS_COUNTS")
    for row in topic_status:
        print(dict(row._mapping))

    print("\nCAMPAIGN_ITEM_STATUS_COUNTS")
    for row in item_status:
        print(dict(row._mapping))

    print(f"\nFAILED_TOPICS_TOTAL: {len(failed_topics)}")
    print(f"FAILED_OR_RETRY_CAMPAIGN_ITEMS_TOTAL: {len(failed_items)}")

    error_counter = Counter((row._mapping["last_error"] or "").strip() for row in failed_items)
    print("\nTOP_FAILED_ITEM_ERRORS")
    for error, count in error_counter.most_common(10):
        print({"count": count, "error": error})

    print("\nFAILED_ITEM_SAMPLE")
    for row in failed_items[:20]:
        print(dict(row._mapping))


if __name__ == "__main__":
    main()
