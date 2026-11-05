import httpx
import re
import urllib.parse
import xml.etree.ElementTree as ET

from app.config.settings import settings


class LinkedInClient:
    AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
    PROFILE_URL = "https://api.linkedin.com/v2/me"
    SHARE_URL = "https://api.linkedin.com/v2/ugcPosts"
    ASSET_REGISTER_URL = "https://api.linkedin.com/v2/assets?action=registerUpload"
    SOCIAL_ACTIONS_URL = "https://api.linkedin.com/v2/socialActions"
    SEARCH_URL = "https://api.linkedin.com/v2/search"
    REST_POSTS_URL = "https://api.linkedin.com/rest/posts"
    BING_RSS_URL = "https://www.bing.com/search"
    DDG_HTML_URL = "https://r.jina.ai/http://html.duckduckgo.com/html/"

    def __init__(self):
        self.client_id = settings.LINKEDIN_CLIENT_ID
        self.client_secret = settings.LINKEDIN_CLIENT_SECRET
        self.redirect_uri = settings.LINKEDIN_REDIRECT_URI
        self.scopes = settings.LINKEDIN_SCOPES or "w_member_social openid profile"

    def _validate_oauth_config(self) -> None:
        missing = []
        if not self.client_id:
            missing.append("LINKEDIN_CLIENT_ID")
        if not self.client_secret:
            missing.append("LINKEDIN_CLIENT_SECRET")
        if not self.redirect_uri:
            missing.append("LINKEDIN_REDIRECT_URI")

        if missing:
            raise ValueError(
                "LinkedIn OAuth settings are not configured. Missing: " + ", ".join(missing)
            )

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
        oauth_headers = {
            "Authorization": f"Bearer {access_token}",
        }
        userinfo_resp = httpx.get(self.USERINFO_URL, headers=oauth_headers, timeout=30)
        if userinfo_resp.status_code < 400:
            return userinfo_resp.json()

        # Fall back to legacy profile API for older scope combinations.
        legacy_headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        resp = httpx.get(self.PROFILE_URL, headers=legacy_headers, timeout=30)
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
        asset_urns: list[str] | None = None,
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

        clean_asset_urns = [urn for urn in (asset_urns or []) if urn]
        if clean_asset_urns:
            body["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
            body["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {
                    "status": "READY",
                    "description": {"text": text},
                    "media": urn,
                    "title": {"text": f"Image {idx + 1}"},
                }
                for idx, urn in enumerate(clean_asset_urns)
            ]

        resp = httpx.post(self.SHARE_URL, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def comment_on_post(
        self,
        access_token: str,
        post_urn: str,
        author_urn: str,
        comment_text: str,
    ) -> dict:
        encoded_urn = urllib.parse.quote(post_urn, safe="")
        url = f"{self.SOCIAL_ACTIONS_URL}/{encoded_urn}/comments"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        body = {
            "actor": author_urn,
            "message": {
                "text": comment_text,
            },
        }
        resp = httpx.post(url, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json() if resp.text else {"status": resp.status_code}

    def like_post(
        self,
        access_token: str,
        post_urn: str,
        author_urn: str,
    ) -> dict:
        encoded_urn = urllib.parse.quote(post_urn, safe="")
        url = f"{self.SOCIAL_ACTIONS_URL}/{encoded_urn}/likes"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        body = {
            "actor": author_urn,
        }
        resp = httpx.post(url, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json() if resp.text else {"status": resp.status_code}

    def is_post_accessible(self, access_token: str, post_urn: str) -> bool:
        encoded_urn = urllib.parse.quote(post_urn, safe="")
        url = f"{self.SOCIAL_ACTIONS_URL}/{encoded_urn}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        resp = httpx.get(url, headers=headers, timeout=30)
        if resp.status_code == 404:
            return False
        if resp.status_code >= 400:
            raise ValueError(f"LinkedIn accessibility check failed with {resp.status_code}.")
        return True

    def _parse_search_post_elements(self, payload: dict) -> list[dict]:
        rows: list[dict] = []
        elements = payload.get("elements") if isinstance(payload, dict) else None
        if not isinstance(elements, list):
            return rows

        for item in elements:
            if not isinstance(item, dict):
                continue

            post_url = item.get("url") or item.get("permalink") or item.get("postUrl")
            post_urn = item.get("id") or item.get("entityUrn") or item.get("urn")
            author = item.get("author") or item.get("owner") or item.get("createdBy") or ""
            content = item.get("commentary") or item.get("text") or item.get("postContent") or ""

            if isinstance(content, dict):
                content = content.get("text") or content.get("raw") or ""

            reactions = item.get("reactionCount") or item.get("numLikes") or 0
            language = item.get("contentLanguage") or item.get("language") or "en"

            if post_urn and not post_url:
                post_url = f"https://www.linkedin.com/feed/update/{post_urn}"

            if not post_url or not content:
                continue

            rows.append(
                {
                    "post_url": str(post_url),
                    "post_urn": str(post_urn) if post_urn else None,
                    "post_author": str(author) if author else "",
                    "post_content": str(content),
                    "post_language": str(language),
                    "post_reaction_count": int(reactions or 0),
                    "is_company_page": False,
                    "is_sponsored": False,
                    "is_recruiter": False,
                    "is_repost": False,
                }
            )

        return rows

    @staticmethod
    def _extract_urn_from_url(url: str) -> str | None:
        if not url:
            return None

        direct = urllib.parse.unquote(url)
        for pattern in [
            r"urn:li:(activity|share|ugcPost):[0-9]+",
            r"activity-([0-9]{10,})",
            r"/posts/.*?-([0-9]{10,})(?:-|/|$)",
        ]:
            match = re.search(pattern, direct)
            if not match:
                continue
            if pattern.startswith("urn:"):
                return match.group(0)
            return f"urn:li:activity:{match.group(1)}"
        return None

    @staticmethod
    def _extract_linkedin_urls_from_ddg_html(html: str, count: int) -> list[str]:
        if not html:
            return []

        candidates: list[str] = []

        # DuckDuckGo often wraps target URLs as uddg=<encoded_url>.
        for encoded in re.findall(r"uddg=([^&\"']+)", html):
            try:
                url = urllib.parse.unquote(encoded)
            except Exception:
                continue
            if "linkedin.com" not in url.lower():
                continue
            if "/feed/update/" not in url and "/posts/" not in url:
                continue
            candidates.append(url)
            if len(candidates) >= count:
                break

        # Fallback direct URL extraction.
        if len(candidates) < count:
            for url in re.findall(r"https?://[^\"'\s<>]+linkedin\.com[^\"'\s<>]+", html):
                parsed = urllib.parse.unquote(url)
                if "/feed/update/" not in parsed and "/posts/" not in parsed:
                    continue
                if parsed not in candidates:
                    candidates.append(parsed)
                if len(candidates) >= count:
                    break

        return candidates[:count]

    def _search_public_linkedin_posts_by_topic(self, topic: str, count: int) -> list[dict]:
        headers = {
            "User-Agent": "Mozilla/5.0",
        }

        rows: list[dict] = []
        seen_urls: set[str] = set()

        query_variants = [
            f'site:linkedin.com/posts {topic}',
            f'site:linkedin.com/posts "{topic}"',
            f'site:linkedin.com/feed/update {topic}',
            f'site:linkedin.com/feed/update "{topic}"',
        ]

        def add_link(link: str) -> None:
            if link in seen_urls:
                return
            seen_urls.add(link)
            rows.append(
                {
                    "post_url": link,
                    "post_urn": self._extract_urn_from_url(link),
                    "post_author": "",
                    "post_content": f"{topic} discussion",
                    "post_language": "en",
                    "post_reaction_count": 0,
                    "is_company_page": False,
                    "is_sponsored": False,
                    "is_recruiter": False,
                    "is_repost": False,
                }
            )

        for query in query_variants:
            ddg_resp = httpx.get(
                self.DDG_HTML_URL,
                params={"q": query},
                headers=headers,
                timeout=30,
                follow_redirects=True,
            )
            ddg_resp.raise_for_status()
            ddg_urls = self._extract_linkedin_urls_from_ddg_html(ddg_resp.text, count)
            for link in ddg_urls:
                add_link(link)
                if len(rows) >= count:
                    return rows[:count]

        # Secondary fallback: Bing RSS extraction.
        params = {
            "q": f'site:linkedin.com {topic}',
            "format": "rss",
        }
        resp = httpx.get(
            self.BING_RSS_URL,
            params=params,
            headers=headers,
            timeout=30,
            follow_redirects=True,
        )
        resp.raise_for_status()

        root = ET.fromstring(resp.text)
        for item in root.findall("./channel/item"):
            link = (item.findtext("link") or "").strip()
            title = (item.findtext("title") or "").strip()
            description = (item.findtext("description") or "").strip()
            if not link or "linkedin.com" not in link.lower():
                continue
            if "/feed/update/" not in link and "/posts/" not in link:
                continue

            post_content = " ".join([part for part in [title, description] if part]).strip() or f"{topic} discussion"
            if link not in seen_urls:
                seen_urls.add(link)
                rows.append(
                    {
                        "post_url": link,
                        "post_urn": self._extract_urn_from_url(link),
                        "post_author": "",
                        "post_content": post_content,
                        "post_language": "en",
                        "post_reaction_count": 0,
                        "is_company_page": False,
                        "is_sponsored": False,
                        "is_recruiter": False,
                        "is_repost": False,
                    }
                )
            if len(rows) >= count:
                break

        return rows[:count]

    def search_posts_by_topic(self, access_token: str, topic: str, count: int = 10) -> list[dict]:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        safe_count = max(1, min(int(count or 10), 50))
        params = {
            "q": "searchEntity",
            "keywords": topic,
            "count": safe_count,
            "start": 0,
        }

        resp = httpx.get(self.SEARCH_URL, headers=headers, params=params, timeout=30)
        if resp.status_code < 400:
            rows = self._parse_search_post_elements(resp.json())
            if rows:
                return rows[:safe_count]

        rest_headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Linkedin-Version": "202404",
        }
        rest_params = {
            "q": "search",
            "keywords": topic,
            "count": safe_count,
            "start": 0,
        }
        rest_resp = httpx.get(self.REST_POSTS_URL, headers=rest_headers, params=rest_params, timeout=30)
        if rest_resp.status_code < 400:
            rows = self._parse_search_post_elements(rest_resp.json())
            return rows[:safe_count]

        # Last-resort fallback when LinkedIn app-level search APIs are unavailable.
        try:
            public_rows = self._search_public_linkedin_posts_by_topic(topic, safe_count)
            if public_rows:
                return public_rows[:safe_count]
        except Exception:
            pass

        detail = "LinkedIn direct post search is not available for current app scopes or API product access."
        if resp.status_code >= 400:
            detail = f"LinkedIn search API error {resp.status_code}."
        if rest_resp.status_code >= 400:
            detail = f"{detail} REST posts search error {rest_resp.status_code}."
        raise ValueError(detail)
