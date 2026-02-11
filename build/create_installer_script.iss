; 脚本为GPX Studio 生成
; 请先安装 Inno Setup: https://jrsoftware.org/isdl.php

#define MyAppName "GPX Studio"
#define MyAppVersion "2.0.10"
#define MyAppPublisher "PingWangWang"
#define MyAppURL "https://github.com/PingWangWang/GpxStudio"
#define MyAppExeName "GPXStudio_2.0.10.exe"
#define MyBuildDir "..\dist\GPXStudio_2.0.10"

[Code]
var
  OldInstallPath: string;
  OldDataPath: string;
  TempDataBackup: string;
  CustomLogFile: string;
  CustomLogLines: TStringList;
  OldVersionDetected: Boolean;
  UninstallOldVersion: Boolean;
  UninstallOldVersionPage: TInputOptionWizardPage;

// 自定义日志记录函数
procedure CustomLog(Msg: string);
begin
  // 同时记录到系统日志和自定义日志
  Log(Msg);
  if CustomLogLines <> nil then
  begin
    CustomLogLines.Add(Msg);
  end;
end;

// 保存自定义日志到文件
procedure SaveCustomLog();
begin
  if (CustomLogFile <> '') and (CustomLogLines <> nil) then
  begin
    try
      CustomLogLines.SaveToFile(CustomLogFile);
      CustomLog('✓ Custom log saved to: ' + CustomLogFile);
    except
      CustomLog('⚠️ Failed to save custom log');
    end;
  end;
end;

// 获取Windows位数
function GetWindowsBits(): string;
begin
  if IsWin64 then
    Result := '64'
  else
    Result := '32';
end;

// 获取Windows版本字符串
function GetWindowsVersionString(): string;
begin
  Result := 'Windows ' + GetWindowsBits() + '-bit';
end;

// 递归复制目录函数
function DirCopy(SourcePath, DestPath: string; Recursive: Boolean): Boolean;
var
  FindRec: TFindRec;
  SourceFilePath, DestFilePath: string;
begin
  Result := True;
  
  // 创建目标目录
  if not DirExists(DestPath) then
  begin
    if not CreateDir(DestPath) then
    begin
      CustomLog('Failed to create directory: ' + DestPath);
      Result := False;
      Exit;
    end;
  end;
  
  // 查找源目录中的所有文件和子目录
  if FindFirst(SourcePath + '\*', FindRec) then
  begin
    try
      repeat
        // 跳过 . �?..
        if (FindRec.Name <> '.') and (FindRec.Name <> '..') then
        begin
          SourceFilePath := SourcePath + '\' + FindRec.Name;
          DestFilePath := DestPath + '\' + FindRec.Name;
          
          // 如果是目录且需要递归
          if (FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY <> 0) and Recursive then
          begin
            if not DirCopy(SourceFilePath, DestFilePath, True) then
              Result := False;
          end
          // 如果是文件
          else if (FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY = 0) then
          begin
            if not FileCopy(SourceFilePath, DestFilePath, True) then
            begin
              CustomLog('Failed to copy file: ' + SourceFilePath + ' to ' + DestFilePath);
              Result := False;
            end;
          end;
        end;
      until not FindNext(FindRec);
    finally
      FindClose(FindRec);
    end;
  end;
end;

// 从安装路径中提取版本号
function ExtractVersionFromPath(Path: string): string;
var
  VersionDir: string;
begin
  Result := '';
  VersionDir := ExtractFileName(Path);
  // 如果是 v1.5.0 格式，提取版本号
  if (Length(VersionDir) > 1) and (Copy(VersionDir, 1, 1) = 'v') then
    Result := Copy(VersionDir, 2, Length(VersionDir) - 1);
end;

// 比较版本号函数（返回 1: version1 > version2, 0: 相等, -1: version1 < version2）
function CompareVersions(Version1, Version2: string): Integer;
var
  Parts1: TStringList;
  Parts2: TStringList;
  I: Integer;
  Num1, Num2: Integer;
  MinCount: Integer;
begin
  Result := 0;
  
  Parts1 := TStringList.Create;
  Parts2 := TStringList.Create;
  
  try
    // 分割版本号为数字部分
    StringChange(Version1, '.', #13#10);
    StringChange(Version2, '.', #13#10);
    
    Parts1.Text := Version1;
    Parts2.Text := Version2;
    
    // 计算最小长度
    MinCount := Parts1.Count;
    if Parts2.Count < MinCount then
      MinCount := Parts2.Count;
    
    // 比较每一部分
    for I := 0 to MinCount - 1 do
    begin
      Num1 := StrToIntDef(Parts1[I], 0);
      Num2 := StrToIntDef(Parts2[I], 0);
      
      if Num1 > Num2 then
      begin
        Result := 1;
        Exit;
      end
      else if Num1 < Num2 then
      begin
        Result := -1;
        Exit;
      end;
    end;
    
    // 如果前面的部分都相等，比较长度
    if Parts1.Count > Parts2.Count then
      Result := 1
    else if Parts1.Count < Parts2.Count then
      Result := -1;
  finally
    Parts1.Free;
    Parts2.Free;
  end;
end;

// 查找旧版本的安装目录（通过注册表和当前安装路径）
function GetOldInstallPath(): string;
var
  UninstallKey: string;
  InstallLocation: string;
  BaseDir: string;
  CurrentInstallDir: string;
  SearchRec: TFindRec;
  BaseDirs: array[0..2] of string;
  I: Integer;
  CurrentVersionDir: string;
begin
  Result := '';
  
  CustomLog('=== 开始查找旧版本安装目录 ===');
  
  // 获取当前要安装的目录（在向导页面显示后可用）
  CurrentInstallDir := WizardDirValue();
  if CurrentInstallDir <> '' then
  begin
    // 从当前安装路径提取基础目录（例如：D:\Program Files (x86)\GPX Studio\v2.0.0 -> D:\Program Files (x86)\GPX Studio）
    BaseDir := ExtractFileDir(CurrentInstallDir);
    CurrentVersionDir := ExtractFileName(CurrentInstallDir);
    
    CustomLog('当前安装目录: ' + CurrentInstallDir);
    CustomLog('提取的基础目录: ' + BaseDir);
    CustomLog('当前版本目录: ' + CurrentVersionDir);
    
    // 在基础目录下查找其他版本
    if DirExists(BaseDir) then
    begin
      CustomLog('基础目录存在，搜索旧版本...');
      if FindFirst(BaseDir + '\v*', SearchRec) then
      begin
        try
          repeat
            if (SearchRec.Attributes and FILE_ATTRIBUTE_DIRECTORY <> 0) and 
               (SearchRec.Name <> '.') and (SearchRec.Name <> '..') and
               (SearchRec.Name <> 'v{#MyAppVersion}') then  // 只排除新版本号
            begin
              Result := BaseDir + '\' + SearchRec.Name;
              CustomLog('✓ 找到旧版本: ' + Result);
              Exit;
            end;
          until not FindNext(SearchRec);
        finally
          FindClose(SearchRec);
        end;
      end
      else
      begin
        CustomLog('未找到版本目录');
      end;
    end
    else
    begin
      CustomLog('基础目录不存在: ' + BaseDir);
    end;
  end
  else
  begin
    CustomLog('当前安装目录不可用');
  end;
  
  // 方法2：从注册表读取旧版本的安装位置
  UninstallKey := 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1';
  
  CustomLog('从注册表搜索旧版本安装...');
  CustomLog('注册表键: ' + UninstallKey);
  
  // 尝试从 HKLM 读取（管理员安装）
  if RegQueryStringValue(HKLM, UninstallKey, 'InstallLocation', InstallLocation) then
  begin
    CustomLog('HKLM注册表找到: ' + InstallLocation);
    if DirExists(InstallLocation) then
    begin
      if InstallLocation <> CurrentInstallDir then
      begin
        Result := InstallLocation;
        CustomLog('✓ 使用注册表位置: ' + Result);
        Exit;
      end
      else
      begin
        CustomLog('注册表位置与当前安装目录相同，跳过');
      end;
    end
    else
    begin
      CustomLog('注册表位置不存在: ' + InstallLocation);
    end;
  end
  else
  begin
    CustomLog('HKLM注册表未找到安装信息');
  end;
  
  // 尝试从 HKCU 读取（当前用户安装）
  if RegQueryStringValue(HKCU, UninstallKey, 'InstallLocation', InstallLocation) then
  begin
    CustomLog('HKCU注册表找到: ' + InstallLocation);
    if DirExists(InstallLocation) then
    begin
      if InstallLocation <> CurrentInstallDir then
      begin
        Result := InstallLocation;
        CustomLog('✓ 使用注册表位置: ' + Result);
        Exit;
      end
      else
      begin
        CustomLog('注册表位置与当前安装目录相同，跳过');
      end;
    end
    else
    begin
      CustomLog('注册表位置不存在: ' + InstallLocation);
    end;
  end
  else
  begin
    CustomLog('HKCU注册表未找到安装信息');
  end;
  
  // 方法3：如果前面都没找到，检查标准安装位置
  CustomLog('检查标准安装位置...');
  BaseDirs[0] := ExpandConstant('{commonpf32}\GPX Studio');
  BaseDirs[1] := ExpandConstant('{commonpf}\GPX Studio');
  BaseDirs[2] := ExpandConstant('{userpf}\GPX Studio');
  
  for I := 0 to 2 do
  begin
    BaseDir := BaseDirs[I];
    CustomLog('检查: ' + BaseDir);
    if DirExists(BaseDir) then
    begin
      CustomLog('标准位置存在，搜索版本目录...');
      if FindFirst(BaseDir + '\v*', SearchRec) then
      begin
        try
          repeat
            if (SearchRec.Attributes and FILE_ATTRIBUTE_DIRECTORY <> 0) and 
               (SearchRec.Name <> '.') and (SearchRec.Name <> '..') and
               (SearchRec.Name <> 'v{#MyAppVersion}') then  // 只排除新版本号
            begin
              Result := BaseDir + '\' + SearchRec.Name;
              CustomLog('✓ 找到旧版本: ' + Result);
              Exit;
            end;
          until not FindNext(SearchRec);
        finally
          FindClose(SearchRec);
        end;
      end
      else
      begin
        CustomLog('标准位置未找到版本目录');
      end;
    end
    else
    begin
      CustomLog('标准位置不存在: ' + BaseDir);
    end;
  end;
  
  if Result = '' then
  begin
    CustomLog('未找到旧版本安装');
  end
  else
  begin
    CustomLog('找到旧版本: ' + Result);
  end;
  
  CustomLog('=== 查找旧版本安装目录完成 ===');
end;

function InitializeSetup(): Boolean;
var
  OldVersion: string;
  OldPath: string;
  StandardDirs: array[0..2] of string;
  SearchRec: TFindRec;
  I: Integer;
  UninstallKey: string;
  InstallLocation: string;
  BaseDir: string;
begin
  Result := True;
  OldVersionDetected := False;
  UninstallOldVersion := False;
  
  // 初始化自定义日志
  CustomLogLines := TStringList.Create;
  
  CustomLog('=== GPX Studio 安装程序初始化 ===');
  CustomLog('安装版本: {#MyAppVersion}');
  
  // 方法1：从自定义注册表位置读取旧版本位置（优先级最高）
  CustomLog('=== 开始查找旧版本安装目录 ===');
  CustomLog('方法1：检查自定义注册表位置...');
  UninstallKey := 'Software\GPXStudio';
  CustomLog('查找注册表: HKCU/' + UninstallKey);
  
  // 尝试从 HKCU 读取（自定义位置）
  if RegQueryStringValue(HKCU, UninstallKey, 'InstallLocation', InstallLocation) then
  begin
    CustomLog('注册表HKCU找到: ' + InstallLocation);
    if DirExists(InstallLocation) then
    begin
      // 检查是否是旧版本（不是当前版本）
      if Pos('v{#MyAppVersion}', InstallLocation) = 0 then
      begin
        OldInstallPath := InstallLocation;
        OldVersion := ExtractVersionFromPath(OldInstallPath);
        OldVersionDetected := True;
        CustomLog('检测到旧版本: ' + OldVersion + ' at ' + OldInstallPath);
      end
      else
      begin
        // 检测到同版本
        OldInstallPath := InstallLocation;
        OldVersion := ExtractVersionFromPath(OldInstallPath);
        OldVersionDetected := True;
        CustomLog('检测到同版本: ' + OldVersion + ' at ' + OldInstallPath);
      end;
    end;
  end;
  
  // 方法2：从标准卸载注册表位置读取
  if not OldVersionDetected then
  begin
    CustomLog('方法2：检查标准卸载注册表位置...');
    UninstallKey := 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1';
    CustomLog('查找注册表: ' + UninstallKey);
    
    // 尝试从 HKLM 读取（管理员安装）
    if RegQueryStringValue(HKLM, UninstallKey, 'InstallLocation', InstallLocation) then
    begin
      CustomLog('注册表HKLM找到: ' + InstallLocation);
      if DirExists(InstallLocation) then
      begin
        // 检查是否是旧版本（不是当前版本）
        if Pos('v{#MyAppVersion}', InstallLocation) = 0 then
        begin
          OldInstallPath := InstallLocation;
          OldVersion := ExtractVersionFromPath(OldInstallPath);
          OldVersionDetected := True;
          CustomLog('检测到旧版本: ' + OldVersion + ' at ' + OldInstallPath);
        end
        else
        begin
          // 检测到同版本
          OldInstallPath := InstallLocation;
          OldVersion := ExtractVersionFromPath(OldInstallPath);
          OldVersionDetected := True;
          CustomLog('检测到同版本: ' + OldVersion + ' at ' + OldInstallPath);
        end;
      end;
    end;
    
    // 尝试从 HKCU 读取（当前用户安装）
    if not OldVersionDetected then
    begin
      if RegQueryStringValue(HKCU, UninstallKey, 'InstallLocation', InstallLocation) then
      begin
        CustomLog('注册表HKCU找到: ' + InstallLocation);
        if DirExists(InstallLocation) then
        begin
          // 检查是否是旧版本（不是当前版本）
          if Pos('v{#MyAppVersion}', InstallLocation) = 0 then
          begin
            OldInstallPath := InstallLocation;
            OldVersion := ExtractVersionFromPath(OldInstallPath);
            OldVersionDetected := True;
            CustomLog('检测到旧版本: ' + OldVersion + ' at ' + OldInstallPath);
          end
          else
          begin
            // 检测到同版本
            OldInstallPath := InstallLocation;
            OldVersion := ExtractVersionFromPath(OldInstallPath);
            OldVersionDetected := True;
            CustomLog('检测到同版本: ' + OldVersion + ' at ' + OldInstallPath);
          end;
        end;
      end;
    end;
    
    // 尝试检查通用的注册表键格式
    if not OldVersionDetected then
    begin
      CustomLog('尝试检查通用注册表键格式...');
      // 检查不带_is1后缀的注册表键
      UninstallKey := 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}';
      CustomLog('检查注册表: ' + UninstallKey);
      
      // 尝试从 HKLM 读取
      if RegQueryStringValue(HKLM, UninstallKey, 'InstallLocation', InstallLocation) then
      begin
        CustomLog('注册表HKLM找到通用键: ' + InstallLocation);
        if DirExists(InstallLocation) then
        begin
          OldInstallPath := InstallLocation;
          OldVersion := ExtractVersionFromPath(OldInstallPath);
          OldVersionDetected := True;
          CustomLog('检测到旧版本: ' + OldVersion + ' at ' + OldInstallPath);
        end;
      end;
      
      // 尝试从 HKCU 读取
      if not OldVersionDetected then
      begin
        if RegQueryStringValue(HKCU, UninstallKey, 'InstallLocation', InstallLocation) then
        begin
          CustomLog('注册表HKCU找到通用键: ' + InstallLocation);
          if DirExists(InstallLocation) then
          begin
            OldInstallPath := InstallLocation;
            OldVersion := ExtractVersionFromPath(OldInstallPath);
            OldVersionDetected := True;
            CustomLog('检测到旧版本: ' + OldVersion + ' at ' + OldInstallPath);
          end;
        end;
      end;
    end;
  end;
  
  // 方法2：在标准位置查找旧版本
  if not OldVersionDetected then
  begin
    CustomLog('注册表未找到，搜索标准位置...');
    StandardDirs[0] := ExpandConstant('{commonpf32}\GPX Studio');
    StandardDirs[1] := ExpandConstant('{commonpf}\GPX Studio');
    StandardDirs[2] := ExpandConstant('{userpf}\GPX Studio');
    
    for I := 0 to 2 do
    begin
      CustomLog('检查: ' + StandardDirs[I]);
      if DirExists(StandardDirs[I]) then
      begin
        if FindFirst(StandardDirs[I] + '\v*', SearchRec) then
        begin
          try
            repeat
              if (SearchRec.Attributes and FILE_ATTRIBUTE_DIRECTORY <> 0) and 
                 (SearchRec.Name <> '.') and (SearchRec.Name <> '..') then
              begin
                OldPath := StandardDirs[I] + '\' + SearchRec.Name;
                OldVersion := ExtractVersionFromPath(OldPath);
                OldInstallPath := OldPath;
                OldVersionDetected := True;
                
                CustomLog('检测到版本: ' + OldVersion + ' at ' + OldPath);
                
                Break;
              end;
            until not FindNext(SearchRec);
          finally
            FindClose(SearchRec);
          end;
        end;
        
        if OldVersionDetected then
          Break;
      end;
    end;
  end;
  
  // 方法3：检查常见的安装位置
  if not OldVersionDetected then
  begin
    CustomLog('检查常见安装位置...');
    // 检查 C:\Program Files (x86)\GPX Studio
    BaseDir := 'C:\Program Files (x86)\GPX Studio';
    if DirExists(BaseDir) then
    begin
      if FindFirst(BaseDir + '\v*', SearchRec) then
      begin
        try
          repeat
            if (SearchRec.Attributes and FILE_ATTRIBUTE_DIRECTORY <> 0) and 
               (SearchRec.Name <> '.') and (SearchRec.Name <> '..') then
            begin
              OldPath := BaseDir + '\' + SearchRec.Name;
              OldVersion := ExtractVersionFromPath(OldPath);
              OldInstallPath := OldPath;
              OldVersionDetected := True;
              
              CustomLog('检测到版本: ' + OldVersion + ' at ' + OldPath);
              
              Break;
            end;
          until not FindNext(SearchRec);
        finally
          FindClose(SearchRec);
        end;
      end;
    end;
  end;
  
  if not OldVersionDetected then
    CustomLog('未找到旧版本安装');
end;

// 获取默认安装目录（如果有旧版本则使用旧版本的基础目录）
function GetDefaultDirName(Param: string): string;
var
  BaseDir: string;
  TempPath: string;
  UninstallKey: string;
  InstallLocation: string;
  StandardDirs: array[0..2] of string;
  SearchRec: TFindRec;
  I: Integer;
  OldPath: string;
  NewPath: string;
begin
  CustomLog('=== GetDefaultDirName 函数开始执行 ===');
  
  // 首先检查自定义注册表位置（优先级最高）
  UninstallKey := 'Software\GPXStudio';
  CustomLog('1. 检查注册表位置: HKCU\\' + UninstallKey);
  
  if RegQueryStringValue(HKCU, UninstallKey, 'InstallLocation', InstallLocation) then
  begin
    CustomLog('   注册表找到安装位置: ' + InstallLocation);
    if DirExists(InstallLocation) then
    begin
      CustomLog('   安装位置目录存在');
      
      // 提取根目录（包含 GPX Studio 的目录）
      TempPath := InstallLocation;
      CustomLog('   旧版本完整路径: ' + TempPath);
      
      // 移除末尾的反斜杠
      while (Length(TempPath) > 0) and (TempPath[Length(TempPath)] = '\') do
        Delete(TempPath, Length(TempPath), 1);
      
      // 查找 \v 字符串，提取基础目录
      I := Pos('\v', TempPath);
      if I > 0 then
      begin
        // 找到 \v 字符串，提取基础目录
        BaseDir := Copy(TempPath, 1, I - 1);
        CustomLog('   提取基础目录: ' + BaseDir);
        
        // 构建新版本路径
        NewPath := BaseDir + '\v{#MyAppVersion}';
        CustomLog('   构建新版本路径: ' + NewPath);
      end
      else
      begin
        // 没有找到 \v 字符串，使用整个路径并添加版本目录
        BaseDir := TempPath;
        CustomLog('   使用整个路径作为基础目录: ' + BaseDir);
        
        // 构建新版本路径
        NewPath := BaseDir + '\v{#MyAppVersion}';
        CustomLog('   构建新版本路径: ' + NewPath);
      end;
      
      Result := NewPath;
      CustomLog('   返回新版本路径: ' + Result);
      CustomLog('=== GetDefaultDirName 函数执行完成 ===');
      Exit;
    end
    else
    begin
      CustomLog('   安装位置目录不存在');
    end;
  end
  else
  begin
    CustomLog('   注册表未找到安装位置');
  end;
  
  // 检查标准安装位置
  CustomLog('2. 检查标准安装位置...');
  StandardDirs[0] := ExpandConstant('{commonpf32}\GPX Studio');
  StandardDirs[1] := ExpandConstant('{commonpf}\GPX Studio');
  StandardDirs[2] := ExpandConstant('{userpf}\GPX Studio');
  
  for I := 0 to 2 do
  begin
    BaseDir := StandardDirs[I];
    CustomLog('   检查标准位置: ' + BaseDir);
    if DirExists(BaseDir) then
    begin
      CustomLog('   标准位置目录存在');
      
      // 构建新版本路径
      NewPath := BaseDir + '\v{#MyAppVersion}';
      CustomLog('   构建新版本路径: ' + NewPath);
      
      Result := NewPath;
      CustomLog('   返回新版本路径: ' + Result);
      CustomLog('=== GetDefaultDirName 函数执行完成 ===');
      Exit;
    end
    else
    begin
      CustomLog('   标准位置目录不存在');
    end;
  end;
  
  // 检查 D 盘的安装位置（根据用户的安装日志）
  CustomLog('3. 检查 D 盘安装位置...');
  BaseDir := 'D:\Program Files (x86)\GPX Studio';
  CustomLog('   检查 D 盘位置: ' + BaseDir);
  if DirExists(BaseDir) then
  begin
    CustomLog('   D 盘位置目录存在');
    
    // 构建新版本路径
    NewPath := BaseDir + '\v{#MyAppVersion}';
    CustomLog('   构建新版本路径: ' + NewPath);
    
    Result := NewPath;
    CustomLog('   返回新版本路径: ' + Result);
    CustomLog('=== GetDefaultDirName 函数执行完成 ===');
    Exit;
  end
  else
  begin
    CustomLog('   D 盘位置目录不存在');
  end;
  
  // 首次安装，使用默认路径
  CustomLog('4. 首次安装，使用默认路径');
  NewPath := ExpandConstant('{autopf}\{#MyAppName}\v{#MyAppVersion}');
  CustomLog('   构建首次安装路径: ' + NewPath);
  
  Result := NewPath;
  CustomLog('   返回首次安装路径: ' + Result);
  CustomLog('=== GetDefaultDirName 函数执行完成 ===');
end;

// 创建自定义页面询问是否卸载旧版本
procedure InitializeWizard();
var
  OldVersion: string;
  VersionCompareResult: Integer;
  PageTitle: string;
  PageDescription: string;
  OptionText: string;
  BaseDir: string;
  TempPath: string;
  I: Integer;
  NewPath: string;
begin
  if OldVersionDetected then
  begin
    OldVersion := ExtractVersionFromPath(OldInstallPath);
    VersionCompareResult := CompareVersions('{#MyAppVersion}', OldVersion);
    
    // 根据版本比较结果设置不同的提示信息
    if VersionCompareResult > 0 then
    begin
      // 升级
      PageTitle := '检测到旧版本 - 准备升级';
      PageDescription := '安装程序检测到您已经安装了 GPX Studio ' + OldVersion + '。' + #13#10 +
        '安装路径：' + OldInstallPath + #13#10 + #13#10 +
        '您正在安装的版本是 GPX Studio {#MyAppVersion}，这是一个升级。' + #13#10 +
        '安装程序将自动备份您的数据，卸载旧版本，然后安装新版本。';
      OptionText := '卸载旧版本 ' + OldVersion + ' 并升级到 {#MyAppVersion}（推荐）';
    end
    else if VersionCompareResult < 0 then
    begin
      // 降级
      PageTitle := '检测到新版本 - 准备降级';
      PageDescription := '安装程序检测到您已经安装了 GPX Studio ' + OldVersion + '。' + #13#10 +
        '安装路径：' + OldInstallPath + #13#10 + #13#10 +
        '您正在安装的版本是 GPX Studio {#MyAppVersion}，这是一个降级。' + #13#10 +
        '安装程序将自动备份您的数据，卸载现有版本，然后安装此版本。';
      OptionText := '卸载现有版本 ' + OldVersion + ' 并降级到 {#MyAppVersion}';
    end
    else
    begin
      // 同版本覆盖
      PageTitle := '检测到同版本 - 准备覆盖';
      PageDescription := '安装程序检测到您已经安装了 GPX Studio ' + OldVersion + '。' + #13#10 +
        '安装路径：' + OldInstallPath + #13#10 + #13#10 +
        '您正在安装的是相同版本。安装程序将覆盖现有安装。' + #13#10 +
        '您的数据将被自动备份和恢复。';
      OptionText := '卸载现有版本并重新安装 {#MyAppVersion}';
    end;
    
    // 创建自定义选项页面
    UninstallOldVersionPage := CreateInputOptionPage(wpSelectDir,
      PageTitle, '发现已安装的 GPX Studio',
      PageDescription,
      False, False);
    
    // 添加选项
    UninstallOldVersionPage.Add(OptionText);
    
    // 默认勾选
    UninstallOldVersionPage.Values[0] := True;
  end;
  
  // 手动设置默认安装目录
  if OldVersionDetected then
  begin
    // 从旧版本路径提取基础目录，构建新版本路径
    TempPath := OldInstallPath;
    // 移除末尾的反斜杠
    while (Length(TempPath) > 0) and (TempPath[Length(TempPath)] = '\') do
      Delete(TempPath, Length(TempPath), 1);
    
    // 查找 \v 字符串，提取基础目录
    I := Pos('\v', TempPath);
    if I > 0 then
    begin
      // 找到 \v 字符串，提取基础目录
      BaseDir := Copy(TempPath, 1, I - 1);
      // 构建新版本路径
      NewPath := BaseDir + '\v{#MyAppVersion}';
    end
    else
    begin
      // 没有找到 \v 字符串，使用整个路径并添加版本目录
      BaseDir := TempPath;
      // 构建新版本路径
      NewPath := BaseDir + '\v{#MyAppVersion}';
    end;
    
    // 设置默认安装目录
    WizardForm.DirEdit.Text := NewPath;
    Log('手动设置默认安装目录: ' + NewPath);
  end;
  
  // 调整向导窗口大小
  WizardForm.ClientHeight := 350; // 减小高度
  Log('调整向导窗口高度为: ' + IntToStr(WizardForm.ClientHeight));
end;

// 在用户点击Next时保存选择
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  
  if OldVersionDetected and (CurPageID = UninstallOldVersionPage.ID) then
  begin
    UninstallOldVersion := UninstallOldVersionPage.Values[0];
    if UninstallOldVersion then
      CustomLog('用户选择卸载旧版本')
    else
      CustomLog('用户选择保留旧版本');
  end;
end;

// 在安装开始前备份数据并卸载旧版本
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  UninstallExe: string;
  UninstallParams: string;
  NewDataPath: string;
  DebugMsg: string;
  BaseDir: string;
  UninstallKey: string;
  InstallLocation: string;
begin
  // ========== 第一步：安装前备份数据并卸载旧版本==========
  if CurStep = ssInstall then
  begin
    // 设置自定义日志文件路径（在安装目录的父目录）
    BaseDir := ExpandConstant('{app}');
    BaseDir := ExtractFileDir(BaseDir);  // 获取父目录（GPX Studio目录）
    CustomLogFile := BaseDir + '\install_log_' + '{#MyAppVersion}' + '.txt';
    CustomLog('日志文件将保存到: ' + CustomLogFile);
    CustomLog('当前安装目录: ' + ExpandConstant('{app}'));
    CustomLog('安装版本: {#MyAppVersion}');
    CustomLog('应用ID: {#SetupSetting("AppId")}');
    
    // 记录系统信息
    CustomLog('系统信息: ' + GetWindowsVersionString());
    if IsAdminInstallMode then
      CustomLog('是否管理员权限: True')
    else
      CustomLog('是否管理员权限: False');
    
    // 如果没有检测到旧版本，或用户选择不卸载，则跳过
    if not OldVersionDetected then
    begin
      CustomLog('未检测到旧版本，跳过卸载流程');
      Exit;
    end;
    
    if not UninstallOldVersion then
    begin
      CustomLog('用户选择不卸载旧版本，跳过卸载流程');
      Exit;
    end;
    
    // 用户选择卸载旧版本
    if OldInstallPath <> '' then
    begin
      CustomLog('开始卸载旧版本: ' + OldInstallPath);
      // 备份旧版本的数据目录
      OldDataPath := OldInstallPath + '\GPXStudioData';
      if DirExists(OldDataPath) then
      begin
        // 创建临时备份目录
        TempDataBackup := ExpandConstant('{tmp}\GPXStudioData_Backup');
        CustomLog('Backing up data from: ' + OldDataPath + ' to ' + TempDataBackup);
        
        // 复制整个数据目录到临时位置
        if DirCopy(OldDataPath, TempDataBackup, True) then
          CustomLog('✓ Data backup successful')
        else
          CustomLog('⚠️ Data backup failed, but continuing installation');
      end
      else
      begin
        CustomLog('No data directory found in old installation');
      end;
      
      // 卸载旧版本
      CustomLog('Attempting to uninstall old version from: ' + OldInstallPath);
      UninstallExe := OldInstallPath + '\unins000.exe';
      
      if FileExists(UninstallExe) then
      begin
        CustomLog('Found uninstaller: ' + UninstallExe);
        // 使用 VERYSILENT 参数，完全静默卸载，不显示任何窗口
        UninstallParams := '/VERYSILENT /NORESTART /SUPPRESSMSGBOXES';
        
        CustomLog('Executing: ' + UninstallExe + ' ' + UninstallParams);
        if Exec(UninstallExe, UninstallParams, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
        begin
          CustomLog('✓ Old version uninstalled successfully. Result code: ' + IntToStr(ResultCode));
          Sleep(1000);
          
          // 验证旧版本注册表是否已删除
          UninstallKey := 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1';
          if (not RegQueryStringValue(HKLM, UninstallKey, 'InstallLocation', InstallLocation)) and 
             (not RegQueryStringValue(HKCU, UninstallKey, 'InstallLocation', InstallLocation)) then
          begin
            CustomLog('✓ Old version registry keys removed');
          end
          else
          begin
            CustomLog('⚠️ Old version registry keys may still exist');
          end;
        end
        else
        begin
          CustomLog('⚠️ Failed to uninstall old version. Error code: ' + IntToStr(ResultCode));
          MsgBox('卸载旧版本失败（错误代码：' + IntToStr(ResultCode) + '）' + #13#10 + '将尝试继续安装...', mbError, MB_OK);
        end;
      end
      else
      begin
        CustomLog('⚠️ Uninstaller not found: ' + UninstallExe);
        CustomLog('Will manually clean up old directory after installation');
      end;
      
      // 清理旧版本的快捷方式（所有可能的版本号）
      DeleteFile(ExpandConstant('{autoprograms}\GPX Studio.lnk'));
      DeleteFile(ExpandConstant('{autodesktop}\GPX Studio.lnk'));
      DeleteFile(ExpandConstant('{autodesktop}\GPX Studio 1.0.0.lnk'));
      DeleteFile(ExpandConstant('{autodesktop}\GPX Studio 1.5.0.lnk'));
      CustomLog('Old shortcuts cleaned up');
    end
    else
    begin
      CustomLog('Old version not found (may be first install)');
    end;
  end;
  
  // ========== Step 2: Restore data after installation ==========
  if CurStep = ssPostInstall then
  begin
    CustomLog('Post-install: Restoring data and cleaning up...');
    
    // 恢复备份的数据到新版本目录
    if TempDataBackup <> '' then
    begin
      if DirExists(TempDataBackup) then
      begin
        NewDataPath := ExpandConstant('{app}\GPXStudioData');
        CustomLog('Restoring data from: ' + TempDataBackup + ' to ' + NewDataPath);
        
        // 如果新目录已存在，先删除（使用全新的备份数据）
        if DirExists(NewDataPath) then
        begin
          CustomLog('New data directory already exists, will merge with backup');
          // 不删除，而是合并，让备份数据覆盖新数据
        end;
        
        // 复制备份数据到新目录
        if DirCopy(TempDataBackup, NewDataPath, True) then
        begin
          CustomLog('✓ Data restored successfully');
          
          // 清理临时备份
          if DelTree(TempDataBackup, True, True, True) then
            CustomLog('Temp backup cleaned up')
          else
            CustomLog('Failed to clean temp backup (not critical)');
        end
        else
        begin
          CustomLog('⚠️ Failed to restore data');
        end;
      end;
    end;
    
    // 删除旧版本目录（如果还存在）
    if OldInstallPath <> '' then
    begin
      if DirExists(OldInstallPath) and (OldInstallPath <> ExpandConstant('{app}')) then
      begin
        CustomLog('Cleaning up old installation directory: ' + OldInstallPath);
        
        if DelTree(OldInstallPath, True, True, True) then
          CustomLog('✓ Old installation directory deleted')
        else
          CustomLog('⚠️ Failed to delete old installation directory (may still be in use)');
      end;
    end;
    
    CustomLog('Post-install cleanup completed');
    
    // 记录新版本注册表信息
    CustomLog('=== 新版本注册表信息 ===');
    UninstallKey := 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1';
    CustomLog('新版本注册表键: ' + UninstallKey);
    CustomLog('新版本安装路径: ' + ExpandConstant('{app}'));
    CustomLog('程序可执行文件: ' + ExpandConstant('{app}\{#MyAppExeName}'));
    
    // 写入自定义注册表位置（用于版本检测）
    CustomLog('写入自定义注册表位置...');
    RegWriteStringValue(HKCU, 'Software\GPXStudio', 'InstallLocation', ExpandConstant('{app}'));
    RegWriteStringValue(HKCU, 'Software\GPXStudio', 'Version', '{#MyAppVersion}');
    CustomLog('自定义注册表位置写入完成: HKCU\\Software\\GPXStudio');
    
    // 保存自定义日志到安装目录
    SaveCustomLog();
    CustomLog('所有日志已保存到: ' + CustomLogFile);
  end;
end;

// 卸载过程中的步骤处理
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  InstallLocation: string;
  BaseDir: string;
  TempPath: string;
  I: Integer;
  SearchRec: TFindRec;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // 卸载完成后执行清理工作
    Log('=== 开始卸载后清理工作 ===');
    
    // 首先从注册表读取安装位置
    Log('从注册表读取安装位置...');
    if RegQueryStringValue(HKCU, 'Software\GPXStudio', 'InstallLocation', InstallLocation) then
    begin
      Log('注册表中记录的安装位置: ' + InstallLocation);
      
      // 删除安装目录
      if DirExists(InstallLocation) then
      begin
        Log('删除安装目录: ' + InstallLocation);
        DelTree(InstallLocation, True, True, True);
      end;
      
      // 尝试删除父目录（如果为空）
      BaseDir := InstallLocation;
      // 移除末尾的反斜杠
      while (Length(BaseDir) > 0) and (BaseDir[Length(BaseDir)] = '\') do
        Delete(BaseDir, Length(BaseDir), 1);
      
      // 查找最后一个反斜杠，提取父目录
      I := Length(BaseDir);
      while (I > 0) and (BaseDir[I] <> '\') do
        Dec(I);
      
      if I > 0 then
      begin
        BaseDir := Copy(BaseDir, 1, I - 1);
        Log('尝试删除父目录: ' + BaseDir);
        
        // 检查父目录是否为空
        if not FindFirst(BaseDir + '\*', SearchRec) then
        begin
          // 目录为空，删除
          Log('父目录为空，删除: ' + BaseDir);
          RemoveDir(BaseDir);
        end
        else
        begin
          // 目录不为空，不删除
          Log('父目录不为空，跳过删除');
          FindClose(SearchRec);
        end;
      end;
    end
    else
    begin
      Log('注册表中未找到安装位置');
    end;
    
    // 删除自定义注册表项
    Log('删除自定义注册表项...');
    RegDeleteValue(HKCU, 'Software\GPXStudio', 'InstallLocation');
    RegDeleteValue(HKCU, 'Software\GPXStudio', 'Version');
    // 尝试删除整个注册表键（如果为空）
    RegDeleteKeyIfEmpty(HKCU, 'Software\GPXStudio');
    Log('自定义注册表项删除完成');
    
    Log('=== 卸载后清理工作完成 ===');
  end;
end;

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{C626F80D-1234-4567-890A-BCDEF0123456}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={code:GetDefaultDirName}
DisableProgramGroupPage=no
DisableDirPage=no
; 启用详细日志记录
SetupLogging=yes
; Uncomment the following line to run in non administrative install mode (install for current user only.)
;PrivilegesRequired=lowest
; 当目录已存在时，询问用户
DirExistsWarning=yes
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
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; 主要的可执行文件
Source: "{#MyBuildDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; 包含整个目录（递归）
Source: "{#MyBuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
; 开始菜单快捷方式（不含版本号，始终指向最新版本）
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "GPX Route Planning Tool"
; 桌面快捷方式（包含版本号，便于区分不同版本）
Name: "{autodesktop}\{#MyAppName} {#MyAppVersion}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "GPX Route Planning Tool v{#MyAppVersion}"

[Run]
; 安装完成后自动启动程序
; nowait: 不等待程序退出
; postinstall: 在安装完成页显示"运行程序"选项
; skipifsilent: 静默安装时跳过（但我们希望自动更新时也启动）
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall
