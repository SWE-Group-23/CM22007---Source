# Updating a Food Item
```json
{
    "authUser": "user",
    "from": "public-gateway",
    "version": "1.0.0",
    "data": {
        "food_id": "UUID",
        "img_id": "UUID (optional)",
        "label": "Name of food (optional)",
        "description": "Text description (optional)",
        "useby": "Time in ISO format (optional)"
    }
}
```

This should:
- Update the given food item with the provided fields.

Status will be:
- 200 if the service ran ok.
- 400 for a badly formatted request (bad version, bad json, missing required fields, etc.)
- 500 for any other errors.
