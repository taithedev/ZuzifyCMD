# ZuzifyCMD v1.2.0.2a
Windows per-user installer, no PowerShell or manual Neon connection. The client calls the HTTPS service at zuzifycmd.vercel.app; the service alone holds the limited database credential. Startup sends a random locally stored installation UUID and version, not hardware fingerprints. Counts are observed first launches (not exact downloads); online means a heartbeat within 90 seconds. Sessions can be remembered with Windows Credential Manager. 
Commands: 432 conversions plus account, owner, friends, text utilities and system features. Owner commands are authorized by database rank; register the intended account and grant owner only after independently verifying its identity. Pro export is server-gated.
Discord generates an 8-digit code; a trusted bot must call the database discord_confirm function with the verified Discord identity. Do not grant that function to the public client or service.
Private source repository: Windows installer is a CI artifact. Publish only the installer to a separate HTTPS download location and put its tag, URL and SHA256 digest in the Neon settings update row. Never distribute a private GitHub token. Update checks automatic; verified installer download requires confirmation.

## Account and rarity update
Registration now validates fields separately, accepts 8+ character passwords (15+ recommended), rejects selected common passwords and shows masked typing on Windows. Use `register <username>` or `login <username>`. Flower rarity is cosmetic, independently rolled per startup. `rarity`, `rarities`, `search` and categorized help are included. The icon is generated during CI.

## Custom terminal and Bloom engine
Original Python ASCII geometry renderer, five rose petal rings, depth buffer, lighting, petal veins and pollen. Owner rainbow uses the authenticated server rank (not a username match); other users retain their weighted cosmetic roll. Native Windows line editor supports history, Tab completion, arrows, Home/End and editing. Command history stores command names only in memory. New dashboard and utilities included. Releases publish automatically after Windows smoke tests.
