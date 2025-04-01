"""
Add some service docs here.
"""

import os
from secrets import token_hex

from quart import Quart, request
import valkey

from blueprints import register


app = Quart(__name__)
app.register_blueprint(register.blueprint)

GW_NAME = "public-gateway"

r = valkey.Valkey(
    host="public-gateway-valkey",
    port="6379",
    db=0,
    username=os.environ["VALKEY_USERNAME"],
    password=os.environ["VALKEY_PASSWORD"],
)


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


def main():
    """
    Add appropriate docs here.
    """

    app.run(port=8080, debug=True)


if __name__ == "__main__":
    main()
