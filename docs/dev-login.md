# Dev Login Endpoint

## Purpose

During local development, the application's only login method is Google OAuth, which requires a real Google account and a valid OAuth token on every session. This is friction for developers and makes it harder to test features that sit behind authentication.

The `POST /api/v1/auth/dev-login` endpoint provides a shortcut: pass an email and a name, get back a JWT — no Google interaction required.

**This endpoint is disabled in production.** It only works when `APP_DEBUG=True`.

---

## Security model

### How it is gated

The endpoint checks `settings.APP_DEBUG` on every request. If the flag is `False`, it returns `403 Forbidden` immediately, before any database access.

```
APP_DEBUG=False  →  403 Forbidden  (production default)
APP_DEBUG=True   →  normal login flow  (development only)
```

### Risks and mitigations

| Risk | Mitigation |
|---|---|
| Endpoint accidentally enabled in production | `APP_DEBUG` defaults to `False` in `app/core/config.py`; the flag must be explicitly set to `True` |
| Weak email validation allows malformed input | `EmailStr` (Pydantic) validates the email field at the DTO layer before the service is called |
| Dev users persist in the production database | Dev login users are only ever created when `APP_DEBUG=True`; the database in production should never have this flag enabled |

### Extra hardening (optional)

For additional safety, you can register the route only when `APP_DEBUG=True` at startup, so the route literally does not exist in production rather than returning 403. This would require a conditional include in `app/http/config.py`.

---

## Alternatives considered

| Approach | Trade-offs |
|---|---|
| **Dev login endpoint (this implementation)** | Simple, zero infrastructure. Risk: accidental prod exposure if `APP_DEBUG` is misconfigured. |
| **Shared test Google account** | No code changes. Requires real internet access, brittle with 2FA, shared credentials. |
| **Local OAuth mock server** (e.g. Keycloak, dex) | Most realistic — app behaves identically to production. More setup required. Best for security-sensitive teams. |
| **Magic token bypass in `/google-login`** | Fewer moving parts (one endpoint), but mixes prod and dev logic in the same handler. |

---

## Usage

### 1. Enable debug mode

In your `.env` file:

```env
APP_DEBUG=True
```

### 2. Start the server

```bash
uvicorn app.main:app --reload
```

### 3. Call the endpoint

**Request**

```
POST /api/v1/auth/dev-login
Content-Type: application/json

{
  "email": "dev@local.com",
  "name": "Dev User"
}
```

**Example with curl**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/dev-login \
  -H "Content-Type: application/json" \
  -d '{"email": "dev@local.com", "name": "Dev User"}'
```

**Response**

```json
{
  "access_token": "<JWT>",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "email": "dev@local.com",
    "name": "Dev User",
    ...
  }
}
```

### 4. Use the token

Include the JWT in the `Authorization` header for any protected endpoint:

```
Authorization: Bearer <access_token>
```

### Production behaviour

When `APP_DEBUG=False`:

```
HTTP 403 Forbidden
{"detail": "This endpoint is only available in debug mode."}
```

---

## Code path

```
POST /api/v1/auth/dev-login
  └── auth_rest.py: dev_login()
        ├── Guard: settings.APP_DEBUG → 403 if False
        └── AuthBusiness.dev_login_service(data)
              ├── UserMongoRepository.find_with_filters({"email": ...})
              ├── If user not found → UserEntity.create() → repo.create()
              │     └── Re-fetch to get DB-assigned _id
              ├── If user exists → update last_login → repo.update()
              ├── UserMapper.to_dto(user_entity)
              ├── AuthBusiness.create_access_token({"sub": user_id})
              └── Return {access_token, token_type, user}
```

### Key files

| File | Role |
|---|---|
| `app/http/rest/v1/auth_rest.py` | HTTP endpoint + `APP_DEBUG` guard |
| `app/business/auth_bo.py` | `dev_login_service()` — user lookup/creation and JWT generation |
| `app/core/common/application/dto/auth.py` | `DevLoginData` DTO (`email: EmailStr`, `name: str`) |
| `app/core/users/infra/database/repositories/user_mongo_repo.py` | `find_with_filters()` used to look up user by email |
| `app/core/config.py` | `APP_DEBUG` setting (defaults to `False`) |
