"""
Runs a Quart app which serves as the public API gateway.
"""

import os
import json
from secrets import token_hex

from quart import Quart, request
from quart_cors import cors
import valkey
import argon2

from blueprints import register, login


app = Quart(__name__)
app = cors(app, allow_origin="http://localhost:3000")

app.register_blueprint(register.blueprint)
app.register_blueprint(login.blueprint)

GW_NAME = "public-gateway"

r = valkey.Valkey(
    host="public-gateway-valkey",
    port="6379",
    db=0,
    username=os.environ["VALKEY_USERNAME"],
    password=os.environ["VALKEY_PASSWORD"],
)
ph = argon2.PasswordHasher()


@app.before_request
async def before_request():
    token = request.cookies.get("session-token")
    if token is None:
        # There could technically be a collison here
        token = token_hex(64)
        request.set_token = True
        r.set(token, "{}", ex=86400 * 7)
    else:
        request.set_token = False

    request.token = token


@app.after_request
async def after_request(response):
    if request.set_token:
        # Should set secure to True when deployed
        response.set_cookie(
            "session-token", request.token, samesite="lax", httponly=True
        )

    return response


@app.route("/")
def index():
    return "Hello, world"


@app.get("/check-logged-in")
async def check_logged_in():
    try:
        session = r.get(request.token)
        # if a session exists but is not authenticated
        if session and session == b"{}":
            return {"logged_in": False}, 200
        # if a session does not exist in valkey
        elif not session:
            return {"logged_in": False}, 200
    except AttributeError:
        # if the request didn't have a session token cookie
        return {"logged_in": False}, 200

    return {"logged_in": True}, 200


def main():
    """
    Starts running the Quart app.
    """

    app.run(port=8080, debug=True)


if __name__ == "__main__":
    main()
