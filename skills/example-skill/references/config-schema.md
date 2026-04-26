# Configuration schema

This skill reads configuration from `~/.config/your-skill-name/config.yaml`.

## Resolution order

Values are resolved in this order, first match wins:

1. Environment variables prefixed `YOUR_SKILL_NAME_*`
2. `~/.config/your-skill-name/config.yaml`
3. `./.your-skill-name/config.yaml` (project-local, optional)
4. Interactive prompt via `bash scripts/configure.sh`

## Required keys

| Key | Env var | Type | Description |
|---|---|---|---|
| `api_endpoint` | `YOUR_SKILL_NAME_API_ENDPOINT` | string (URL) | Base URL for the upstream API. |
| `project_id`   | `YOUR_SKILL_NAME_PROJECT_ID`   | string         | Project identifier. |

## Optional keys

| Key | Env var | Type | Default | Description |
|---|---|---|---|---|
| `timeout_seconds` | `YOUR_SKILL_NAME_TIMEOUT_SECONDS` | integer | `30` | Request timeout. |

## Example

```yaml
# ~/.config/your-skill-name/config.yaml
api_endpoint: https://api.example.com
project_id: proj_abc123
timeout_seconds: 30
```

## File permissions

The config file must be `0600` (owner read/write only). `configure.sh` sets this automatically. If permissions are wrong, the skill will refuse to read the file and prompt you to `chmod 600` it.
