# API
This is a custom API, written in Python using FastAPI, to help me accomplish tasks the can be improved through a RESTful API

## Setup
Simplest setup is to start from [compose.yml](https://github.com/jnstockley/api/blob/dev/compose.yml) and [template.env](https://github.com/jnstockley/api/blob/dev/template.env), which should be renamed to `.env`

### Environment Vairables
- `API_KEY` - Any long, random string. Keep this secret as this is the only form of authentication for the API. All routes require it, except `/health-check/`
- `DATABASE_URL` - The URL to connect to postgres DB. Must start with `postgresql+psycopg://`. Should be in the format specifiec in [template.env](https://github.com/jnstockley/api/blob/dev/template.env)
- `TZ` - Timezone of the container
- `PGTZ` - Timezone the Postgres container should use
- `NEXTCLOUD_URL` - Base URL (must be `https://`) of the Nextcloud instance used by the Talk webhooks
- `NEXTCLOUD_TALK_TOKEN` - Conversation token of the registered [Nextcloud Talk bot](https://nextcloud-talk.readthedocs.io/en/latest/bot-list/) used by `/webhook/databasus`
- `NEXTCLOUD_TALK_SECRET` - Shared secret of the registered Nextcloud Talk bot used by `/webhook/databasus`
- `BESZEL_NEXTCLOUD_TALK_TOKEN` - Conversation token for the separate Beszel Talk bot used by `/webhook/beszel`
- `BESZEL_NEXTCLOUD_TALK_SECRET` - Shared secret of the registered Beszel Talk bot

## Webhooks
- `POST /webhook/databasus` - Forwards a `header` and `message` to a Nextcloud Talk conversation via the [Nextcloud Talk Bot API](https://nextcloud-talk.readthedocs.io/en/latest/bot-list/), using the [nctalk](https://pypi.org/project/nctalk/) package. Requires the `X-API-KEY` header and a JSON body: `{"header": "...", "message": "..."}`
- `POST /webhook/beszel` - Forwards Beszel's generic JSON notifications (`{"title": "...", "message": "..."}`) using a separate Talk bot. Requires the `X-API-KEY` header. Posts the title in bold followed by the message. Returns `{"status": "sent"}` on success, `422` for invalid payloads, `500` for missing or insecure Talk configuration, or `502` when delivery fails.

### Beszel setup

1. Register a separate bot named **Beszel** using Nextcloud's [bot management commands](https://nextcloud-talk.readthedocs.io/en/latest/bot-list/) and enable it in the destination Talk conversation.
2. Set `NEXTCLOUD_URL`, `BESZEL_NEXTCLOUD_TALK_TOKEN` (the destination conversation token), and `BESZEL_NEXTCLOUD_TALK_SECRET` (the new bot's shared secret) in `.env`, then recreate the API container to load the settings. Beszel credentials are required; this endpoint does not fall back to the Databasus bot.
3. In Beszel, open **Settings > Notifications** and add this [generic webhook URL](https://beszel.dev/guide/notifications/generic), replacing the host and API key:

   ```text
   generic://api.example.com/webhook/beszel?template=json&@X-API-KEY=YOUR_URL_ENCODED_API_KEY
   ```

   The `generic://` service uses HTTPS by default. URL-encode the API key if it contains special characters. `template=json` supplies the `title` and `message` fields, and `@X-API-KEY` adds the authentication header.
4. Send a test notification from Beszel, then enable alerts in its systems table.

## How to Access
Using the [compose.yml](https://github.com/jnstockley/api/blob/dev/compose.yml) file, you can access the API at `http://<IP>:5000/health-check`. If everything is setup correctly, you should see `{"status":"ok"}`
