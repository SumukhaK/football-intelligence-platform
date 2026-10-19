# Account Preferences API

ADR 035 extends the existing accounts API without changing older endpoints.
Both routes always require a valid bearer token, even with `AUTH_REQUIRED=false`.
The server derives identity from that token. A banned account receives 403.
These account routes do not require consent; the app checks consent first.

## GET /v2/me/preferences

Returns HTTP 200 with:

```json
{"email":"sam@example.com","favourite":{"league":"Premier League","team":"Arsenal"}}
```

An account with no favourite, including older records without this field,
returns `{"email":"sam@example.com","favourite":null}`.
Only a successful explicit null permits onboarding. Responses are never used
as an offline fallback.

## PUT /v2/me/preferences

Body: `{"favourite":{"league":"Premier League","team":"Arsenal"}}`.
Both strings are required, case-sensitive canonical names, 1–100 characters.
`league` must be served by `/v2/competitions`; `team` must belong to that league
in the latest season returned by `/v2/teams?competition=...`.
Null, unknown fields (including email/account IDs), aliases and mismatched
teams are rejected. Clearing a favourite is outside this contract.

Returns the same shape as GET after saving. Updates only the favourite field
in the existing JSON user record or Firestore account document.

## Errors and compatibility

All errors use `{"error":"...","detail":"..."}`.
Missing, invalid, expired or revoked credentials return 401 `Not signed in`;
banned accounts return 403 `Account blocked`. Invalid request bodies or catalog
pairs return 422 `Invalid favourite`. Store/provider/catalog failures and
invalid stored favourites return 503 `Account preferences unavailable`, never
a successful empty account. No provider exception details are returned.

No migration job or cloud write is needed. Other account fields and old clients'
endpoints remain intact. Old apps keep device-local behaviour; updated apps
discard legacy unscoped favourites and load from the server before routing.
