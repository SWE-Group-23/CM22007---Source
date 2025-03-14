# Checking a Username is Valid
```json
{
    "authUser": "token"
    "version": "1.0.0",
    "from": "public-gateway",
    "data": {
        "step": "check-valid-username",
        "username": "username"
    }
}
```

This will:
- Return invalid if the username is >=5 characters long.
- Return invalid if the username consists only of [0-9A-Za-z._-].
- Return invalid if the username starts or ends with [._-].
- Check if the username is unique in the accounts table.

```json
{
    "status": 200,
    "data": {
        "valid": false,
    }
}
```

Status will be:
- 200 if the service ran ok.
- 400 if the request was badly formatted.
- 500 if the service had an exception for some other reason.

Any non 2XX code will have `resp["data"]["reason"]`.

# Set a Password
```json
{
    "authUser": "token",
    "version": "1.0.0",
    "from": "public-gateway",
    "data": {
        "step": "check-password",
        "password-digest": "NDjiNdal4knkS213MS/ndas+ajk=",
    }
}
```

This will:
- Check if the token is at the right stage.
- Salt and hash the already hashed (by the public gateway) username:password.
- Store this salt and hash in the users Valkey stage.
- Update the users Valkey stage.

```json
{
    "status": 200,
    "data": {}
}
```

:::concern - information disclosure 403 vs 400:::

Status will be:
- 200 if the call was successful.
- 400 if the request was badly formatted, or the user has no current Valkey stage.
- 403 if the user has not got the correct Valkey stage.
- 500 if the service had an exception for some other reason.

Any non 2XX code will have `resp["data"]["reason"]`.

# Set up OTP
```json
{
    "authUser": "token",
    "version": "1.0.0",
    "from": "public-gateway",
    "data": {
        "step": "setup-otp",
    }
}
```

This will:
- Check if the token is at the right stage.
- Generate and store an OTP secret.
- Create a provisioning URI.
- Update the users Valkey stage.

```json
{
    "status": 200,
    "data": {
        "prov_uri": "otpauth://totp/app%20name:username?secret=SECRET&issuer=app%20name"
    }
}
```

:::concern - information disclosure 403 vs 400:::

Status will be:
- 200 if the call was successful.
- 400 if the request was badly formatted, or the user has no current Valkey stage.
- 403 if the user has not got the correct Valkey stage.
- 500 if the service had an exception for some other reason.

Any non 2XX code will have `resp["data"]["reason"]`.

# Verify OTP
```json
{
    "authUser": "token",
    "version": "1.0.0",
    "from": "public-gateway",
    "data": {
        "step": "verify-otp",
        "otp": "123456",
    }
}
```

This will:
- Check if the token is at the right stage.
- Check given OTP with stored TOTP secret.
- Update the users Valkey stage.

```json
{
    "status": 200
    "data": {}
}
```

:::concern - information disclosure 403 vs 400:::

Status will be:
- 200 if the call was successful.
- 400 if the request was badly formatted, or the user has no current Valkey stage.
- 403 if the user has not got the correct Valkey stage.
- 500 if the service had an exception for some other reason.

Any non 2XX code will have `resp["data"]["reason"]`.
