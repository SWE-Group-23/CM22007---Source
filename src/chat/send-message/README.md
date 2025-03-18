# Add Message
```json
{
  "authUser": "user",
  "version": "1.0.0",
  "from": "send-message",
  "data": {
    "chat_id": "chat_id",
    "sender_id": "user_id",
    "time_sent": time_sent,
    "message": "sample chat message"
  }
}
```
Where time_sent is in milliseconds

This should:
- Add a message sent by a user in a chat to the messages table

```json
{
  "status": 200,
  "data": {
    "message": "Message sent"
  }
}
```
Status will be:
- 200 if the service ran ok
- 400 if the request was poorly formatted
- 500 if the service had an exception for some other reason