"""
Add some service docs here.
"""

import os
from secrets import token_hex

from quart import Quart, request, Response
import valkey

import shared
from shared.rpcs.register_rpc import RegisterRPCClient

app = Quart(__name__)


r = valkey.Valkey(
    host="public-gateway-valkey",
    port="6379",
    db=0,
    username=os.environ["VALKEY_USERNAME"],
    password=os.environ["VALKEY_PASSWORD"],
)


register_client = RegisterRPCClient(
    os.environ["RABBITMQ_USERNAME"],
    os.environ["RABBITMQ_PASSWORD"],
)


@app.before_request
async def before_request():
    token = request.cookies.get("session-token")
    if token is None:
        # There could technically be a collison here
        token = token_hex(64)
        request.set_token = True
        r.set(token, "{}", ex=86400*7)
    else:
        request.set_token = False
    
    request.token = token

@app.after_request
async def after_request(response):
    if request.set_token:
        # Should set secure to True when deployed
        response.set_cookie("session-token", request.token, samesite="lax", httponly=True)

    return response
        

@app.route("/")
def index():
    return "Hello, world"

@app.post("/register/check-valid-username")
async def check_username():
    json = await request.get_json()
    
    print(request)
    print(json)

    if json is None or "username" not in json:
        return Response(status=400)

    resp = register_client.check_valid_username_call(
        sid=request.token,
        srv_from="public-gateway",
        username=json["username"],
    )
    
    print(resp)

    if resp["status"] != 200:
        return Response(status=400)
    
    return resp["data"]


def main():
    """
    Add appropriate docs here.
    """
    
    app.run(port=8080, debug=True)

if __name__ == "__main__":
    main()
