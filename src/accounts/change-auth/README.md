# The Factors
Accounts have three factors:
- Password
- OTP
- Backup Code

Provided at least two of these factors, users are able to modify
all of their factors.

# Changing Authentication
## Backup Code + Password
```json
{
  "sid": "token",
  "version": "1.0.0",
  "from": "public-gateway",
  "data": {
      "factors": "backup-pass",
      "username": "username",
      "backup-code": "...",
      "password-digest": "$argon2id$..."
  }
}
```

## Backup Code + OTP
### Step 1
```json
{
  "sid": "token",
  "version": "1.0.0",
  "from": "public-gateway",
  "data": {
      "factors": "backup-otp",
      "username": "username",
      "backup-code": "..."
  }
}
```

### Step 2
```json
{
    "sid": "token",
    "version": "1.0.0",
    "from": "public-gateway",
    "data": {
        "factors": "otp",
        "otp": "123456"
    }
}
```

## Password + OTP
### Step 1
```json
{
  "sid": "token",
  "version": "1.0.0",
  "from": "public-gateway",
  "data": {
      "factors": "password-otp",
      "username": "username",
      "password-digest": "$argon2id$..."
  }
}
```

### Step 2
```json
{
    "sid": "token",
    "version": "1.0.0",
    "from": "public-gateway",
    "data": {
        "factors": "otp",
        "otp": "123456"
    }
}
```

## Responses
For any two-step processes, responses to the first step will be:
```json
{
    "status": 200,
    "data": {
        "correct": true
    }
}
```
with `.data.correct` being `true` if they can continue to the next stage, and `false`
if not.

For the final step of two-step processes, or the only step of single-step processes,
the response will be the same as above, but with `true` indicating that the session token
or authenticated user can now decide on one factor to change.

Other status codes:
- 400 - malformed request/json.
- 403 - if user skipped a step in the process.
- 500 - other internal error occurred.

## Changing a Factor
Once the `sid` or `authUser` is authenticated, they are authorised to change one of their
three factors. Once they have done so, they will have to authenticate again if they wish
to change another factor.

### Change Password
```json
{
    "sid": "token",
    "version": "1.0.0",
    "from": "public-gateway",
    "data": {
        "change": "password",
        "password-digest": "$argon2id$..."
    }
}
```

The response will be:
```json
{
    "status": 200,
    "data": {}
}
```
if all went well.

Other status codes:
- 400 - malformed request/json.
- 403 - if user has not been authenticated yet so is not authorised to change a factor.
- 500 - other internal error occurred.

### Change Backup Code
```json
{
    "sid": "token",
    "version": "1.0.0",
    "from": "public-gateway",
    "data": {
        "change": "backup"
    }
}
```

The response will be:
```json
{
    "status": 200,
    "data": {
        "backup-code": "..."
    }
}
```
if all went well.

Other status codes:
- 400 - malformed request/json.
- 403 - if user has not been authenticated yet so is not authorised to change a factor.
- 500 - other internal error occurred.

### Change OTP
#### Step 1
```json
{
    "sid": "token",
    "version": "1.0.0",
    "from": "public-gateway",
    "data": {
        "change": "otp-new"
    }
}
```

The response will be:
```json
{
    "status": 200,
    "data": {
        "otp-sec": "SECRET"
    }
}
```
if all went well.

Other status codes:
- 400 - malformed request/json.
- 403 - if user has not been authenticated yet so is not authorised to change a factor.
- 500 - other internal error occurred.

To confirm the change, the user must give back the current OTP.

#### Step 2
```json
{
    "sid": "token",
    "version": "1.0.0",
    "from": "public-gateway",
    "data": {
        "change": "otp-verify"
        "otp": "123456"
    }
}
```

The response will be:
```json
{
    "status": 200,
    "data": {
        "correct": true,
    }
}
```
if all went well. `.data.correct` will be `false` if the OTP is incorrect, and the user
can send another OTP.

Other status codes:
- 400 - malformed request/json.
- 403 - if user has not been authenticated yet so is not authorised to change a factor.
- 500 - other internal error occurred.
