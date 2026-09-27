"""Unit tests for HelloFreshClient using unittest.mock."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from pyhellofresh import (
    DEFAULT_BASE_URL,
    HelloFreshAuthenticationError,
    HelloFreshClient,
    HelloFreshConnectionError,
    HelloFreshResponseError,
)
from tests.conftest import (
    SAMPLE_BALANCE_RESPONSE,
    SAMPLE_CART_PRICE_RESPONSE,
    SAMPLE_MENU_RESPONSE,
    SAMPLE_PAST_DELIVERIES_RESPONSE,
    SAMPLE_PROFILE_RESPONSE,
    SAMPLE_RECIPE_RESPONSE,
    SAMPLE_TOKEN_RESPONSE,
)


def create_mock_session(
    status: int = 200,
    json_data: dict | list | None = None,
    text: str | None = None,
    side_effect: Exception | type[Exception] | None = None,
    content_type: str = "application/json",
) -> MagicMock:
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.closed = False
    mock_session.close = AsyncMock()

    if side_effect:
        mock_session.request.side_effect = side_effect
    else:
        resp = MagicMock()
        resp.status = status
        resp.headers = {"Content-Type": content_type}
        if json_data is not None:
            resp.json = AsyncMock(return_value=json_data)
        else:
            resp.json = AsyncMock(side_effect=Exception("Invalid JSON"))
        if text is None and json_data is not None:
            resp.text = AsyncMock(return_value=json.dumps(json_data))
        else:
            resp.text = AsyncMock(return_value=text or "")

        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=resp)
        ctx.__aexit__ = AsyncMock(return_value=None)
        mock_session.request.return_value = ctx

    mock_session.get = mock_session.request
    return mock_session


def sequenced_session(payloads: list[dict]) -> MagicMock:
    """Session whose successive requests return each payload in order."""
    session = MagicMock(spec=aiohttp.ClientSession)
    session.closed = False
    session.close = AsyncMock()
    contexts = []
    for payload in payloads:
        resp = MagicMock()
        resp.status = 200
        resp.headers = {"Content-Type": "application/json"}
        resp.json = AsyncMock(return_value=payload)
        resp.text = AsyncMock(return_value=json.dumps(payload))
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=resp)
        ctx.__aexit__ = AsyncMock(return_value=None)
        contexts.append(ctx)
    session.request.side_effect = contexts
    session.get = session.request
    return session


@pytest.mark.anyio
async def test_client_init_properties():
    client = HelloFreshClient(
        access_token="test_access",
        refresh_token="test_refresh",
        country="GB",
        locale="en-GB",
        request_timeout=15.0,
    )
    assert client.access_token == "test_access"
    assert client.refresh_token == "test_refresh"
    assert client.country == "GB"
    assert client.locale == "en-GB"
    assert client.base_url == DEFAULT_BASE_URL
    assert client.request_timeout == 15.0

    client.access_token = "new_access"
    client.refresh_token = "new_refresh"
    assert client.access_token == "new_access"
    assert client.refresh_token == "new_refresh"
    await client.close()


@pytest.mark.anyio
async def test_inject_websession_does_not_close_external_session():
    """Verify compliance with Home Assistant's inject-websession quality rule.

    An externally injected ClientSession must NOT be closed when client.close() or
    context manager exits.
    """
    external_session = MagicMock(spec=aiohttp.ClientSession)
    external_session.closed = False
    external_session.close = AsyncMock()

    client = HelloFreshClient(session=external_session, access_token="tok")
    assert client._owns_session is False

    await client.close()
    external_session.close.assert_not_called()

    async with HelloFreshClient(session=external_session, access_token="tok"):
        pass
    external_session.close.assert_not_called()


@pytest.mark.anyio
async def test_async_context_manager():
    session = create_mock_session(status=200, json_data=SAMPLE_PROFILE_RESPONSE)
    async with HelloFreshClient(session=session, access_token="tok") as client:
        profile = await client.get_profile()
        assert profile.total_people == 2


@pytest.mark.anyio
async def test_close_auto_session():
    client = HelloFreshClient(access_token="tok")
    session = await client._get_session()
    assert client._owns_session is True
    await client.close()
    assert session.closed is True


@pytest.mark.anyio
async def test_client_factory():
    client = await HelloFreshClient.with_session(access_token="tok")
    assert client.access_token == "tok"
    await client.close()


@pytest.mark.anyio
async def test_auth_required_error():
    client = HelloFreshClient(access_token=None)
    with pytest.raises(HelloFreshAuthenticationError):
        await client.get_profile()
    await client.close()


@pytest.mark.anyio
async def test_start_passwordless_login():
    session = create_mock_session(status=204)
    client = HelloFreshClient(session=session)
    public_id = await client.start_passwordless_login(
        "user@example.com", redirect_url="https://www.hellofresh.co.uk/menu"
    )
    assert isinstance(public_id, str)
    assert len(public_id) > 0
    session.request.assert_called_once()


@pytest.mark.anyio
async def test_finish_passwordless_login_from_url():
    sample_url = (
        "https://www.hellofresh.co.uk/passwordless/login/finish?"
        "code=mock_code&email=user%40example.com&public_id=mock_pub_id"
    )
    session = create_mock_session(status=200, json_data=SAMPLE_TOKEN_RESPONSE)
    client = HelloFreshClient(session=session)

    token_resp = await client.finish_passwordless_login_from_url(sample_url)
    assert token_resp.access_token == SAMPLE_TOKEN_RESPONSE["access_token"]
    assert client.access_token == SAMPLE_TOKEN_RESPONSE["access_token"]


@pytest.mark.anyio
async def test_finish_passwordless_login_from_url_invalid_error():
    sample_invalid_url = (
        "https://www.hellofresh.co.uk/passwordless/login/finish?invalid=1"
    )
    session = create_mock_session()
    client = HelloFreshClient(session=session)

    with pytest.raises(HelloFreshAuthenticationError):
        await client.finish_passwordless_login_from_url(sample_invalid_url)


@pytest.mark.anyio
async def test_refresh_access_token():
    session = create_mock_session(status=200, json_data=SAMPLE_TOKEN_RESPONSE)
    client = HelloFreshClient(session=session, refresh_token="old_refresh")
    token_resp = await client.refresh_access_token()
    assert token_resp.access_token == SAMPLE_TOKEN_RESPONSE["access_token"]
    assert client.access_token == SAMPLE_TOKEN_RESPONSE["access_token"]


@pytest.mark.anyio
async def test_refresh_no_token_error():
    session = create_mock_session()
    client = HelloFreshClient(session=session, refresh_token=None)
    with pytest.raises(HelloFreshAuthenticationError):
        await client.refresh_access_token()


@pytest.mark.anyio
async def test_get_profile():
    session = create_mock_session(status=200, json_data=SAMPLE_PROFILE_RESPONSE)
    client = HelloFreshClient(session=session, access_token="token")
    profile = await client.get_profile()
    assert profile.total_people == 2
    assert profile.exclusions == ["pork", "shellfish"]


@pytest.mark.anyio
async def test_get_customer_info():
    session = create_mock_session(
        status=200,
        json_data={"id": "15961823", "uuid": "297d5bcb-f9ce-43f0-90b2-38e4b7827a59"},
    )
    client = HelloFreshClient(session=session, access_token="token")
    info = await client.get_customer_info()
    assert info["uuid"] == "297d5bcb-f9ce-43f0-90b2-38e4b7827a59"


@pytest.mark.anyio
async def test_get_subscriptions():
    session = create_mock_session(status=200, json_data=[{"id": 10323453}])
    client = HelloFreshClient(session=session, access_token="token")
    subs = await client.get_subscriptions()
    assert len(subs) == 1
    assert subs[0]["id"] == 10323453


@pytest.mark.anyio
async def test_get_balance():
    session = create_mock_session(status=200, json_data=SAMPLE_BALANCE_RESPONSE)
    client = HelloFreshClient(session=session, access_token="token")
    balance = await client.get_balance("297d5bcb-f9ce-43f0-90b2-38e4b7827a59")
    assert balance.amount == 800
    assert balance.currency_code == "GBP"


@pytest.mark.anyio
async def test_get_past_deliveries():
    session = create_mock_session(status=200, json_data=SAMPLE_PAST_DELIVERIES_RESPONSE)
    client = HelloFreshClient(session=session, access_token="token")
    past = await client.get_past_deliveries("2026-W30", "2026-W40")
    assert len(past.weeks) == 1
    assert past.next_week == "2026-W32"


@pytest.mark.anyio
async def test_get_menu():
    session = create_mock_session(status=200, json_data=SAMPLE_MENU_RESPONSE)
    client = HelloFreshClient(session=session, access_token="token")
    menu = await client.get_menu("2026-W32", subscription_id=10323453)
    assert menu.week == "2026-W32"
    assert len(menu.meals) == 1


_OFFSET_DELIVERIES = {
    "weeks": [
        {
            "week": "2026-W39",
            "cutoffDate": "2026-09-18T23:59:59+00:00",
            "status": "DELIVERED",
        },
        {
            "week": "2026-W40",
            "cutoffDate": "2026-09-25T23:59:59+00:00",
            "status": "RUNNING",
        },
        {
            "week": "2026-W41",
            "cutoffDate": "2026-10-02T23:59:59+00:00",
            "status": "RUNNING",
        },
    ]
}

_OFFSET_CUSTOMER = {
    "activeSubscriptionId": 10323453,
    "activeSubscriptionSkus": "GB-CBU-2-2-0",
}


def _offset_menu(week: str) -> dict:
    return {
        "id": "menu",
        "week": week,
        "meals": [
            {
                "index": 1,
                "selection": {"quantity": 1},
                "recipe": {"id": "chosen", "name": "In the box"},
            },
            {
                "index": 2,
                "selection": {"quantity": 0},
                "recipe": {"id": "available", "name": "Not selected"},
            },
        ],
    }


@pytest.mark.anyio
async def test_get_meals_for_week_offset_returns_selected_meals():
    session = sequenced_session(
        [_OFFSET_DELIVERIES, _OFFSET_CUSTOMER, _offset_menu("2026-W40")]
    )
    client = HelloFreshClient(session=session, access_token="token")
    fixed_now = datetime(2026, 9, 27, tzinfo=timezone.utc)
    with patch("pyhellofresh.client._utcnow", return_value=fixed_now):
        meals = await client.get_meals_for_week_offset(0)

    assert [meal.recipe.name for meal in meals if meal.recipe] == ["In the box"]
    menu_call = session.request.call_args_list[2]
    assert menu_call.kwargs["params"]["week"] == "2026-W40"


@pytest.mark.anyio
async def test_get_meals_for_week_offset_moves_forward_and_back():
    session = sequenced_session(
        [_OFFSET_DELIVERIES, _OFFSET_CUSTOMER, _offset_menu("2026-W41")]
    )
    client = HelloFreshClient(session=session, access_token="token")
    fixed_now = datetime(2026, 9, 27, tzinfo=timezone.utc)
    with patch("pyhellofresh.client._utcnow", return_value=fixed_now):
        await client.get_meals_for_week_offset(1)
    assert session.request.call_args_list[2].kwargs["params"]["week"] == "2026-W41"

    session = sequenced_session(
        [_OFFSET_DELIVERIES, _OFFSET_CUSTOMER, _offset_menu("2026-W39")]
    )
    client = HelloFreshClient(session=session, access_token="token")
    with patch("pyhellofresh.client._utcnow", return_value=fixed_now):
        await client.get_meals_for_week_offset(-1)
    assert session.request.call_args_list[2].kwargs["params"]["week"] == "2026-W39"


@pytest.mark.anyio
async def test_get_recipe():
    session = create_mock_session(status=200, json_data=SAMPLE_RECIPE_RESPONSE)
    client = HelloFreshClient(session=session, access_token="token")
    recipe = await client.get_recipe("6a2a93831f9f329b3991d936")
    assert recipe.id == "6a2a93831f9f329b3991d936"
    assert recipe.name == "Mexican Inspired Veggie Small Plates"


@pytest.mark.anyio
async def test_get_menu_auto_subscription():
    session = MagicMock()
    session.closed = False

    # 1st call for get_customer_info, 2nd call for get_menu
    ctx1 = MagicMock()
    ctx1.__aenter__ = AsyncMock(
        return_value=MagicMock(
            status=200,
            headers={"Content-Type": "application/json"},
            json=AsyncMock(
                return_value={
                    "activeSubscriptionId": 10323453,
                    "activeSubscriptionSkus": "GB-CBU-2-2-0",
                }
            ),
        )
    )
    ctx1.__aexit__ = AsyncMock(return_value=None)

    ctx2 = MagicMock()
    ctx2.__aenter__ = AsyncMock(
        return_value=MagicMock(
            status=200,
            headers={"Content-Type": "application/json"},
            json=AsyncMock(return_value=SAMPLE_MENU_RESPONSE),
        )
    )
    ctx2.__aexit__ = AsyncMock(return_value=None)

    session.request.side_effect = [ctx1, ctx2]
    client = HelloFreshClient(session=session, access_token="token")
    menu = await client.get_menu("2026-W32")
    assert menu.week == "2026-W32"


@pytest.mark.anyio
async def test_search_recipes():
    session = create_mock_session(
        status=200,
        json_data={
            "items": [SAMPLE_RECIPE_RESPONSE],
            "total": 1,
            "take": 20,
            "skip": 0,
        },
    )
    client = HelloFreshClient(session=session)
    recipes = await client.search_recipes("veggie", take=5)
    assert len(recipes) == 1
    assert recipes[0].id == "6a2a93831f9f329b3991d936"
    assert recipes[0].name == "Mexican Inspired Veggie Small Plates"
    session.request.assert_called_once()
    call_args = session.request.call_args
    assert call_args.args[0] == "GET"
    assert call_args.args[1] == f"{DEFAULT_BASE_URL}/gw/api/recipes/search"
    assert call_args.kwargs["params"]["q"] == "veggie"
    assert call_args.kwargs["params"]["take"] == 5


@pytest.mark.anyio
async def test_search_recipes_non_dict_response():
    session = create_mock_session(status=200, json_data=[])
    client = HelloFreshClient(session=session)
    recipes = await client.search_recipes("veggie")
    assert recipes == []


@pytest.mark.anyio
async def test_get_cart_price_auto_subscription():
    session = MagicMock()
    session.closed = False

    ctx1 = MagicMock()
    ctx1.__aenter__ = AsyncMock(
        return_value=MagicMock(
            status=200,
            headers={"Content-Type": "application/json"},
            json=AsyncMock(
                return_value={
                    "id": "15961823",
                    "activeSubscriptionId": 10323453,
                    "activeSubscriptionSkus": "GB-CBU-2-2-0",
                    "customerPlanIds": ["cc5bbc8f-f56d-4d0b-929c-984a3e071cdd"],
                }
            ),
        )
    )
    ctx1.__aexit__ = AsyncMock(return_value=None)

    ctx2 = MagicMock()
    ctx2.__aenter__ = AsyncMock(
        return_value=MagicMock(
            status=200,
            headers={"Content-Type": "application/json"},
            json=AsyncMock(return_value=SAMPLE_CART_PRICE_RESPONSE),
        )
    )
    ctx2.__aexit__ = AsyncMock(return_value=None)

    session.request.side_effect = [ctx1, ctx2]
    client = HelloFreshClient(session=session, access_token="token")
    cart = await client.get_cart_price("2026-W32")
    assert cart.grand_total == 37.94


@pytest.mark.anyio
async def test_get_cart_price_explicit():
    session = create_mock_session(status=200, json_data=SAMPLE_CART_PRICE_RESPONSE)
    client = HelloFreshClient(session=session, access_token="token")
    cart = await client.get_cart_price(
        "2026-W32", box_size=2, subscription_id="10323453"
    )
    assert cart.grand_total == 37.94


@pytest.mark.anyio
async def test_text_and_json_string_responses():
    session = create_mock_session(
        status=200, json_data=None, text='{"key": "val"}', content_type="text/html"
    )
    client = HelloFreshClient(session=session, access_token="token")
    res = await client._request("GET", "/test", auth_required=False)
    assert res == {"key": "val"}

    session_plain = create_mock_session(
        status=200, json_data=None, text="raw_string", content_type="text/plain"
    )
    client_plain = HelloFreshClient(session=session_plain, access_token="token")
    res_plain = await client_plain._request("GET", "/test", auth_required=False)
    assert res_plain == "raw_string"


@pytest.mark.anyio
async def test_http_401_error():
    session = create_mock_session(status=401, text="Unauthorized")
    client = HelloFreshClient(session=session, access_token="bad_token")
    with pytest.raises(HelloFreshAuthenticationError):
        await client.get_profile()


@pytest.mark.anyio
async def test_http_500_error():
    session = create_mock_session(status=500, text="Internal Server Error")
    client = HelloFreshClient(session=session, access_token="token")
    with pytest.raises(HelloFreshResponseError) as exc_info:
        await client.get_profile()
    assert exc_info.value.status_code == 500


@pytest.mark.anyio
async def test_invalid_grant_raises_authentication_error():
    session = create_mock_session(
        status=400,
        json_data={
            "error": "invalid_grant",
            "error_description": "Unknown or invalid refresh token.",
        },
    )
    client = HelloFreshClient(session=session, refresh_token="invalid_token")

    with pytest.raises(HelloFreshAuthenticationError) as exc_info:
        await client.refresh_access_token()

    assert "invalid_grant" in str(exc_info.value)
    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "invalid_grant"


@pytest.mark.anyio
async def test_connection_error():
    session = create_mock_session(side_effect=aiohttp.ClientError("Network error"))
    client = HelloFreshClient(session=session, access_token="token")
    with pytest.raises(HelloFreshConnectionError):
        await client.get_profile()


@pytest.mark.anyio
async def test_timeout_error():
    session = create_mock_session(side_effect=TimeoutError("Timeout"))
    client = HelloFreshClient(session=session, access_token="token")
    with pytest.raises(HelloFreshConnectionError) as exc_info:
        await client.get_profile()
    assert "timed out" in str(exc_info.value)


@pytest.mark.anyio
async def test_builtin_timeout_error():
    session = create_mock_session(side_effect=TimeoutError("Builtin Timeout"))
    client = HelloFreshClient(session=session, access_token="token")
    with pytest.raises(HelloFreshConnectionError) as exc_info:
        await client.get_profile()
    assert "timed out" in str(exc_info.value)


@pytest.mark.anyio
async def test_fetch_guest_token_success():
    mock_html = (
        '<html><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"ssrPayload":{"serverAuth":{"access_token":"live_dynamic_token"}}}}}'
        "</script></html>"
    )
    session = create_mock_session(status=200, text=mock_html, content_type="text/html")
    client = HelloFreshClient(session=session, guest_token=None)

    token = await client.fetch_guest_token()
    assert token == "live_dynamic_token"
    assert client._guest_token == "live_dynamic_token"


@pytest.mark.anyio
async def test_fetch_guest_token_parse_error():
    mock_html = "<html><body>No Next Data</body></html>"
    session = create_mock_session(status=200, text=mock_html, content_type="text/html")
    client = HelloFreshClient(session=session, guest_token=None)

    with pytest.raises(HelloFreshAuthenticationError):
        await client.fetch_guest_token()


@pytest.mark.anyio
async def test_authenticated_request_401_refreshes_token_and_retries():
    # 1st call: GET /profile -> 401 Token is expired
    # 2nd call: POST /gw/refresh -> 200 OK TokenResponse
    # 3rd call: GET /profile -> 200 OK Profile JSON
    resp_401 = MagicMock()
    resp_401.status = 401
    resp_401.text = AsyncMock(return_value='{"errorMessage": "Token is expired"}')

    resp_refresh = MagicMock()
    resp_refresh.status = 200
    resp_refresh.headers = {"Content-Type": "application/json"}
    resp_refresh.json = AsyncMock(return_value=SAMPLE_TOKEN_RESPONSE)

    resp_profile = MagicMock()
    resp_profile.status = 200
    resp_profile.headers = {"Content-Type": "application/json"}
    resp_profile.json = AsyncMock(return_value=SAMPLE_PROFILE_RESPONSE)

    ctx1 = MagicMock()
    ctx1.__aenter__ = AsyncMock(return_value=resp_401)
    ctx1.__aexit__ = AsyncMock(return_value=None)

    ctx2 = MagicMock()
    ctx2.__aenter__ = AsyncMock(return_value=resp_refresh)
    ctx2.__aexit__ = AsyncMock(return_value=None)

    ctx3 = MagicMock()
    ctx3.__aenter__ = AsyncMock(return_value=resp_profile)
    ctx3.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.request.side_effect = [ctx1, ctx2, ctx3]

    client = HelloFreshClient(
        session=mock_session,
        access_token="expired_token",
        refresh_token="valid_refresh",
    )
    profile = await client.get_profile()
    assert profile.total_people == 2
    assert client.access_token == SAMPLE_TOKEN_RESPONSE["access_token"]

    mock_html = (
        '<html><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"ssrPayload":{"serverAuth":{"access_token":"new_fresh_guest_token"}}}}}'
        "</script></html>"
    )
    # First response 401, second response (/login) 200 HTML, third response 204
    resp_401 = MagicMock()
    resp_401.status = 401
    resp_401.text = AsyncMock(return_value="Unauthorized")

    resp_html = MagicMock()
    resp_html.status = 200
    resp_html.text = AsyncMock(return_value=mock_html)

    resp_204 = MagicMock()
    resp_204.status = 204

    ctx1 = MagicMock()
    ctx1.__aenter__ = AsyncMock(return_value=resp_401)
    ctx1.__aexit__ = AsyncMock(return_value=None)

    ctx2 = MagicMock()
    ctx2.__aenter__ = AsyncMock(return_value=resp_html)
    ctx2.__aexit__ = AsyncMock(return_value=None)

    ctx3 = MagicMock()
    ctx3.__aenter__ = AsyncMock(return_value=resp_204)
    ctx3.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.request.side_effect = [ctx1, ctx2, ctx3]
    mock_session.get = mock_session.request

    client = HelloFreshClient(session=mock_session, guest_token="expired_token")
    res = await client.start_passwordless_login("user@example.com")
    assert isinstance(res, str)
    assert client._guest_token == "new_fresh_guest_token"
