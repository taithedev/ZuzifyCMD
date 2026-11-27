# ZuzifyCMD 1.1.0
Double-click ZuzifyCMD.exe from GitHub Releases. No PowerShell, Node server, API, or Electron required. The loader is a shaded pink/white 3D ASCII flower that grows from a glowing center. Offline commands work immediately.

## Direct Neon setup (private/trusted desktop)
The Neon project is Zuzify App Data, database zuzify, schema zuzifycmd. Direct SQL functions are installed. Create a dedicated restricted login role (not owner, no table permissions or inherited admin roles), and grant only:
```sql
GRANT CONNECT ON DATABASE zuzify TO your_restricted_role;
GRANT USAGE ON SCHEMA zuzifycmd TO your_restricted_role;
GRANT EXECUTE ON FUNCTION zuzifycmd.direct_catalog(), zuzifycmd.direct_auth(text,text,text), zuzifycmd.direct_session(text,text) TO your_restricted_role;
```
In the EXE, type connect, paste the restricted role's Neon URL at the hidden prompt, and optionally save it to Windows Credential Manager. TLS certificate and hostname verification are required. Use register or login for CMD accounts. Do not distribute shared database credentials or embed them in the EXE. For a public consumer service, use an identity-aware backend. The previous API source is retained for reference only; not needed by this client. Direct accounts use bcrypt and the old API uses a different format.

Type help, sync, flower, or update. Startup checks GitHub for updates automatically; installation of verified downloads is manual.

## Build
Install requirements.txt with Python 3.12, then run python client/zuzifycmd.py --self-test. GitHub Actions builds and tests the Windows EXE before publishing.
