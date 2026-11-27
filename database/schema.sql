BEGIN;
CREATE SCHEMA IF NOT EXISTS zuzifycmd;
CREATE TABLE IF NOT EXISTS zuzifycmd.accounts (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), username text NOT NULL UNIQUE CHECK (username ~ '^[a-z0-9_]{3,24}$'), password_hash text NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS zuzifycmd.sessions (token_hash text PRIMARY KEY, account_id uuid NOT NULL REFERENCES zuzifycmd.accounts(id) ON DELETE CASCADE, expires_at timestamptz NOT NULL);
CREATE TABLE IF NOT EXISTS zuzifycmd.commands (name text PRIMARY KEY, description text NOT NULL, category text NOT NULL, handler text NOT NULL, enabled boolean NOT NULL DEFAULT true, updated_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS zuzifycmd.auth_attempts (bucket text NOT NULL, window_id bigint NOT NULL, hits integer NOT NULL DEFAULT 1, PRIMARY KEY(bucket,window_id));
INSERT INTO zuzifycmd.commands(name,description,category,handler) VALUES
('help','List available commands','core','help'),
('clear','Clear the terminal','core','clear'),
('exit','Close the terminal','core','exit'),
('whoami','Display your account','account','whoami'),
('logout','End your session','account','logout'),
('sync','Refresh cloud catalog','cloud','sync'),
('update','Check for app updates','cloud','update'),
('version','Show app version','core','version'),
('time','Show local time','system','time'),
('date','Show local date','system','date'),
('sysinfo','Show OS and processor count','system','sysinfo'),
('uptime','Show app session uptime','system','uptime'),
('echo','Print text','tools','echo'),
('uuid','Generate a random UUID','tools','uuid'),
('hash','Compute SHA-256 of text','tools','hash'),
('base64','Encode text as Base64','tools','base64'),
('decode64','Decode Base64 text','tools','decode64'),
('theme','Toggle terminal theme','core','theme'),
('flower','Preview flower animation','core','flower'),
('about','About ZuzifyCMD','core','about'),
('commands','List available commands','core','help'),
('cls','Clear the terminal','core','clear'),
('now','Show local time','system','time'),
('guid','Generate a random UUID','tools','uuid')
ON CONFLICT(name) DO NOTHING;
COMMIT;
