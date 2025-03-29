# Delete Account Chats
```json
{
  "authUser": "user",
  "version": "1.0.0",
  "from": "delete-account-chats",
  "data": {
    "user_id": "user_id"
  }
}
```

This should:
- Delete a all chats associated with a user

```json
{
  "status": 200,
  "data": {
    "message": "Success"
  }
}
```
Status will be:
- 200 if the service ran ok
- 400 if the request was poorly formatted
- 500 if the service had an exception for some other reason