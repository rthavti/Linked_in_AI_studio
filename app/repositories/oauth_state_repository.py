from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.oauth_state import OAuthState


class OAuthStateRepository:

    def __init__(self, db: Session):
        self._db = db

    def create(self, state: str, expires_at: datetime) -> OAuthState:
        oauth_state = OAuthState(
            state=state,
            expires_at=expires_at,
            used=False,
        )
        self._db.add(oauth_state)
        self._db.commit()
        self._db.refresh(oauth_state)
        return oauth_state

    def get_by_state(self, state: str) -> OAuthState | None:
        return (
            self._db.query(OAuthState)
            .filter(OAuthState.state == state)
            .first()
        )

    def mark_used(self, oauth_state: OAuthState) -> OAuthState:
        oauth_state.used = True
        self._db.commit()
        self._db.refresh(oauth_state)
        return oauth_state
