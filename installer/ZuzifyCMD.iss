[Setup]
AppId=ZuzifyCMD
AppName=ZuzifyCMD
AppVersion=1.2.0.1a
SetupIconFile=..\assets\zuzifycmd.ico
AppPublisher=Zuzify
DefaultDirName={localappdata}\Programs\ZuzifyCMD
DefaultGroupName=ZuzifyCMD
OutputDir=..\dist
OutputBaseFilename=ZuzifyCMD-Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern
UninstallDisplayIcon={app}\ZuzifyCMD.exe
[Files]
Source: "..\dist\ZuzifyCMD.exe"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\ZuzifyCMD"; Filename: "{app}\ZuzifyCMD.exe"
Name: "{userdesktop}\ZuzifyCMD"; Filename: "{app}\ZuzifyCMD.exe"
[Run]
Filename: "{app}\ZuzifyCMD.exe"; Description: "Launch ZuzifyCMD"; Flags: nowait postinstall skipifsilent
