"""Async API Client for HelloFresh."""

from __future__ import annotations

import json
import re
import types
import uuid
from typing import Any, Self
from urllib.parse import parse_qs, urlparse

import aiohttp

from .const import (
    DEFAULT_BASE_URL,
    DEFAULT_BRAND,
    DEFAULT_COUNTRY,
    DEFAULT_GUEST_TOKEN,
    DEFAULT_LOCALE,
    USER_AGENT,
)
from .errors import (
    HelloFreshAuthenticationError,
    HelloFreshConnectionError,
    HelloFreshError,
    HelloFreshResponseError,
)
from .models import (
    AccountBalance,
    CartPrice,
    PastDeliveries,
    Profile,
    Recipe,
    TokenResponse,
    WeeklyMenu,
)

__all__ = ["HelloFreshClient"]


class HelloFreshClient:
    """Async Client for accessing HelloFresh APIs.

    Supports dependency injection of an external aiohttp.ClientSession in compliance
    with Home Assistant's inject-websession quality rule.
    """

    def __init__(
        self,
        *,
        session: aiohttp.ClientSession | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        guest_token: str | None = DEFAULT_GUEST_TOKEN,
        country: str = DEFAULT_COUNTRY,
        locale: str = DEFAULT_LOCALE,
        base_url: str = DEFAULT_BASE_URL,
        request_timeout: float = 10.0,
    ) -> None:
        """Initialize the HelloFresh Client.

        Args:
            session: Optional externally managed aiohttp.ClientSession.
            access_token: Optional OAuth Bearer access token.
            refresh_token: Optional OAuth refresh token.
            guest_token: Optional guest token for unauthenticated gateway endpoints.
            country: ISO country code (default "GB").
            locale: Language locale identifier (default "en-GB").
            base_url: Base URL for HelloFresh gateway (default "https://www.hellofresh.co.uk").
            request_timeout: Timeout in seconds for HTTP requests (default 10.0).
        """
        self._session = session
        self._owns_session = session is None
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._guest_token = guest_token
        self._country = country
        self._locale = locale
        self._base_url = base_url.rstrip("/")
        self._request_timeout = request_timeout

    @classmethod
    async def with_session(
        cls,
        *,
        access_token: str | None = None,
        refresh_token: str | None = None,
        guest_token: str | None = DEFAULT_GUEST_TOKEN,
        country: str = DEFAULT_COUNTRY,
        locale: str = DEFAULT_LOCALE,
        base_url: str = DEFAULT_BASE_URL,
        request_timeout: float = 10.0,
    ) -> Self:
        """Create a client instance with an internally managed aiohttp ClientSession.

        Args:
            access_token: Optional OAuth Bearer access token.
            refresh_token: Optional OAuth refresh token.
            guest_token: Optional guest token for unauthenticated gateway endpoints.
            country: ISO country code.
            locale: Language locale.
            base_url: Base gateway URL.
            request_timeout: Request timeout in seconds.

        Returns:
            HelloFreshClient initialized with an active session.
        """
        session = aiohttp.ClientSession()
        return cls(
            session=session,
            access_token=access_token,
            refresh_token=refresh_token,
            guest_token=guest_token,
            country=country,
            locale=locale,
            base_url=base_url,
            request_timeout=request_timeout,
        )

    async def __aenter__(self) -> Self:
        """Async context manager entry point."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Async context manager exit point."""
        await self.close()

    @property
    def access_token(self) -> str | None:
        """Get current access token."""
        return self._access_token

    @access_token.setter
    def access_token(self, value: str | None) -> None:
        """Set access token."""
        self._access_token = value

    @property
    def refresh_token(self) -> str | None:
        """Get current refresh token."""
        return self._refresh_token

    @refresh_token.setter
    def refresh_token(self, value: str | None) -> None:
        """Set refresh token."""
        self._refresh_token = value

    @property
    def country(self) -> str:
        """Get country code."""
        return self._country

    @property
    def locale(self) -> str:
        """Get locale identifier."""
        return self._locale

    @property
    def base_url(self) -> str:
        """Get base URL."""
        return self._base_url

    @property
    def request_timeout(self) -> float:
        """Get default request timeout in seconds."""
        return self._request_timeout

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def close(self) -> None:
        """Close the internally owned aiohttp session.

        Note: If the session was injected externally, it will NOT be closed.
        """
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    async def fetch_guest_token(self) -> str:
        """Dynamically fetch a fresh guest token from HelloFresh SSR HTML.

        Returns:
            The freshly extracted guest JWT access token.

        Raises:
            HelloFreshConnectionError: On network issue or timeout.
            HelloFreshAuthenticationError: If guest token cannot be parsed from SSR HTML.
        """
        session = await self._get_session()
        url = f"{self._base_url}/login"
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status >= 400:
                    text = await resp.text()
                    raise HelloFreshResponseError(resp.status, text)

                html = await resp.text()
                match = re.search(
                    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
                    html,
                )
                if match:
                    data = json.loads(match.group(1))
                    server_auth = (
                        data.get("props", {})
                        .get("pageProps", {})
                        .get("ssrPayload", {})
                        .get("serverAuth", {})
                    )
                    guest_token = server_auth.get("access_token")
                    if guest_token and isinstance(guest_token, str):
                        self._guest_token = guest_token
                        return guest_token

                raise HelloFreshAuthenticationError(
                    "Unable to parse guest token from HelloFresh SSR HTML payload."
                )
        except TimeoutError as err:
            raise HelloFreshConnectionError("Request timed out") from err
        except aiohttp.ClientError as err:
            raise HelloFreshConnectionError(f"Connection error: {err}") from err

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | list[Any] | None = None,
        auth_required: bool = True,
        timeout: float | None = None,
    ) -> Any:
        if auth_required and not self._access_token:
            raise HelloFreshAuthenticationError(
                "Access token is required for this operation."
            )

        session = await self._get_session()
        url = f"{self._base_url}{path}"
        req_timeout = aiohttp.ClientTimeout(
            total=timeout if timeout is not None else self._request_timeout
        )

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }

        # Use access_token if present; otherwise use guest_token
        token_to_use = self._access_token or self._guest_token
        if not token_to_use and not auth_required:
            try:
                token_to_use = await self.fetch_guest_token()
            except HelloFreshError:
                token_to_use = DEFAULT_GUEST_TOKEN
                self._guest_token = DEFAULT_GUEST_TOKEN

        if token_to_use:
            headers["Authorization"] = f"Bearer {token_to_use}"

        try:
            async with session.request(
                method,
                url,
                params=params,
                json=json_data,
                headers=headers,
                timeout=req_timeout,
            ) as resp:
                # If unauthenticated call failed with 401 and using guest token, retry once
                if resp.status == 401 and not auth_required and not self._access_token:
                    try:
                        fresh_guest_token = await self.fetch_guest_token()
                        headers["Authorization"] = f"Bearer {fresh_guest_token}"
                        async with session.request(
                            method,
                            url,
                            params=params,
                            json=json_data,
                            headers=headers,
                            timeout=req_timeout,
                        ) as retry_resp:
                            if retry_resp.status == 204:
                                return None
                            if retry_resp.status >= 400:
                                retry_text = await retry_resp.text()
                                if retry_resp.status in (401, 403):
                                    raise HelloFreshAuthenticationError(
                                        f"Authentication failed with status {retry_resp.status}"
                                    )
                                raise HelloFreshResponseError(
                                    retry_resp.status, retry_text
                                )
                            content_type = retry_resp.headers.get("Content-Type", "")
                            if "application/json" in content_type:
                                return await retry_resp.json()
                            return await retry_resp.text()
                    except HelloFreshError:
                        pass

                if resp.status in (401, 403):
                    text = await resp.text()

                    # If authenticated call failed with 401/403 and we have refresh_token, try refreshing once
                    if auth_required and self._refresh_token:
                        try:
                            await self.refresh_access_token()
                            headers["Authorization"] = f"Bearer {self._access_token}"
                            async with session.request(
                                method,
                                url,
                                params=params,
                                json=json_data,
                                headers=headers,
                                timeout=req_timeout,
                            ) as retry_resp:
                                if retry_resp.status == 204:
                                    return None
                                if retry_resp.status in (401, 403):
                                    retry_text = await retry_resp.text()
                                    msg = f"Authentication failed with status {retry_resp.status}: {retry_text}"
                                    raise HelloFreshAuthenticationError(
                                        msg, status_code=retry_resp.status
                                    )
                                if retry_resp.status >= 400:
                                    retry_text = await retry_resp.text()
                                    raise HelloFreshResponseError(
                                        retry_resp.status, retry_text
                                    )
                                content_type = retry_resp.headers.get(
                                    "Content-Type", ""
                                )
                                if "application/json" in content_type:
                                    return await retry_resp.json()
                                return await retry_resp.text()
                        except HelloFreshAuthenticationError:
                            raise
                        except HelloFreshError:
                            pass

                    raise HelloFreshAuthenticationError(
                        f"Authentication failed with status {resp.status}: {text}",
                        status_code=resp.status,
                    )
                if resp.status >= 400:
                    text = await resp.text()
                    try:
                        err_json = json.loads(text)
                        if isinstance(err_json, dict):
                            err_code = str(
                                err_json.get("error")
                                or err_json.get("error_code")
                                or ""
                            )
                            err_desc = str(
                                err_json.get("error_description")
                                or err_json.get("message")
                                or text
                            )
                            auth_keywords = (
                                "invalid_grant",
                                "invalid_token",
                                "unauthorized",
                                "invalid_code",
                                "expired_token",
                            )
                            if (
                                err_code.lower() in auth_keywords
                                or "refresh token" in err_desc.lower()
                                or "invalid token" in err_desc.lower()
                            ):
                                raise HelloFreshAuthenticationError(
                                    f"Authentication failed [{err_code or 'auth_error'}]: {err_desc}",
                                    status_code=resp.status,
                                    error_code=err_code or None,
                                )
                    except (json.JSONDecodeError, TypeError, ValueError):
                        pass

                    raise HelloFreshResponseError(resp.status, text)

                if resp.status == 204:
                    return None

                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return await resp.json()
                text = await resp.text()
                try:
                    return json.loads(text)
                except (json.JSONDecodeError, TypeError, ValueError):
                    return text
        except TimeoutError as err:
            raise HelloFreshConnectionError("Request timed out") from err
        except aiohttp.ClientError as err:
            raise HelloFreshConnectionError(f"Connection error: {err}") from err

    # --- AUTHENTICATION FLOWS ---

    async def start_passwordless_login(
        self, email: str, redirect_url: str | None = None
    ) -> str:
        """Start passwordless magic link login flow.

        Args:
            email: User email address.
            redirect_url: Optional custom redirect URL.

        Returns:
            The generated public_id UUID string.

        Raises:
            HelloFreshConnectionError: On network issue or timeout.
            HelloFreshResponseError: On unexpected status code.
        """
        public_id = str(uuid.uuid4())
        path = "/gw/v1/passwordless/start"
        params = {
            "country": self._country,
            "locale": self._locale,
        }
        payload = {
            "email": email,
            "channel": "email",
            "send": "link",
            "redirect_url": redirect_url
            or f"{self._base_url}/my-account/deliveries/menu",
            "public_id": public_id,
        }
        await self._request(
            "POST", path, params=params, json_data=payload, auth_required=False
        )
        return public_id

    async def finish_passwordless_login_from_url(
        self,
        url: str,
        public_id: str | None = None,
    ) -> TokenResponse:
        """Complete passwordless magic link login using a magic link URL or tracking link.

        Resolves tracking redirects (e.g. click.link.hellofresh.co.uk), extracts
        the code, email, public_id, and redirect_url query parameters, and exchanges
        them for OAuth tokens.

        Args:
            url: The full magic link URL received in email.
            public_id: Optional fallback public_id if missing from URL query parameters.

        Returns:
            TokenResponse containing access_token and refresh_token.

        Raises:
            HelloFreshAuthenticationError: If required parameters cannot be extracted.
            HelloFreshConnectionError: On network or redirection failure.
        """
        parsed = urlparse(url)
        query = parse_qs(parsed.query)

        code_list = query.get("code")
        email_list = query.get("email")
        pub_id_list = query.get("public_id")
        redirect_list = query.get("redirect_url")

        code = code_list[0] if code_list else None
        email = email_list[0] if email_list else None
        resolved_pub_id = pub_id_list[0] if pub_id_list else public_id
        redirect_url = redirect_list[0] if redirect_list else None

        # If missing parameters and it's a tracking URL, resolve redirect using Location header
        if (not code or not email or not resolved_pub_id) and url.startswith(
            ("http://", "https://")
        ):
            session = await self._get_session()
            headers = {"User-Agent": USER_AGENT}
            try:
                async with session.get(
                    url, headers=headers, allow_redirects=False
                ) as resp:
                    if (
                        resp.status in (301, 302, 303, 307, 308)
                        and "Location" in resp.headers
                    ):
                        final_url_str = resp.headers["Location"]
                    else:
                        final_url_str = str(resp.url)

                    parsed = urlparse(final_url_str)
                    query = parse_qs(parsed.query)
                    code = (query.get("code") or [None])[0]
                    email = (query.get("email") or [None])[0]
                    resolved_pub_id = (query.get("public_id") or [resolved_pub_id])[0]
                    redirect_url = (query.get("redirect_url") or [redirect_url])[0]
            except aiohttp.ClientError as err:
                raise HelloFreshConnectionError(
                    f"Failed to resolve magic link URL redirects: {err}"
                ) from err

        if not code or not email or not resolved_pub_id:
            raise HelloFreshAuthenticationError(
                "Invalid magic link URL. Missing required query parameters "
                f"(code, email, or public_id) in URL: {url}"
            )

        return await self.finish_passwordless_login(
            code=code,
            email=email,
            public_id=resolved_pub_id,
            redirect_url=redirect_url,
        )

    async def finish_passwordless_login(
        self,
        code: str,
        email: str,
        public_id: str,
        redirect_url: str | None = None,
    ) -> TokenResponse:
        """Complete passwordless magic link login using the code from the magic link.

        Args:
            code: The magic link token code.
            email: User email address.
            public_id: The public_id returned by start_passwordless_login.
            redirect_url: Optional custom redirect URL.

        Returns:
            TokenResponse object containing access_token and refresh_token.

        Raises:
            HelloFreshConnectionError: On network issue or timeout.
            HelloFreshResponseError: On unexpected status code.
        """
        path = "/gw/v1/passwordless/magic-link/finish"
        params = {
            "channel": "email",
            "code": code,
            "country": self._country.lower(),
            "email": email,
            "public_id": public_id,
            "redirect_url": redirect_url
            or f"{self._base_url}/my-account/deliveries/menu",
        }
        data = await self._request("GET", path, params=params, auth_required=False)
        token_resp = TokenResponse.from_dict(data)
        if token_resp.access_token:
            self._access_token = token_resp.access_token
        if token_resp.refresh_token:
            self._refresh_token = token_resp.refresh_token
        return token_resp

    async def refresh_access_token(
        self, refresh_token: str | None = None
    ) -> TokenResponse:
        """Refresh the access token using a refresh token.

        Args:
            refresh_token: Optional refresh token. Uses stored refresh_token if omitted.

        Returns:
            TokenResponse containing updated access_token and refresh_token.

        Raises:
            HelloFreshAuthenticationError: If no refresh token is available.
            HelloFreshConnectionError: On network issue or timeout.
            HelloFreshResponseError: On unexpected status code.
        """
        token_to_use = refresh_token or self._refresh_token
        if not token_to_use:
            raise HelloFreshAuthenticationError("No refresh token available.")

        path = "/gw/refresh"
        params = {
            "country": self._country,
            "locale": self._locale,
        }
        payload = {
            "refresh_token": token_to_use,
        }
        data = await self._request(
            "POST", path, params=params, json_data=payload, auth_required=False
        )
        token_resp = TokenResponse.from_dict(data)
        if token_resp.access_token:
            self._access_token = token_resp.access_token
        if token_resp.refresh_token:
            self._refresh_token = token_resp.refresh_token
        return token_resp

    # --- DATA ENDPOINTS ---

    async def get_profile(self) -> Profile:
        """Fetch the current customer profile.

        Returns:
            Profile object containing household and dietary preferences.

        Raises:
            HelloFreshAuthenticationError: If not authenticated or token invalid.
            HelloFreshConnectionError: On network issue or timeout.
            HelloFreshResponseError: On unexpected status code.
        """
        path = "/gw/profile-service/v2/customers/me/profile"
        params = {
            "brand": DEFAULT_BRAND,
            "regionCode": self._country,
        }
        data = await self._request("GET", path, params=params)
        return Profile.from_dict(data)

    async def get_customer_info(self) -> dict[str, Any]:
        """Fetch basic customer info including UUID, active subscription ID, and plan IDs.

        Returns:
            Dictionary containing customer info.

        Raises:
            HelloFreshAuthenticationError: If access_token is missing or expired.
            HelloFreshConnectionError: On network issue or timeout.
        """
        path = "/gw/api/customers/me/info"
        params = {
            "country": self._country,
            "locale": self._locale,
        }
        return await self._request("GET", path, params=params, auth_required=True)

    async def get_subscriptions(self) -> list[dict[str, Any]]:
        """Fetch customer active subscriptions.

        Returns:
            List of subscription dictionaries.

        Raises:
            HelloFreshAuthenticationError: If access_token is missing or expired.
            HelloFreshConnectionError: On network issue or timeout.
        """
        path = "/gw/api/customers/me/subscriptions"
        params = {"country": self._country}
        data = await self._request("GET", path, params=params, auth_required=True)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "items" in data:
            return data["items"]
        return []

    async def get_balance(self, customer_id: str | None = None) -> AccountBalance:
        """Fetch account balance.

        Args:
            customer_id: Optional customer UUID string. If None, fetches customer info UUID.

        Returns:
            AccountBalance object.

        Raises:
            HelloFreshAuthenticationError: If access_token is missing or expired.
            HelloFreshConnectionError: On network issue or timeout.
        """
        if not customer_id or customer_id == "me":
            info = await self.get_customer_info()
            customer_id = info.get("uuid") or info.get("id")

        path = f"/gw/payments/customers/{customer_id}/balance"
        params = {
            "business_unit": self._country,
            "country": self._country,
        }
        data = await self._request("GET", path, params=params, auth_required=True)
        return AccountBalance.from_dict(data)

    async def get_past_deliveries(
        self,
        range_start: str | None = None,
        range_end: str | None = None,
    ) -> PastDeliveries:
        """Fetch customer deliveries schedule.

        Args:
            range_start: Optional ISO week string start (e.g. '2026-W30').
            range_end: Optional ISO week string end (e.g. '2026-W40').

        Returns:
            PastDeliveries model containing past delivery items.

        Raises:
            HelloFreshAuthenticationError: If access_token is missing or expired.
            HelloFreshConnectionError: On network issue or timeout.
        """
        path = "/gw/api/customers/me/deliveries"
        params = {
            "country": self._country,
            "locale": self._locale,
        }
        if range_start:
            params["rangeStart"] = range_start
        if range_end:
            params["rangeEnd"] = range_end

        data = await self._request("GET", path, params=params, auth_required=True)
        return PastDeliveries.from_dict(data)

    async def get_menu(
        self,
        week: str,
        subscription_id: str | int | None = None,
        product_sku: str | None = None,
    ) -> WeeklyMenu:
        """Fetch weekly menu recipes.

        Args:
            week: Target delivery week identifier (e.g. '2026-W32').
            subscription_id: Optional customer subscription ID.
            product_sku: Optional product SKU (default auto-retrieved from customer info).

        Returns:
            WeeklyMenu model.

        Raises:
            HelloFreshAuthenticationError: If access_token is missing or expired.
            HelloFreshConnectionError: On network issue or timeout.
        """
        if not subscription_id or not product_sku:
            try:
                info = await self.get_customer_info()
                if not subscription_id:
                    subscription_id = info.get("activeSubscriptionId")
                if not product_sku:
                    product_sku = info.get("activeSubscriptionSkus")
            except HelloFreshError:
                pass

        path = "/gw/my-deliveries/menu"
        params: dict[str, Any] = {
            "week": week,
            "country": self._country.lower(),
            "locale": self._locale,
        }
        if product_sku:
            params["product-sku"] = str(product_sku)
        if subscription_id:
            params["subscription"] = str(subscription_id)

        data = await self._request("GET", path, params=params, auth_required=True)
        return WeeklyMenu.from_dict(data)

    async def get_recipe(self, recipe_id: str) -> Recipe:
        """Fetch details for a specific recipe.

        Args:
            recipe_id: Recipe identifier string.

        Returns:
            Recipe model object.

        Raises:
            HelloFreshAuthenticationError: If access_token is missing or expired.
            HelloFreshConnectionError: On network issue or timeout.
        """
        path = f"/gw/recipes/recipes/{recipe_id}"
        params = {
            "country": self._country,
            "locale": self._locale,
        }
        data = await self._request("GET", path, params=params, auth_required=True)
        return Recipe.from_dict(data)

    async def get_cart_price(
        self,
        week: str,
        box_size: int = 2,
        subscription_id: str | int | None = None,
        product_sku: str | None = None,
        products: list[dict[str, Any]] | None = None,
    ) -> CartPrice:
        """Calculate cart price for a specific week.

        Args:
            week: Target delivery week identifier (e.g. '2026-W32').
            box_size: Number of meals / box size (default 2).
            subscription_id: Optional subscription ID.
            product_sku: Optional product SKU string.
            products: Optional list of product dictionaries.

        Returns:
            CartPrice model.

        Raises:
            HelloFreshAuthenticationError: If access_token is missing or expired.
            HelloFreshConnectionError: On network issue or timeout.
        """
        if not subscription_id or not product_sku:
            try:
                info = await self.get_customer_info()
                if not subscription_id:
                    subscription_id = info.get("activeSubscriptionId")
                if not product_sku:
                    product_sku = info.get("activeSubscriptionSkus")
            except HelloFreshError:
                pass

        if not products:
            sku_handle = product_sku or "GB-CBU-2-2-0"
            products = [
                {
                    "handle": sku_handle,
                    "hfWeek": week,
                }
            ]

        path = f"/gw/v1/carts/{week}/price"
        payload: dict[str, Any] = {
            "country": self._country,
            "locale": self._locale,
            "boxSize": box_size,
            "isRecurring": True,
            "products": products,
        }
        if subscription_id:
            payload["subscriptionID"] = subscription_id

        data = await self._request("POST", path, json_data=payload, auth_required=True)
        return CartPrice.from_dict(data)
