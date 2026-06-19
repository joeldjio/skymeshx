; ═══════════════════════════════════════════════════════════════════════
;  SkyMeshX CLI — Windows Installer (Inno Setup 6+)
; ═══════════════════════════════════════════════════════════════════════
;
;  Build:
;     iscc tools\installer\inno\skymeshx_cli.iss
;  Output:
;     tools\installer\out\SkyMeshX-CLI-Setup-0.2.0.exe
;
;  Prerequisite: PyInstaller has produced dist\SkyMeshXCLI\.
; ═══════════════════════════════════════════════════════════════════════

#define AppName        "SkyMeshX CLI"
#define AppPublisher   "SkyMeshX Aerospace Research"
#define AppVersion     "0.2.0"
#define AppURL         "https://github.com/joeldjio/skymeshxproject"
#define AppExeName     "skymeshx.exe"
#define AppId          "{{B5A1F4F2-9E1E-4A2C-9D6B-SKYMESHX-CLI}"

#define ProjectRoot    "..\..\.."
#define DistRoot       ProjectRoot + "\dist\SkyMeshXCLI"
#define AssetsDir      "..\assets"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\SkyMeshX CLI
DefaultGroupName=SkyMeshX
DisableProgramGroupPage=yes
LicenseFile={#ProjectRoot}\LICENSE
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\out
OutputBaseFilename=SkyMeshX-CLI-Setup-{#AppVersion}
SetupIconFile={#AssetsDir}\skymeshx_icon.ico
WizardImageFile={#AssetsDir}\wizard_large.bmp
WizardSmallImageFile={#AssetsDir}\wizard_small.bmp
WizardStyle=modern
WizardSizePercent=110
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}
ShowLanguageDialog=no
DisableWelcomePage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german";  MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "addtopath";    Description: "Add &skymeshx.exe to the system PATH"; \
    GroupDescription: "Integration:"; Flags: checkedonce
Name: "desktopicon";  Description: "Create a &desktop shortcut"; \
    GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "{#DistRoot}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ProjectRoot}\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ProjectRoot}\LICENSE";   DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "cmd.exe"; \
    Parameters: "/K ""{app}\{#AppExeName}"" --help"; \
    IconFilename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "cmd.exe"; \
    Parameters: "/K ""{app}\{#AppExeName}"" --help"; \
    IconFilename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
; Optional PATH entry for current-user install
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; \
    ValueData: "{olddata};{app}"; \
    Check: NeedsAddPath('{app}'); Tasks: addtopath

[Run]
Filename: "{app}\{#AppExeName}"; Parameters: "--help"; \
    Description: "Show {#AppName} help"; \
    Flags: postinstall skipifsilent runascurrentuser shellexec

[UninstallDelete]
Type: filesandordirs; Name: "{app}\_internal"

[Code]
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath) then
  begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;
