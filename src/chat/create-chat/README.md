# Create Chat
```json
{
  "authUser": "user",
  "version": "1.0.0",
  "from": "create-chat",
  "data": {
    "receiver_user": "receiver_user"
  }
}
```

This should:
- Create a new chat between the ```authUser``` and the receiver

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