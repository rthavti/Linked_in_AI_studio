"""
Excel Ingestion Workflow

Reads an Excel file and imports topics into the database.
"""

from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.logger import logger
from app.models.topic import Category
from app.models.topic import Priority
from app.repositories.topic_repository import TopicRepository
from app.schemas.ingest import (
    IngestError,
    IngestRow,
    IngestSummary,
)


class IngestWorkflow:

    REQUIRED_COLUMNS = [
        "Topic",
        "Category",
        "Priority",
    ]

    def __init__(self, db: Session):

        self.db = db
        self.repository = TopicRepository(db)

    def execute(
        self,
        excel_file: str | Path,
    ) -> tuple[IngestSummary, list[IngestRow]]:

        excel_file = Path(excel_file)

        if not excel_file.exists():
            raise FileNotFoundError(excel_file)

        logger.info(
            "Reading Excel file: %s",
            excel_file,
        )

        dataframe = pd.read_excel(excel_file)

        self.validate_columns(dataframe)

        summary = IngestSummary()
        rows: list[IngestRow] = []

        for row_number, row in dataframe.iterrows():

            row_topic = ""
            row_category = ""
            row_priority = ""
            status = "Imported"
            error_message: str | None = None

            try:

                topic = self.clean_string(
                    row["Topic"],
                )

                category = self.clean_string(
                    row["Category"],
                )

                priority = self.clean_string(
                    row["Priority"],
                )

                row_topic = topic
                row_category = category
                row_priority = priority

                if not topic:
                    raise ValueError("Topic cannot be empty.")

                if not category:
                    raise ValueError("Category cannot be empty.")

                if not priority:
                    raise ValueError("Priority cannot be empty.")

                if self.repository.get_by_topic(topic):
                    summary.duplicates += 1
                    status = "Duplicate"
                    rows.append(
                        IngestRow(
                            row=row_number + 2,
                            topic=topic,
                            category=category,
                            priority=priority,
                            status=status,
                            error_message=None,
                        )
                    )
                    continue

                category_enum = Category(category.upper())
                priority_enum = Priority(priority.upper())

                self.repository.create(
                    topic_text=topic,
                    category=category_enum,
                    priority=priority_enum,
                )

                summary.imported += 1

            except Exception as ex:
                status = "Failed"
                error_message = str(ex)
                summary.failed += 1

                summary.errors.append(
                    IngestError(
                        row=row_number + 2,
                        message=error_message,
                    )
                )

                logger.exception(
                    "Failed importing row %s",
                    row_number + 2,
                )

            rows.append(
                IngestRow(
                    row=row_number + 2,
                    topic=row_topic,
                    category=row_category,
                    priority=row_priority,
                    status=status,
                    error_message=error_message,
                )
            )

        try:

            self.repository.commit()

        except Exception:

            self.repository.rollback()
            raise

        logger.info(
            "Import complete. Imported=%s Duplicates=%s Failed=%s",
            summary.imported,
            summary.duplicates,
            summary.failed,
        )

        return summary, rows

    @staticmethod
    def validate_columns(dataframe):

        missing = []

        for column in IngestWorkflow.REQUIRED_COLUMNS:

            if column not in dataframe.columns:
                missing.append(column)

        if missing:

            raise ValueError(
                f"Missing required columns: {', '.join(missing)}"
            )

    @staticmethod
    def clean_string(value) -> str:

        if pd.isna(value):
            return ""

        return str(value).strip()