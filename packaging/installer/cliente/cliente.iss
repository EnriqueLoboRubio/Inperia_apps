#define MyAppName "Inperia Cliente"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Inperia"
#define MyAppExeName "Inperia Cliente.exe"

[Setup]
AppId={{3E3EF178-20C7-4C03-9142-AF78A8A9A1D1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Inperia Cliente
DefaultGroupName={#MyAppName}
OutputDir=..\..\..\dist\installer\cliente
OutputBaseFilename=Inperia_Cliente_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Dirs]
Name: "{localappdata}\Inperia Cliente"

[Files]
Source: "..\..\..\dist\cliente\Inperia Cliente\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\config\default_config.json"; DestDir: "{localappdata}\Inperia Cliente"; DestName: "config.json"; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName}"; Flags: nowait postinstall skipifsilent
