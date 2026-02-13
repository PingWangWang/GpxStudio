; GPX Studio NSIS 安装脚本
; 请先安装 NSIS: https://nsis.sourceforge.io/Download

; 定义安装程序名称和版本
!define PRODUCT_NAME "GPX Studio"
!define PRODUCT_VERSION "2.0.32"
!define PRODUCT_PUBLISHER "PingWangWang"
!define PRODUCT_URL "https://github.com/PingWangWang/GpxStudio"
!define PRODUCT_ICON "..\res\GPXStudio.ico"
!define PRODUCT_EXE "GPXStudio_2.0.32.exe"
!define BUILD_DIR "..\dist\GPXStudio_2.0.32"

; 定义注册表路径
!define REG_ROOT "HKCU"
!define REG_PATH "Software\GPXStudio"

; 设置安装程序名称
Name "${PRODUCT_NAME} v${PRODUCT_VERSION}"

; 包含必要的库
!include "MUI2.nsh"
!include "LogicLib.nsh"

; 压缩设置（必须在MUI设置之前）
SetCompressor Zlib

; 安装程序设置
OutFile "..\dist\GPXStudio_Setup_${PRODUCT_VERSION}.exe"
Icon "${PRODUCT_ICON}"
UninstallIcon "${PRODUCT_ICON}"

; 设置 MUI 安装向导图标
!define MUI_ICON "${PRODUCT_ICON}"
!define MUI_UNICON "${PRODUCT_ICON}"

; 设置安装目录
InstallDir "$PROGRAMFILES\GPX Studio\v${PRODUCT_VERSION}"
InstallDirRegKey ${REG_ROOT} "${REG_PATH}" "InstallLocation"

; MUI 页面设置
!define MUI_PAGE_CUSTOMFUNCTION_SHOW DirectoryPageShow
!define MUI_PAGE_CUSTOMFUNCTION_LEAVE DirectoryPageLeave
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

; 结束页面设置
; 提供“运行程序”的勾选项（默认勾选）
!define MUI_FINISHPAGE_RUN "$INSTDIR\${PRODUCT_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "运行 GPX Studio v${PRODUCT_VERSION}"
!insertmacro MUI_PAGE_FINISH

; 设置现代UI语言为中文
!insertmacro MUI_LANGUAGE "SimpChinese"

; 定义变量
Var OLD_VERSION
Var OLD_INSTALL_PATH
Var DATA_MIGRATED
Var PROCESS_RUNNING
Var LOG_FILE
Var LOG_HANDLE
Var PATH_PROCESSED

; 初始化函数
Function .onInit
  ; 初始化调试日志
  StrCpy $0 "$TEMP\gpx_setup_debug.log"
  FileOpen $1 $0 w
  FileWrite $1 "--- Installer Init Start ---$\r$\n"
  FileWrite $1 "Build Time: ${__TIMESTAMP__}$\r$\n"
  FileClose $1
  
  Push "Function .onInit executed"
  Call WriteDebugLog
  
  ; === 修正从注册表读取的旧版本路径 ===
  ; InstallDirRegKey 会优先读取旧版本路径 (如 ...\v2.0.18)
  ; 此处逻辑将其更新为当前版本路径 (如 ...\v2.0.19)
  
  StrCpy $R0 $INSTDIR
  StrLen $R1 $R0
  
  ${Do}
    IntOp $R1 $R1 - 1
    ${If} $R1 < 0
      ${Break}
    ${EndIf}
    StrCpy $R2 $R0 1 $R1
    ${If} $R2 == "\"
       Goto found_slash
    ${EndIf}
  ${Loop}
  Goto done_check
  
  found_slash:
    ; $R1 是反斜杠索引，获取父目录 (例如 ...\GPX Studio)
    StrCpy $R3 $R0 $R1
    
    ; 检查父目录是否以 "\GPX Studio" 结尾
    StrLen $R4 "\GPX Studio"
    StrCpy $R5 $R3 "" -$R4
    ${If} $R5 == "\GPX Studio"
      ; 确认父目录是 GPX Studio，重置 INSTDIR 为新版本
      StrCpy $INSTDIR "$R3\v${PRODUCT_VERSION}"
      
      Push "Detected old version registry path: $R0"
      Call WriteDebugLog
      Push "Auto-updated INSTDIR to new version: $INSTDIR"
      Call WriteDebugLog
    ${EndIf}
    
  done_check:
  ; ==================================
  
  ; 初始化路径处理标记
  StrCpy $PATH_PROCESSED "0"
FunctionEnd

Function WriteDebugLog
  Exch $R0 ; log message
  Push $R1
  Push $R2
  
  StrCpy $R1 "$TEMP\gpx_setup_debug.log"
  FileOpen $R2 $R1 a
  FileSeek $R2 0 END
  FileWrite $R2 "$R0$\r$\n"
  FileClose $R2
  
  Pop $R2
  Pop $R1
  Pop $R0
FunctionEnd

; 目录页面显示时的回调
Function DirectoryPageShow
  Push "--> Enter DirectoryPageShow"
  Call WriteDebugLog
  Push "    Current INSTDIR: $INSTDIR"
  Call WriteDebugLog
FunctionEnd

; 目录页面路径验证回调（用户修改路径时实时触发）
Function .onVerifyInstDir
  ; 定义 WM_SETTEXT
  !ifndef WM_SETTEXT
    !define WM_SETTEXT 0x000C
  !endif
  
  ; 记录校验开始
  ; 注意：这个函数调用频率极高，每输入一个字符都会触发
  ; 为了避免日志爆炸，我们尽量精简，但在关键修正点详细记录
  
  ; 检查路径是否以 \v版本号 结尾
  StrLen $0 "\v${PRODUCT_VERSION}"
  StrCpy $1 $INSTDIR "" -$0
  
  ${If} $1 == "\v${PRODUCT_VERSION}"
    ; 检查是否以 \GPX Studio\v版本号 结尾
    StrLen $2 "\GPX Studio\v${PRODUCT_VERSION}"
    StrCpy $3 $INSTDIR "" -$2
    
    ${If} $3 != "\GPX Studio\v${PRODUCT_VERSION}"
      ; 路径不对，开始修正
      Push "Detect path issue in .onVerifyInstDir"
      Call WriteDebugLog
      Push "    Current bad path: $INSTDIR"
      Call WriteDebugLog
      
      ; 1. 更新内部变量
      StrCpy $4 $INSTDIR -$0 ; 去除 \v版本号
      StrCpy $INSTDIR "$4\GPX Studio\v${PRODUCT_VERSION}"
      
      Push "    Internal var updated to: $INSTDIR"
      Call WriteDebugLog
      
      ; 2. 更新 UI 显示
      ; 查找内部对话框句柄 (#32770 类是标准对话框类名)
      FindWindow $0 "#32770" "" $HWNDPARENT
      ; 获取目录输入框控件 (ID 1019 是 NSIS 目录选择页面的标准输入框ID)
      GetDlgItem $1 $0 1019
      ; 发送消息更新文本
      SendMessage $1 ${WM_SETTEXT} 0 "STR:$INSTDIR"
      
      ; 记录这次修正
      Push "    UI visual update triggered via SendMessage"
      Call WriteDebugLog
    ${EndIf}
  ${EndIf}
FunctionEnd

; 目录页面离开回调（用户点击安装后触发）
Function DirectoryPageLeave
  ; 不在这里修改路径，仅仅记录日志
  Push "--> Enter DirectoryPageLeave"
  Call WriteDebugLog
  Push "    Confirming INSTDIR: $INSTDIR"
  Call WriteDebugLog
  
  ; === 检查旧版本并请求确认 ===
  ReadRegStr $0 ${REG_ROOT} "${REG_PATH}" "Version"
  ${If} $0 != ""
  ${AndIf} $0 != "${PRODUCT_VERSION}"
    ReadRegStr $1 ${REG_ROOT} "${REG_PATH}" "InstallLocation"
    
    MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "检测到系统中已安装旧版本 (v$0)。$\r$\n$\r$\n旧版本位置: $1$\r$\n新版本位置: $INSTDIR$\r$\n$\r$\n点击“是”：继续安装。安装过程将自动迁移数据并卸载旧版本。$\r$\n点击“否”：停止安装。" IDYES continue_install
    
    ; 用户选择停止
    Push "User chose to stop installation due to old version."
    Call WriteDebugLog
    Abort
    
    continue_install:
    Push "User chose to continue installation."
    Call WriteDebugLog
  ${EndIf}
  ; ==============================
FunctionEnd

; 定义路径修正函数，将在安装开始时调用
Function CorrectInstallPath
  Push "--> Enter CorrectInstallPath"
  Call WriteDebugLog
  
  Push $R0
  Push $R1
  Push $R2
  Push $R3
  
  StrCpy $R0 $INSTDIR
  Push "    Initial Path: $R0"
  Call WriteDebugLog
  
  ; 1. 去除末尾可能存在的反斜杠
  StrCpy $R1 $R0 "" -1
  ${If} $R1 == "\"
    StrCpy $R0 $R0 -1
    Push "    Removed trailing backslash. Now: $R0"
    Call WriteDebugLog
  ${EndIf}
  
  ; 2. 检查并移除末尾的 \v版本号
  StrLen $R1 "\v${PRODUCT_VERSION}"
  StrCpy $R2 $R0 "" -$R1
  ${If} $R2 == "\v${PRODUCT_VERSION}"
    StrCpy $R0 $R0 -$R1
    Push "    Removed version suffix. Now: $R0"
    Call WriteDebugLog
  ${EndIf}
  
  ; 3. 检查并移除末尾的 \GPX Studio
  StrLen $R1 "\GPX Studio"
  StrCpy $R2 $R0 "" -$R1
  ${If} $R2 == "\GPX Studio"
    StrCpy $R0 $R0 -$R1
    Push "    Removed 'GPX Studio' suffix. Now: $R0"
    Call WriteDebugLog
  ${EndIf}
  
  ; 4. 重建标准路径
  StrCpy $INSTDIR "$R0\GPX Studio\v${PRODUCT_VERSION}"
  Push "    Final Rebuilt Path: $INSTDIR"
  Call WriteDebugLog
  
  Pop $R3
  Pop $R2
  Pop $R1
  Pop $R0
  
  Push "<-- Exit CorrectInstallPath"
  Call WriteDebugLog
FunctionEnd


; 获取路径的最后一级目录名
Function GetLastDirName
  Exch $R0
  Push $R1
  Push $R2
  
  StrCpy $R1 ""
  StrLen $R2 $R0
  
  IntOp $R2 $R2 - 1
  ${If} $R2 < 0
    StrCpy $R0 ""
    Goto done
  ${EndIf}
  
  ; 去掉末尾的反斜杠
  StrCpy $R1 $R0 1 $R2
  ${If} $R1 == "\"
    StrCpy $R0 $R0 $R2
    StrLen $R2 $R0
    IntOp $R2 $R2 - 1
  ${EndIf}
  
  ${DoWhile} $R2 >= 0
    StrCpy $R1 $R0 1 $R2
    ${If} $R1 == "\"
      IntOp $R2 $R2 + 1
      StrCpy $R0 $R0 "" $R2
      ${Break}
    ${EndIf}
    IntOp $R2 $R2 - 1
  ${Loop}
  
  done:
  
  Pop $R2
  Pop $R1
  Exch $R0
FunctionEnd



Section "Main Section" SEC01
  ; 在所有操作开始前，强制修正路径
  Call CorrectInstallPath

  ; 获取 InstallDir 的上一级目录作为日志基础路径
  Push $INSTDIR
  Call GetLastDirName
  Pop $0 ; 应该是 v2.0.18，丢弃
  
  ; 这里我们需要真正的上一级，GetLastDirName 只是获取名称
  ; 简单起见，从 INSTDIR 截取掉 \v2.0.18
  StrCpy $R0 $INSTDIR
  StrLen $R1 "\v${PRODUCT_VERSION}"
  StrCpy $R0 $R0 -$R1 ; 现在 R0 是 ...\GPX Studio
  
  StrCpy $LOG_FILE "$R0\install_log_v${PRODUCT_VERSION}.log"
  
  ; 如果日志文件已存在，以追加模式打开；否则创建新文件
  IfFileExists "$LOG_FILE" 0 create_new_log
    FileOpen $LOG_HANDLE $LOG_FILE a
    FileSeek $LOG_HANDLE 0 END
    Goto log_opened
  create_new_log:
    CreateDirectory "$R0" ; 确保 GPX Studio 目录存在
    FileOpen $LOG_HANDLE $LOG_FILE w
  log_opened:
  
  ; 导入调试日志
  FileWrite $LOG_HANDLE "$\r$\n=== 路径处理调试信息 ===$\r$\n"
  FileOpen $R1 "$TEMP\gpx_setup_debug.log" r
  ${Do}
    FileRead $R1 $R2
    ${If} $R2 == ""
      ${Break}
    ${EndIf}
    FileWrite $LOG_HANDLE $R2
  ${Loop}
  FileClose $R1
  FileWrite $LOG_HANDLE "=== 调试信息结束 ===$\r$\n$\r$\n"

  FileWrite $LOG_HANDLE "$\r$\n========================================$\r$\n"
  FileWrite $LOG_HANDLE "GPX Studio v${PRODUCT_VERSION} 安装日志$\r$\n"
  FileWrite $LOG_HANDLE "安装开始$\r$\n"
  FileWrite $LOG_HANDLE "========================================$\r$\n$\r$\n"
  
  DetailPrint "========================================"
  DetailPrint "开始安装 GPX Studio v${PRODUCT_VERSION}"
  DetailPrint "========================================"
  DetailPrint "日志文件: $LOG_FILE"
  DetailPrint "安装目录: $INSTDIR"
  
  FileWrite $LOG_HANDLE "日志文件: $LOG_FILE$\r$\n"
  FileWrite $LOG_HANDLE "最终安装目录: $INSTDIR$\r$\n"
  
  ; 记录路径分析信息
  Push $INSTDIR
  Call GetLastDirName
  Pop $0
  FileWrite $LOG_HANDLE "安装路径最后一级目录: $0$\r$\n$\r$\n"
  
  ; 创建最终的安装目录
  DetailPrint "正在创建安装目录..."
  FileWrite $LOG_HANDLE "正在创建安装目录...$\r$\n"
  CreateDirectory "$INSTDIR"
  DetailPrint "安装目录创建成功"
  FileWrite $LOG_HANDLE "安装目录创建成功$\r$\n$\r$\n"
  
  ; 设置输出路径并安装文件
  DetailPrint "正在复制程序文件到安装目录..."
  FileWrite $LOG_HANDLE "正在复制程序文件到安装目录...$\r$\n"
  SetOutPath "$INSTDIR"
  File /r "${BUILD_DIR}\*"
  DetailPrint "程序文件复制完成"
  FileWrite $LOG_HANDLE "程序文件复制完成$\r$\n$\r$\n"

  ; === 插入：检测旧版本处理（在创建快捷方式和写注册表之前）===
  ; 这样做是为了防止旧版本卸载程序删除掉新写入的注册表或快捷方式
  DetailPrint "正在检测系统中的旧版本..."
  FileWrite $LOG_HANDLE "正在检测系统中的旧版本...$\r$\n"
  Call DetectOldVersion
  
  ; 如果存在旧版本，迁移数据并卸载
  ${If} $OLD_VERSION != ""
    DetailPrint "检测到旧版本: v$OLD_VERSION"
    DetailPrint "旧版本安装路径: $OLD_INSTALL_PATH"
    FileWrite $LOG_HANDLE "检测到旧版本: v$OLD_VERSION$\r$\n"
    FileWrite $LOG_HANDLE "旧版本安装路径: $OLD_INSTALL_PATH$\r$\n"
    Call MigrateOldData
    Call UninstallOldVersion
  ${Else}
    DetailPrint "未检测到旧版本"
    FileWrite $LOG_HANDLE "未检测到旧版本$\r$\n"
  ${EndIf}
  ; ==========================================================
  
  ; 创建开始菜单快捷方式
  DetailPrint "正在创建开始菜单快捷方式..."
  FileWrite $LOG_HANDLE "正在创建开始菜单快捷方式...$\r$\n"
  CreateDirectory "$SMPROGRAMS\GPX Studio"
  CreateShortcut "$SMPROGRAMS\GPX Studio\GPX Studio v${PRODUCT_VERSION}.lnk" "$INSTDIR\${PRODUCT_EXE}"
  CreateShortcut "$SMPROGRAMS\GPX Studio\Uninstall v${PRODUCT_VERSION}.lnk" "$INSTDIR\Uninstall.exe"
  DetailPrint "开始菜单快捷方式创建成功"
  FileWrite $LOG_HANDLE "开始菜单快捷方式创建成功$\r$\n$\r$\n"
  
  ; 创建桌面快捷方式
  DetailPrint "正在创建桌面快捷方式..."
  FileWrite $LOG_HANDLE "正在创建桌面快捷方式...$\r$\n"
  CreateShortcut "$DESKTOP\GPX Studio ${PRODUCT_VERSION}.lnk" "$INSTDIR\${PRODUCT_EXE}"
  DetailPrint "桌面快捷方式创建成功"
  FileWrite $LOG_HANDLE "桌面快捷方式创建成功$\r$\n$\r$\n"
  
  ; 写入注册表
  DetailPrint "正在写入注册表信息..."
  FileWrite $LOG_HANDLE "正在写入注册表信息...$\r$\n"
  WriteRegStr ${REG_ROOT} "${REG_PATH}" "InstallLocation" "$INSTDIR"
  WriteRegStr ${REG_ROOT} "${REG_PATH}" "Version" "${PRODUCT_VERSION}"
  WriteRegStr ${REG_ROOT} "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_NAME} v${PRODUCT_VERSION}"
  WriteRegStr ${REG_ROOT} "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${REG_ROOT} "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr ${REG_ROOT} "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "URLInfoAbout" "${PRODUCT_URL}"
  WriteRegStr ${REG_ROOT} "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayIcon" "$INSTDIR\${PRODUCT_EXE}"
  WriteRegStr ${REG_ROOT} "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr ${REG_ROOT} "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "InstallLocation" "$INSTDIR"
  WriteRegDWORD ${REG_ROOT} "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "NoModify" 1
  WriteRegDWORD ${REG_ROOT} "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "NoRepair" 1
  DetailPrint "注册表信息写入完成"
  FileWrite $LOG_HANDLE "注册表信息写入完成$\r$\n$\r$\n"
  
  FileWrite $LOG_HANDLE "$\r$\n========================================$\r$\n"
  FileWrite $LOG_HANDLE "安装完成！$\r$\n"
  FileWrite $LOG_HANDLE "========================================$\r$\n"
  FileClose $LOG_HANDLE
  
  DetailPrint "========================================"
  DetailPrint "安装完成！"
  DetailPrint "日志已保存: $LOG_FILE"
  DetailPrint "========================================"
SectionEnd

Section "Uninstall"
  ; 以追加模式打开日志文件
  ; 根据卸载程序位置(INSTDIR)计算日志路径，不使用 $PROGRAMFILES，确保支持非C盘安装
  ; INSTDIR = ...\GPX Studio\v2.0.18，日志在 ...\GPX Studio\install_log_...
  StrCpy $R0 $INSTDIR
  StrLen $R1 "\v${PRODUCT_VERSION}"
  StrCpy $R0 $R0 -$R1
  StrCpy $LOG_FILE "$R0\install_log_v${PRODUCT_VERSION}.log"
  
  ; 如果日志文件存在，以追加模式打开；否则创建新文件
  IfFileExists "$LOG_FILE" 0 create_uninstall_log
    FileOpen $LOG_HANDLE $LOG_FILE a
    FileSeek $LOG_HANDLE 0 END
    Goto uninstall_log_opened
  create_uninstall_log:
    FileOpen $LOG_HANDLE $LOG_FILE w
  uninstall_log_opened:
  
  FileWrite $LOG_HANDLE "$\r$\n========================================$\r$\n"
  FileWrite $LOG_HANDLE "GPX Studio v${PRODUCT_VERSION} 卸载日志$\r$\n"
  FileWrite $LOG_HANDLE "卸载开始$\r$\n"
  FileWrite $LOG_HANDLE "========================================$\r$\n$\r$\n"
  
  DetailPrint "========================================"
  DetailPrint "开始卸载 GPX Studio v${PRODUCT_VERSION}"
  DetailPrint "========================================"
  DetailPrint "日志文件: $LOG_FILE"
  DetailPrint "卸载路径: $INSTDIR"
  
  FileWrite $LOG_HANDLE "日志文件: $LOG_FILE$\r$\n"
  FileWrite $LOG_HANDLE "卸载路径: $INSTDIR$\r$\n$\r$\n"
  
  DetailPrint "正在检查程序是否运行中..."
  FileWrite $LOG_HANDLE "正在检查程序是否运行中...$\r$\n"
  Call un.CheckProcessRunning
  ${If} $PROCESS_RUNNING == "true"
    DetailPrint "检测到程序正在运行"
    FileWrite $LOG_HANDLE "检测到程序正在运行$\r$\n"
    MessageBox MB_YESNO|MB_ICONQUESTION "GPX Studio 正在运行中。卸载程序需要关闭软件才能继续。程序将自动关闭程序并继续卸载，或者取消卸载。"
    ${If} $0 == IDNO
      DetailPrint "用户取消卸载"
      FileWrite $LOG_HANDLE "用户取消卸载$\r$\n"
      FileClose $LOG_HANDLE
      Abort
    ${EndIf}
    DetailPrint "正在关闭程序..."
    FileWrite $LOG_HANDLE "正在关闭程序...$\r$\n"
    Call un.CloseProcess
    DetailPrint "程序已关闭"
    FileWrite $LOG_HANDLE "程序已关闭$\r$\n"
  ${Else}
    DetailPrint "程序未运行"
    FileWrite $LOG_HANDLE "程序未运行$\r$\n"
  ${EndIf}
  
  DetailPrint "正在删除快捷方式..."
  FileWrite $LOG_HANDLE "$\r$\n正在删除快捷方式...$\r$\n"
  Delete "$SMPROGRAMS\GPX Studio\GPX Studio v${PRODUCT_VERSION}.lnk"
  Delete "$SMPROGRAMS\GPX Studio\Uninstall v${PRODUCT_VERSION}.lnk"
  Delete "$DESKTOP\GPX Studio ${PRODUCT_VERSION}.lnk"
  DetailPrint "快捷方式删除完成"
  FileWrite $LOG_HANDLE "快捷方式删除完成$\r$\n"
  
  DetailPrint "正在删除开始菜单文件夹..."
  FileWrite $LOG_HANDLE "正在删除开始菜单文件夹...$\r$\n"
  RMDir /r "$SMPROGRAMS\GPX Studio"
  DetailPrint "开始菜单文件夹删除完成"
  FileWrite $LOG_HANDLE "开始菜单文件夹删除完成$\r$\n"
  
  DetailPrint "正在删除安装目录..."
  FileWrite $LOG_HANDLE "正在删除安装目录...$\r$\n"
  ; 只删除v版本号子目录，保留GPX Studio主目录和日志文件
  RMDir /r "$INSTDIR"
  DetailPrint "安装目录删除完成"
  FileWrite $LOG_HANDLE "安装目录删除完成（已保留GPX Studio主目录和日志文件）$\r$\n"
  
  DetailPrint "正在清理注册表信息..."
  FileWrite $LOG_HANDLE "正在清理注册表信息...$\r$\n"
  DeleteRegValue ${REG_ROOT} "${REG_PATH}" "InstallLocation"
  DeleteRegValue ${REG_ROOT} "${REG_PATH}" "Version"
  DeleteRegKey /ifempty ${REG_ROOT} "${REG_PATH}"
  DeleteRegKey ${REG_ROOT} "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
  DetailPrint "注册表信息清理完成"
  FileWrite $LOG_HANDLE "注册表信息清理完成$\r$\n"
  
  FileWrite $LOG_HANDLE "$\r$\n========================================$\r$\n"
  FileWrite $LOG_HANDLE "卸载完成！$\r$\n"
  FileWrite $LOG_HANDLE "========================================$\r$\n"
  FileClose $LOG_HANDLE
  
  DetailPrint "========================================"
  DetailPrint "卸载完成！"
  DetailPrint "日志已保存: $LOG_FILE"
  DetailPrint "========================================"
SectionEnd

Section "Uninstaller"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Function DetectOldVersion
  StrCpy $OLD_VERSION ""
  StrCpy $OLD_INSTALL_PATH ""
  DetailPrint "正在读取注册表中的版本信息..."
  FileWrite $LOG_HANDLE "正在读取注册表中的版本信息...$\r$\n"
  ReadRegStr $OLD_VERSION ${REG_ROOT} "${REG_PATH}" "Version"
  ${If} $OLD_VERSION != ""
    DetailPrint "找到已安装版本: v$OLD_VERSION"
    FileWrite $LOG_HANDLE "找到已安装版本: v$OLD_VERSION$\r$\n"
    ${If} $OLD_VERSION != "${PRODUCT_VERSION}"
      DetailPrint "版本不同，需要处理旧版本"
      FileWrite $LOG_HANDLE "版本不同，需要处理旧版本$\r$\n"
      ReadRegStr $OLD_INSTALL_PATH ${REG_ROOT} "${REG_PATH}" "InstallLocation"
      DetailPrint "旧版本路径: $OLD_INSTALL_PATH"
      FileWrite $LOG_HANDLE "旧版本路径: $OLD_INSTALL_PATH$\r$\n"
    ${Else}
      DetailPrint "版本相同，跳过旧版本处理"
      FileWrite $LOG_HANDLE "版本相同，跳过旧版本处理$\r$\n"
      StrCpy $OLD_VERSION ""
      StrCpy $OLD_INSTALL_PATH ""
    ${EndIf}
  ${Else}
    DetailPrint "注册表中未找到旧版本信息"
    FileWrite $LOG_HANDLE "注册表中未找到旧版本信息$\r$\n"
  ${EndIf}
FunctionEnd

Function MigrateOldData
  StrCpy $DATA_MIGRATED "false"
  ${If} $OLD_INSTALL_PATH != ""
    DetailPrint "检查旧版本数据目录: $OLD_INSTALL_PATH\GPXStudioData"
    FileWrite $LOG_HANDLE "检查旧版本数据目录: $OLD_INSTALL_PATH\GPXStudioData$\r$\n"
    IfFileExists "$OLD_INSTALL_PATH\GPXStudioData" 0 skip_migrate
      DetailPrint "找到旧版本数据目录"
      FileWrite $LOG_HANDLE "找到旧版本数据目录$\r$\n"
      DetailPrint "开始迁移旧版本数据..."
      FileWrite $LOG_HANDLE "开始迁移旧版本数据...$\r$\n"
      DetailPrint "创建新数据目录: $INSTDIR\GPXStudioData"
      FileWrite $LOG_HANDLE "创建新数据目录: $INSTDIR\GPXStudioData$\r$\n"
      CreateDirectory "$INSTDIR\GPXStudioData"
      DetailPrint "正在复制数据文件..."
      FileWrite $LOG_HANDLE "正在复制数据文件...$\r$\n"
      CopyFiles /SILENT "$OLD_INSTALL_PATH\GPXStudioData\*.*" "$INSTDIR\GPXStudioData\"
      StrCpy $DATA_MIGRATED "true"
      DetailPrint "数据迁移完成！"
      FileWrite $LOG_HANDLE "数据迁移完成！$\r$\n"
      Goto migrate_done
    skip_migrate:
      DetailPrint "旧版本数据目录不存在，跳过数据迁移"
      FileWrite $LOG_HANDLE "旧版本数据目录不存在，跳过数据迁移$\r$\n"
    migrate_done:
  ${Else}
    DetailPrint "旧版本路径为空，跳过数据迁移"
    FileWrite $LOG_HANDLE "旧版本路径为空，跳过数据迁移$\r$\n"
  ${EndIf}
FunctionEnd

Function UninstallOldVersion
  ${If} $OLD_INSTALL_PATH != ""
    DetailPrint "检查旧版本卸载程序: $OLD_INSTALL_PATH\Uninstall.exe"
    FileWrite $LOG_HANDLE "检查旧版本卸载程序: $OLD_INSTALL_PATH\Uninstall.exe$\r$\n"
    IfFileExists "$OLD_INSTALL_PATH\Uninstall.exe" 0 skip_uninstall
      DetailPrint "找到旧版本卸载程序"
      FileWrite $LOG_HANDLE "找到旧版本卸载程序$\r$\n"
      DetailPrint "开始静默卸载旧版本..."
      FileWrite $LOG_HANDLE "开始静默卸载旧版本...$\r$\n"
      DetailPrint "执行命令: $OLD_INSTALL_PATH\Uninstall.exe /S _?=$OLD_INSTALL_PATH"
      FileWrite $LOG_HANDLE "执行命令: $OLD_INSTALL_PATH\Uninstall.exe /S _?=$OLD_INSTALL_PATH$\r$\n"
      ExecWait '"$OLD_INSTALL_PATH\Uninstall.exe" /S _?=$OLD_INSTALL_PATH'
      
      ; 清理卸载程序和残留目录
      Delete "$OLD_INSTALL_PATH\Uninstall.exe"
      RMDir "$OLD_INSTALL_PATH"
      
      DetailPrint "旧版本卸载完成！"
      FileWrite $LOG_HANDLE "旧版本卸载完成！$\r$\n"
      Goto uninstall_done
    skip_uninstall:
      DetailPrint "旧版本卸载程序不存在，跳过卸载"
      FileWrite $LOG_HANDLE "旧版本卸载程序不存在，跳过卸载$\r$\n"
    uninstall_done:
  ${Else}
    DetailPrint "旧版本路径为空，跳过卸载"
    FileWrite $LOG_HANDLE "旧版本路径为空，跳过卸载$\r$\n"
  ${EndIf}
FunctionEnd

Function un.CheckProcessRunning
  StrCpy $PROCESS_RUNNING "false"
  DetailPrint "检查窗口: 'GPX Studio'"
  FileWrite $LOG_HANDLE "Function un.CheckProcessRunning: Checking for 'GPX Studio' window...$\r$\n"
  
  System::Call "user32::FindWindowA(i 0, t 'GPX Studio') i .r0"
  ${If} $0 != 0
    DetailPrint "找到运行中的窗口 (句柄: $0)"
    StrCpy $PROCESS_RUNNING "true"
    FileWrite $LOG_HANDLE "Found window 'GPX Studio', Handle: $0$\r$\n"
  ${Else}
    DetailPrint "未找到窗口 'GPX Studio'，继续检查其他窗口"
    FileWrite $LOG_HANDLE "Window 'GPX Studio' not found. Checking 'GPX Studio v'...$\r$\n"
    
    DetailPrint "检查窗口: 'GPX Studio v'"
    System::Call "user32::FindWindowA(i 0, t 'GPX Studio v') i .r0"
    ${If} $0 != 0
      DetailPrint "找到运行中的窗口 (句柄: $0)"
      StrCpy $PROCESS_RUNNING "true"
      FileWrite $LOG_HANDLE "Found window 'GPX Studio v', Handle: $0$\r$\n"
    ${Else}
      DetailPrint "未找到任何运行中的GPX Studio窗口"
      FileWrite $LOG_HANDLE "No running GPX Studio windows found.$\r$\n"
    ${EndIf}
  ${EndIf}
FunctionEnd

Function un.CloseProcess
  FileWrite $LOG_HANDLE "Function un.CloseProcess: Attempting to close processes...$\r$\n"

  DetailPrint "尝试关闭窗口: 'GPX Studio'"
  System::Call "user32::FindWindowA(i 0, t 'GPX Studio') i .r0"
  ${If} $0 != 0
    DetailPrint "发送关闭消息到窗口 (句柄: $0)"
    FileWrite $LOG_HANDLE "Posting WM_CLOSE to 'GPX Studio' (Handle: $0)...$\r$\n"
    System::Call "user32::PostMessageA(i r0, i 0x0010, i 0, i 0)"
  ${EndIf}
  
  DetailPrint "尝试关闭窗口: 'GPX Studio v'"
  System::Call "user32::FindWindowA(i 0, t 'GPX Studio v') i .r0"
  ${If} $0 != 0
    DetailPrint "发送关闭消息到窗口 (句柄: $0)"
    FileWrite $LOG_HANDLE "Posting WM_CLOSE to 'GPX Studio v' (Handle: $0)...$\r$\n"
    System::Call "user32::PostMessageA(i r0, i 0x0010, i 0, i 0)"
  ${EndIf}
  
  DetailPrint "等待程序关闭..."
  FileWrite $LOG_HANDLE "Waiting 1s for process termination...$\r$\n"
  Sleep 1000
  DetailPrint "等待完成"
  FileWrite $LOG_HANDLE "Wait complete.$\r$\n"
FunctionEnd