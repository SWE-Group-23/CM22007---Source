# Delete Message
```json
{
  "authUser": "user",
  "version": "1.0.0",
  "from": "delete-message",
  "data": {
    "msg_id": "message_id"
  }
}
```

This should:
- Delete a specific message stored in the messages table by id

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