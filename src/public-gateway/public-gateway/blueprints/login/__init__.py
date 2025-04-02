import os
import json

from quart import Blueprint, request, Response, abort
import valkey
from pika.exceptions import ChannelWrongStateError, AMQPConnectionError
import argon2

from shared.rpcs.login_rpc import LoginRPCClient

blueprint = Blueprint("login", __name__, url_prefix="/login")

GW_NAME = "public-gateway"

r = valkey.Valkey(
    host="public-gateway-valkey",
    port="6379",
    db=0,
    username=os.environ["VALKEY_USERNAME"],
    password=os.environ["VALKEY_PASSWORD"],
)

ph = argon2.PasswordHasher()


def create_login_client():
    global login_client

    login_client = LoginRPCClient(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"],
    )


create_login_client()


@blueprint.before_request
async def block_auth_users():
    try:
        session = r.get(request.token)
        if session and session != b"{}":
            abort(403, "Already logged in.")
    except AttributeError:
        pass


@blueprint.post("/check-password")
async def check_password():
    json_req = await request.get_json()

    if json_req is None:
        return Response(status=400)

    if "password" not in json_req or "username" not in json_req:
        return Response(status=400)

    try:
        pw_digest = ph.hash(
            json_req["password"],
            salt=json_req["username"].ljust(16, "=").encode(),
        )
    except argon2.exceptions.HashingError:
        return Response(status=500)

    while True:
        try:
            resp = login_client.user_pw_call(
                sid=request.token,
                srv_from=GW_NAME,
                username=json_req["username"],
                password_digest=pw_digest,
            )
            break
        except (ChannelWrongStateError, AMQPConnectionError):
            create_login_client()

    return resp["data"], resp["status"]


@blueprint.post("/verify-otp")
async def verify_otp():
    json_req = await request.get_json()

    if json_req is None or "otp" not in json_req:
        return Response(status=400)

    while True:
        try:
            resp = login_client.verify_otp_call(
                sid=request.token,
                srv_from=GW_NAME,
                otp=json_req["otp"],
            )
            break
        except (ChannelWrongStateError, AMQPConnectionError):
            create_login_client()

    # if successful, set the username in valkey
    # to indicate logged in user
    if resp["status"] == 200 and resp["data"]["correct"]:
        r.set(
            request.token,
            json.dumps({"username": resp["data"]["username"]}),
            keepttl=True,
        )

    return resp["data"], resp["status"]
