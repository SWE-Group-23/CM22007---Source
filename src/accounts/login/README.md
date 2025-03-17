# Username and Password
```json
{
    "authUser": "token",
    "from": "public-gateway",
    "version": "1.0.0",
    "data": {
        "step": "username-password",
        "username": "Username",
        "password_digest": "$argon2id$..."
    }
}
```

This should:
- Check that the username and password are correct.

```json
{
    "status": 200,
    "data": {
        "correct": false
    }
}
```

Status will be:
- 200 if the service ran ok.
- 400 if the request was badly formatted.
- 403 if the token exists in Valkey already.
- 500 if the service had an exception for some other reason.

# Verify OTP
```json
{
    "authUser": "token",
    "from": "public-gateway",
    "version": "1.0.0",
    "data": {
        "step": "verify-otp",
        "otp": "123456"
    }
}
```

This should:
- Check that the OTP is correct for the user at the current time.

```json
{
    "status": 200,
    "data": {
        "correct": false
    }
}
```

Status will be:
- 200 if the service ran ok.
- 400 if the request was badly formatted.
- 403 if the token exists in Valkey already.
- 500 if the service had an exception for some other reason.
