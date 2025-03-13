# Checking a Username is Unique
```json
{
    "version": "1.0.0",
    "from": "public-gateway",
    "data": {
        "step": "check-unique"
        "username": "username"
    }
}
```

This will:
- Check if the username is unique in the ScyllaDB.

```json
{
    "status": 200,
    "data": {
        "unique": false,
    }
}
```

Status will be:
- 200 if the service ran ok.
