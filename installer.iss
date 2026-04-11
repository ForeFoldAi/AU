; Inno Setup 6 — builds a Windows installer for the Nuitka onefile EXE.
; Prerequisite: run build_nuitka.bat first so build\AttendanceReport.dist exists.

#define AppName "ForeFold Report Generator"
#define AppVersion "1.0.0"
#define AppPublisher "ForeFold AI"
#define AppExeName "AttendanceReport.exe"

[Setup]
AppId={{E7D1F9A3-2B8C-4D6E-A1F0-9C8B7A6D5E4F}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
; Per-user install (no admin) — works on locked-down PCs. Installs under AppData.
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
OutputDir=build\installer
OutputBaseFilename=ForeFoldReportGeneratorSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExeName}
MinVersion=10.0
CloseApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; Standalone build: include the entire dist folder so all DLLs/Qt plugins ship.
Source: "build\AttendanceReport.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup: Boolean;
var
  Path: String;
begin
  Path := ExpandConstant('{src}\build\AttendanceReport.dist\{#AppExeName}');
  if not FileExists(Path) then
  begin
    MsgBox('Missing: ' + Path + #13#10 + #13#10 +
           'Build the EXE first: open a terminal in this project folder and run build_nuitka.bat, ' +
           'then compile this script again.', mbError, MB_OK);
    Result := False;
  end
  else
    Result := True;
end;
