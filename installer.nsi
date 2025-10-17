; TelegrammBolt Installer Script
!define APPNAME "TelegrammBolt"
!define COMPANYNAME "Your Company"
!define DESCRIPTION "Telegram Bot for DSE Management"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0

RequestExecutionLevel admin
InstallDir "$PROGRAMFILES\${APPNAME}"
Name "${APPNAME}"
outFile "${APPNAME}_Setup.exe"

Page directory
Page instfiles

Section "install"
    SetOutPath $INSTDIR
    
    ; Копируем исполняемый файл
    File "dist\TelegrammBolt.exe"
    
    ; Копируем конфигурационные файлы
    File "ven_bot.json"
    File "smtp_config.json"
    
    ; Создаем директории
    CreateDirectory "$INSTDIR\photos"
    
    ; Создаем ярлык на рабочем столе
    CreateShortcut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\TelegrammBolt.exe"
    
    ; Создаем ярлык в меню Пуск
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortcut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\TelegrammBolt.exe"
    CreateShortcut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    
    ; Создаем деинсталлятор
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    ; Добавляем в реестр для Programs and Features
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegDWord HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWord HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWord HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
    WriteRegDWord HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
SectionEnd

Section "uninstall"
    Delete "$INSTDIR\TelegrammBolt.exe"
    Delete "$INSTDIR\ven_bot.json"
    Delete "$INSTDIR\smtp_config.json"
    Delete "$INSTDIR\uninstall.exe"
    
    RMDir /r "$INSTDIR\photos"
    RMDir "$INSTDIR"
    
    Delete "$DESKTOP\${APPNAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APPNAME}"
    
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
SectionEnd