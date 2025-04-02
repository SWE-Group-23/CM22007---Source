```json
{
  "authUser": "user",
  "version": "1.0.0",
  "from": "fetch-messages",
  "data": {}
}
```

This should:
- Find all foods belonging to the authenticated user.

```json
{
  "status": 200,
  "data": {
    "foods": [
      {
        "food_id": "UUID",
        "img_id": "UUID",
        "label": "Tomatoes",
        "useby": "YYYY-MM-DDTHH:MM"
      }
    ]
  }
}
```

Status will be:
- 200 if successful call, if no food, then "data" will be an empty JSON object.
- 400 if the request was poorly formatted.
- 500 if the service had an exception for some other reason.
