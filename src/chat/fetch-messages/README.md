# Fetch Messages
```json
{
  "authUser": "user",
  "version": "1.0.0",
  "from": "fetch-messages",
  "data": {
    "chat_id": "chat_id"
  }
}
```

This should:
- Return a list of messages for a specific chat

```json
{
  "status": 200,
  "data": {
    "messages": [
      {
        "msg_id": "msg_id",
        "chat_id": "chat_id",
        "sender_user": "sender_user",
        "sent_time": "time_sent",
        "message": "sample chat message",
        "reported": "False"
      }
  ] 
  }
}
```
Status will be:
- 200 if the service ran ok
- 400 if the request was poorly formatted
- 500 if the service had an exception for some other reason