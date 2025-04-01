import os

from quart import Blueprint, request, Response
import valkey
from pika.exceptions import ChannelWrongStateError
import argon2

from shared.rpcs.register_rpc import RegisterRPCClient

blueprint = Blueprint("register", __name__, url_prefix="/register")

GW_NAME = "public-gateway"

r = valkey.Valkey(
    host="public-gateway-valkey",
    port="6379",
    db=0,
    username=os.environ["VALKEY_USERNAME"],
    password=os.environ["VALKEY_PASSWORD"],
)

ph = argon2.PasswordHasher()


def create_register_client():
    global register_client

    register_client = RegisterRPCClient(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"],
    )


create_register_client()


@blueprint.post("/check-valid-username")
async def check_username():
    json = await request.get_json()

    if json is None or "username" not in json:
        return Response(status=400)

    while True:
        try:
            resp = register_client.check_valid_username_call(
                sid=request.token,
                srv_from=GW_NAME,
                username=json["username"],
            )
            break
        except ChannelWrongStateError:
            create_register_client()

    return resp["data"], resp["status"]


@blueprint.post("/check-password")
async def check_password():
    json = await request.get_json()

    if json is None:
        return Response(status=400)

    if "password" not in json or "username" not in json:
        return Response(status=400)

    try:
        pw_digest = ph.hash(
            json["password"], salt=json["username"].ljust(16, "=").encode()
        )
    except argon2.exceptions.HashingError:
        return Response(status=500)

    while True:
        try:
            resp = register_client.set_password_call(
                sid=request.token,
                srv_from=GW_NAME,
                password_digest=pw_digest,
            )
            break
        except ChannelWrongStateError:
            create_register_client()

    return resp["data"], resp["status"]


@blueprint.get("/setup-otp")
async def setup_otp():
    while True:
        try:
            resp = register_client.setup_otp_call(
                sid=request.token,
                srv_from=GW_NAME,
            )
            break
        except ChannelWrongStateError:
            create_register_client()

    return resp["data"], resp["status"]


@blueprint.post("/verify-otp")
async def verify_otp():
    json = await request.get_json()

    if json is None:
        return Response(status=400)

    if "otp" not in json:
        return Response(status=400)

    while True:
        try:
            resp = register_client.verify_otp_call(
                sid=request.token,
                srv_from=GW_NAME,
                otp=json["otp"],
            )
            break
        except ChannelWrongStateError:
            create_register_client()

    return resp["data"], resp["status"]


@blueprint.get("/backup-code")
async def backup_code():
    while True:
        try:
            resp = register_client.backup_code_call(
                sid=request.token,
                srv_from=GW_NAME,
            )
            break
        except ChannelWrongStateError:
            create_register_client()

    return resp["data"], resp["status"]
