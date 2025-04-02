# View Chats

Requests to the server should follow:

```json
{
  "authUser": "user",
  "version": "1.0.0",
  "from": "view-chats",
  "data": {}
}
```

This should:
- Return a list of chats for the ```authUser```

```json
{
  "status": 200,
  "data": {
    "chats": [
      {
        "chat_id": "chat_id",
        "user1": "username",
        "user2": "username",
        "blocked": "False"
      }
    ]
  }
}
```
Status will be:
- 200 if the service ran ok
- 400 if the request was poorly formatted
- 500 if the service had an exception for some other reason

It is expected that either user1 or user2 will be the logged in user viewing the chats list.