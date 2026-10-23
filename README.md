
<h2 align="center">
    ──「 Telegram Music Bot 」──
</h2>


<h3 align="center">
    ─「 ᴅᴇᴩʟᴏʏ ᴏɴ ʜᴇʀᴏᴋᴜ 」─
</h3>

<p align="center"><a href="https://dashboard.heroku.com/new?template=https://github.com/THE-SHIV-OFFICIAL/REDWINEpro"> <img src="https://img.shields.io/badge/Deploy%20On%20Heroku-yellow?style=for-the-badge&logo=heroku" width="220" height="38.45"/></a></p>

### Central error logger

Unhandled update-handler exceptions, asyncio background-task failures, fatal
startup/runtime errors, and existing `ERROR`/`CRITICAL` log records are sent
to the configured Telegram error group. Reports include the UTC timestamp,
bot/account identity, context, source location, update details, exception
type, and traceback.

The default error logger chat is `-1004392214389`. It can be changed through
`ERROR_LOGGER_ID` in the deployment environment. Add every bot/assistant that
must report errors to that chat and give it permission to send messages.

The deployment runtime uses Python `3.12`, which is the safest baseline for
Pyrogram/Kurigram, PyTgCalls and the native media dependencies on a VPS.

Clone bots are restarted in bounded parallel batches instead of one-by-one.
`CLONE_START_CONCURRENCY` defaults to `6`; `CLONE_START_TIMEOUT` and
`ASSISTANT_START_TIMEOUT` prevent one unavailable bot or assistant from
holding up the rest of the deployment. FloodWait clones retry in the
background instead of blocking the complete restart.

### VPS deployment

Use a virtual environment; do not install this bot into the system Python.
The included installer installs FFmpeg, creates `.venv`, and installs the
locked Telegram client dependencies:

```bash
cd /path/to/anjali-main
sudo bash deploy/install-vps.sh
nano .env
.venv/bin/python -m SHIVMUSIC
```

Fill at least `API_ID`, `API_HASH`, `BOT_TOKEN`, `LOGGER_ID`, `MONGO_DB_URI`,
`OWNER_ID`, and `STRING_SESSION` in `.env`. Optional API/Spotify credentials
are intentionally not bundled in the source anymore.

For automatic restarts, copy `deploy/shivmusic.service.example` to
`/etc/systemd/system/shivmusic.service`, replace the two placeholder paths and
the service user, then run:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now shivmusic
sudo journalctl -u shivmusic -f
```

If the bot was previously started by a `while true` shell loop, stop that old
process before starting systemd; otherwise two Telegram clients will compete
for the same session.
