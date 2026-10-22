; Script de Inno Setup 6 para InstalarTorreLoca.exe
; Compilar con:  "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\TorreLoca.iss
; (build.bat lo hace automaticamente despues de generar dist\TorreLoca.exe)

#define AppName "TORRE LOCA"
#define AppVersion "1.0.0"

[Setup]
AppId={{6F1D7A52-3B8E-4C0A-9E61-7A2B5C94D0E1}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Desafios Locos
DefaultDirName={autopf}\TorreLoca
DefaultGroupName=Desafios Locos
OutputDir=..\dist
OutputBaseFilename=InstalarTorreLoca
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\TorreLoca.exe
DisableProgramGroupPage=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "..\dist\TorreLoca.exe"; DestDir: "{app}"; Flags: ignoreversion
; Si colocas un demo.mp4 en assets\ antes de compilar, se instala junto al juego
Source: "..\assets\demo.mp4"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\TORRE LOCA"; Filename: "{app}\TorreLoca.exe"
Name: "{group}\Desinstalar TORRE LOCA"; Filename: "{uninstallexe}"
Name: "{autodesktop}\TORRE LOCA"; Filename: "{app}\TorreLoca.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\TorreLoca.exe"; Description: "Iniciar TORRE LOCA"; Flags: nowait postinstall skipifsilent
