# ZuzifyCMD 1.0.0
Windows-first terminal with a rotating ASCII flower, monochrome theme, Neon-backed accounts, and a server-managed command catalog. No Electron.

## Start locally
1. Use Python 3.12 and Node 22.
2. In the repository root, run `npm install`.
3. Apply `database/schema.sql` in the intended Neon database if not already applied. Create a dedicated database login with only USAGE on zuzifycmd and SELECT/INSERT/UPDATE/DELETE on its tables (do not use the database owner in production).
4. Set DATABASE_URL in the API host's secret settings, using the dedicated role and TLS. Run `npm start` for local development.
5. In PowerShell: `$env:ZUZIFY_API_URL = "http://127.0.0.1:8787/api/cmd"; python client/zuzifycmd.py`.
6. For a hosted deployment, deploy the repository to a Node-capable host such as Vercel (the API is api/cmd.js), set DATABASE_URL server-side, and set ZUZIFY_API_URL on the client to the HTTPS endpoint. Never put database credentials into the client.

Accounts are specific to CMD, not shared Zuzify Identity. Passwords are scrypt-hashed, session tokens are random, stored only as hashes in Neon and kept in memory on the client. Catalog rows map to built-in handlers, never execute remote shell code. Guests can use local utilities without an account.
 
## Windows build
`python -m pip install pyinstaller==6.12.0` then `python -m PyInstaller --onefile --name ZuzifyCMD client/zuzifycmd.py`. The exe is in dist. Run `python client/zuzifycmd.py --self-test` for smoke tests.
 
The app checks the official GitHub latest stable release at startup in the background, and refreshes its command catalog on each start/login and on sync. If a newer EXE is available, the update command offers to download it, verifies the GitHub SHA-256 digest and leaves the file in your Downloads folder for manual launch. It does not silently execute new binaries.
 
## Admin
Update command descriptions, enable flags, and aliases in the zuzifycmd.commands table. Only implemented local handlers can run. Use a restricted server database role, keep API protection enabled, and configure cleanup of expired sessions and old auth-attempt rows.
