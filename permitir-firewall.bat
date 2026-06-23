@echo off
REM Libera a porta 8765 no Firewall do Windows para o PvP local do Grid Battler.
REM Du-clique neste arquivo e clique "Sim" na janela de permissao (UAC).

net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Pedindo permissao de administrador...
  powershell -Command "Start-Process -Verb RunAs -FilePath '%~f0'"
  exit /b
)

echo Criando regra de firewall (porta TCP 8765)...
netsh advfirewall firewall delete rule name="Grid Battler relay" >nul 2>&1
netsh advfirewall firewall add rule name="Grid Battler relay" dir=in action=allow protocol=TCP localport=8765 profile=any

echo.
echo ============================================================
echo  Pronto! A porta 8765 foi liberada.
echo  Agora, numa janela normal, rode:   python relay.py
echo  e abra a URL que aparecer nos DOIS aparelhos.
echo.
echo  (Para remover depois:
echo   netsh advfirewall firewall delete rule name="Grid Battler relay")
echo ============================================================
echo.
pause
