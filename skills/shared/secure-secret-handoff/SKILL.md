---
name: secure-secret-handoff
compat: [claude-code, codex]
description: Use for secrets without exposing values to the model.
---

# Secure Secret Handoff

Whenever a user must supply an API key, bot token, client secret, webhook secret, or password, use the `secure_handoff` MCP server. Never ask the user to paste a secret into chat or a tool argument.

1. Call `list_destinations`; choose only an allowlisted destination ID.
2. Call `create_handoff` with only the destination ID and TTL. The key, validator, and path must be pre-bound in trusted configuration and must never be tool arguments.
3. Give the user the one-time tailnet HTTPS URL.
4. After submission, call `get_handoff_status`; proceed only when status is `consumed`.
5. Reload the target and verify only key presence, file mode, provider identity, or connection health. Never print the value.
6. Cancel abandoned handoffs. Never enable Tailscale Funnel.
