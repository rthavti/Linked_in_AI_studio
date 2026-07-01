from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.linkedin_account import LinkedInAccount


class LinkedInAccountRepository:

    def __init__(self, db: Session):
        self._db = db

    def get_by_id(self, account_id: int) -> LinkedInAccount | None:
        return (
            self._db.query(LinkedInAccount)
            .filter(LinkedInAccount.id == account_id)
            .first()
        )

    def get_all(self) -> list[LinkedInAccount]:
        return (
            self._db.query(LinkedInAccount)
            .filter(LinkedInAccount.disconnected_at.is_(None))
            .order_by(LinkedInAccount.created_at.desc())
            .all()
        )

    def create_or_update(
        self,
        provider_user_id: str,
        access_token: str,
        refresh_token: str | None = None,
        expires_at=None,
    ) -> LinkedInAccount:
        account = (
            self._db.query(LinkedInAccount)
            .filter(LinkedInAccount.provider_user_id == provider_user_id)
            .first()
        )
        if account is None:
            account = LinkedInAccount(
                provider_user_id=provider_user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )
            self._db.add(account)
        else:
            account.access_token = access_token
            account.refresh_token = refresh_token
            account.expires_at = expires_at
            account.disconnected_at = None

        self._db.commit()
        self._db.refresh(account)
        return account

    def update(self, account: LinkedInAccount) -> LinkedInAccount:
        self._db.commit()
        self._db.refresh(account)
        return account

    def delete(self, account_id: int) -> bool:
        account = self.get_by_id(account_id)
        if account is None:
            return False
        self._db.delete(account)
        self._db.commit()
        return True

    def disconnect(self, account_id: int) -> bool:
        account = self.get_by_id(account_id)
        if account is None:
            return False
        account.disconnected_at = datetime.utcnow()
        self._db.commit()
        return True

    def get_latest(self) -> LinkedInAccount | None:
        return (
            self._db.query(LinkedInAccount)
            .filter(LinkedInAccount.disconnected_at.is_(None))
            .order_by(LinkedInAccount.created_at.desc())
            .first()
        )
