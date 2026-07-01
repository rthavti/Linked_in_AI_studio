import httpx
import urllib.parse

from app.config.settings import settings


class LinkedInClient:
    AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    PROFILE_URL = "https://api.linkedin.com/v2/me"
    SHARE_URL = "https://api.linkedin.com/v2/ugcPosts"
    ASSET_REGISTER_URL = "https://api.linkedin.com/v2/assets?action=registerUpload"

    def __init__(self):
        self.client_id = settings.LINKEDIN_CLIENT_ID
        self.client_secret = settings.LINKEDIN_CLIENT_SECRET
        self.redirect_uri = settings.LINKEDIN_REDIRECT_URI
        self.scopes = settings.LINKEDIN_SCOPES or "w_member_social r_liteprofile"

    def _validate_oauth_config(self) -> None:
        if not self.client_id or not self.client_secret or not self.redirect_uri:
            raise ValueError("LinkedIn OAuth settings are not configured.")

    def get_authorize_url(self, state: str) -> str:
        self._validate_oauth_config()
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scopes,
            "state": state,
        }
        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> dict:
        self._validate_oauth_config()
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        resp = httpx.post(self.TOKEN_URL, data=data, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_profile(self, access_token: str) -> dict:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        resp = httpx.get(self.PROFILE_URL, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def refresh_access_token(self, refresh_token: str) -> dict:
        self._validate_oauth_config()
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        resp = httpx.post(self.TOKEN_URL, data=data, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def register_image_upload(self, access_token: str, author_urn: str, mime_type: str) -> dict:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        body = {
            "registerUploadRequest": {
                "owner": author_urn,
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent",
                    }
                ],
                "supportedUploadMechanism": [
                    "SYNCHRONOUS_UPLOAD",
                ],
            }
        }
        resp = httpx.post(self.ASSET_REGISTER_URL, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        value = data.get("value", {})
        asset = value.get("asset")
        upload_mechanism = value.get("uploadMechanism", {})
        media_request = upload_mechanism.get(
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {}
        )
        upload_url = media_request.get("uploadUrl")

        if not asset or not upload_url:
            raise ValueError("LinkedIn asset registration failed.")

        return {"asset_urn": asset, "upload_url": upload_url}

    def upload_image(self, upload_url: str, image_bytes: bytes, mime_type: str) -> dict:
        headers = {
            "Content-Type": mime_type,
        }
        resp = httpx.put(upload_url, content=image_bytes, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.json() if resp.text else {"status": resp.status_code}

    def publish_post(
        self,
        access_token: str,
        author_urn: str,
        text: str,
        visibility: str = "PUBLIC",
        asset_urn: str | None = None,
    ) -> dict:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        content = {
            "shareCommentary": {"text": text},
        }
        body = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
        }

        if asset_urn:
            body["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
            body["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {
                    "status": "READY",
                    "description": {"text": text},
                    "media": asset_urn,
                    "title": {"text": "Image"},
                }
            ]

        resp = httpx.post(self.SHARE_URL, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
