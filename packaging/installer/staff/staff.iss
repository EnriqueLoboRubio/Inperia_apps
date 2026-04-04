#define MyAppName "Inperia Staff"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Inperia"
#define MyAppExeName "Inperia Staff.exe"

[Setup]
AppId={{44CFE2D8-C2DE-4D03-9281-4D794A709A1F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Inperia Staff
DefaultGroupName={#MyAppName}
OutputDir=..\..\..\dist\installer\staff
OutputBaseFilename=Inperia_Staff_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Dirs]
Name: "{localappdata}\Inperia Staff"

[Files]
Source: "..\..\..\dist\staff\Inperia Staff\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\..\shared\config.json"; DestDir: "{localappdata}\Inperia Staff"; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
function TryUseExistingFile(var TargetPath: String; const CandidatePath: String): Boolean;
begin
  Result := FileExists(CandidatePath);
  if Result then
    TargetPath := CandidatePath;
end;

function FindOllamaExecutable(var OllamaExe: String): Boolean;
var
  WhereOutputFile: String;
  WhereLines: TArrayOfString;
  ResultCode: Integer;
begin
  Result := False;
  OllamaExe := '';

  if TryUseExistingFile(OllamaExe, ExpandConstant('{localappdata}\Programs\Ollama\ollama.exe')) then
  begin
    Result := True;
    exit;
  end;

  if TryUseExistingFile(OllamaExe, ExpandConstant('{autopf}\Ollama\ollama.exe')) then
  begin
    Result := True;
    exit;
  end;

  if IsWin64 and TryUseExistingFile(OllamaExe, ExpandConstant('{commonpf64}\Ollama\ollama.exe')) then
  begin
    Result := True;
    exit;
  end;

  if TryUseExistingFile(OllamaExe, ExpandConstant('{commonpf32}\Ollama\ollama.exe')) then
  begin
    Result := True;
    exit;
  end;

  if TryUseExistingFile(OllamaExe, ExpandConstant('{commonpf}\Ollama\ollama.exe')) then
  begin
    Result := True;
    exit;
  end;

  WhereOutputFile := ExpandConstant('{tmp}\ollama_where.txt');
  if Exec(
    'cmd.exe',
    '/c where ollama.exe > "' + WhereOutputFile + '"',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  ) then
  begin
    if (ResultCode = 0) and LoadStringsFromFile(WhereOutputFile, WhereLines) then
    begin
      if (GetArrayLength(WhereLines) > 0) and FileExists(Trim(WhereLines[0])) then
      begin
        OllamaExe := Trim(WhereLines[0]);
        Result := True;
      end;
    end;
  end;

  if FileExists(WhereOutputFile) then
    DeleteFile(WhereOutputFile);
end;

function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  OllamaListFile: String;
  FileLines: TArrayOfString;
  i: Integer;
  OllamaFound: Boolean;
  QwenFound: Boolean;
  OllamaExe: String;
  CmdParams: String;
begin
  OllamaFound := False;
  QwenFound := False;
  OllamaListFile := '';

  if FindOllamaExecutable(OllamaExe) then
  begin
    OllamaListFile := ExpandConstant('{tmp}\ollama_list.txt');
    CmdParams := '/c ""' + OllamaExe + '" list > "' + OllamaListFile + '""';

    if Exec('cmd.exe', CmdParams, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    begin
      if ResultCode = 0 then
      begin
        OllamaFound := True;
        if LoadStringsFromFile(OllamaListFile, FileLines) then
        begin
          for i := 0 to GetArrayLength(FileLines) - 1 do
          begin
            if Pos('qwen2.5:latest', Lowercase(FileLines[i])) > 0 then
            begin
              QwenFound := True;
              break;
            end;
          end;
        end;
      end;
    end;
  end;
  
  if not OllamaFound then
  begin
    MsgBox('Error: No se ha detectado Ollama en el sistema o no esta en el PATH.' + #13#10 + 'Ollama es un requisito obligatorio.' + #13#10 + 'Por favor, instalalo desde ollama.com antes de continuar.', mbError, MB_OK);
    Result := False;
  end
  else if not QwenFound then
  begin
    MsgBox('Error: No se ha encontrado el modelo "qwen2.5:latest" en Ollama.' + #13#10 + 'Por favor, abre una terminal y ejecuta el siguiente comando antes de instalar:' + #13#10 + #13#10 + 'ollama run qwen2.5:latest', mbError, MB_OK);
    Result := False;
  end
  else
  begin
    Result := True;
  end;
  
  if FileExists(OllamaListFile) then
    DeleteFile(OllamaListFile);
end;
