; 脚本由 GPX Studio 生成
; 请先安装 Inno Setup: https://jrsoftware.org/isdl.php

#define MyAppName "GPX Studio"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "PingWangWang"
#define MyAppURL "https://github.com/PingWangWang/GpxStudio"
#define MyAppExeName "GPXStudio_1.0.0.exe"
#define MyBuildDir "..\dist\GPXStudio_1.0.0"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{C626F80D-1234-4567-890A-BCDEF0123456}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; Uncomment the following line to run in non administrative install mode (install for current user only.)
;PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=GPXStudio_Setup_v{#MyAppVersion}
SetupIconFile=..\res\GPXStudio.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
; 使用默认语言（英文），以避免找不到中文语言文件的错误
Name: "english"; MessagesFile: "compiler:Default.isl"
; 如果确定安装了中文语言包，可以取消下面的注释并注释掉上面那行
; Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 主要的可执行文件
Source: "{#MyBuildDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; 包含整个目录（递归）
Source: "{#MyBuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
