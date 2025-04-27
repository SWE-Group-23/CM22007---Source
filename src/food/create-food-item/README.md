# Creating a Food Item
```json
{
    "authUser": "user",
    "from": "public-gateway",
    "version": "1.0.0",
    "data": {
        "img_id": "UUID (optional)",
        "label": "Name of food",
        "description": "Text description (optional)",
        "useby": "Time in ISO format"
    }
}
```

This should:
- Add the given food item to the database.

Status will be:
- 200 if the service ran ok.
- 400 for a badly formatted request (bad version, bad json, missing required fields, etc.)
- 500 for any other errors.
