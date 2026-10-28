# HumanitZ - NPC Community Dedicated Fix - patcher do servidor dedicado WINDOWS (PowerShell, ja vem no Windows)
# Altera 2 bytes em UHZCommunityNPCSubSys::ShouldCreateSubsystem no HumanitZServer-Win64-Shipping.exe para o
# subsistema de comunidade de NPCs existir tambem no servidor dedicado. Acha o ponto por padrao de bytes (nao por
# endereco fixo), recusa versoes desconhecidas e cria backup .bak antes de alterar.
#
# Uso: copie este arquivo para ...\HumanitZServer\Binaries\Win64\ (pasta do HumanitZServer-Win64-Shipping.exe),
#      com o servidor parado, clique com o botao direito -> "Executar com o PowerShell".
#      - Se o patch nao estiver aplicado: aplica.
#      - Se ja estiver aplicado: pergunta se quer restaurar o original (.bak).
# Linha de comando: powershell -File humanitz_npc_patcher.ps1 [-Exe caminho\do.exe] [-Restore] [-NoPause]
param([string]$Exe = "", [switch]$Restore, [switch]$NoPause)
$ErrorActionPreference = "Stop"
function Fim([int]$code) {
  if (-not $NoPause) { Read-Host "`nPressione Enter para sair / Press Enter to exit" | Out-Null }
  exit $code
}
$Padrao = "40 53 48 83 EC 20 48 8B DA E8 ?? ?? ?? ?? 84 C0 74 0A 48 85 DB 74 05 E8 ?? ?? ?? ?? 32 C0 48 83 C4 20 5B C3"
$Off = 16; $Novo = "EB 0C"
function Rx($tokens) { ($tokens | ForEach-Object { if ($_ -eq "??") { "[\s\S]" } else { "\x" + $_ } }) -join "" }
try {
  if ($Exe -eq "") {
    $dirs = @($PSScriptRoot, (Split-Path $PSScriptRoot -Parent))
    $cands = foreach ($d in $dirs) { $f = Join-Path $d "HumanitZServer-Win64-Shipping.exe"; if (Test-Path $f) { $f } }
    if (-not $cands) {
      Write-Host "ERRO: coloque este arquivo na pasta ...\HumanitZServer\Binaries\Win64 do servidor (onde fica HumanitZServer-Win64-Shipping.exe)." -ForegroundColor Red
      Write-Host "ERROR: put this file in the server's ...\HumanitZServer\Binaries\Win64 folder (next to HumanitZServer-Win64-Shipping.exe)." -ForegroundColor Red
      Fim 1
    }
    $Exe = @($cands)[0]
  }
  $bak = "$Exe.bak"
  Write-Host "Executavel / Executable: $Exe"
  $bytes = [IO.File]::ReadAllBytes($Exe)
  $text = [Text.Encoding]::GetEncoding(28591).GetString($bytes)
  $tok = $Padrao.Split(" "); $new = $Novo.Split(" ")
  $pt = $tok.Clone(); for ($i = 0; $i -lt $new.Length; $i++) { $pt[$Off + $i] = $new[$i] }
  $aplicado = ([regex]::Matches($text, (Rx $pt)).Count -eq 1)
  if ($aplicado -and -not $Restore -and -not $NoPause) {
    Write-Host "O patch ja esta aplicado. / The patch is already applied." -ForegroundColor Green
    $r = Read-Host "Restaurar o executavel original? / Restore the original executable? (s/y/N)"
    if ($r -match '^[sSyY]') { $Restore = $true } else { Fim 0 }
  }
  if ($Restore) {
    if (-not (Test-Path $bak)) { Write-Host "ERRO: backup nao encontrado / backup not found: $bak" -ForegroundColor Red; Fim 1 }
    Copy-Item $bak $Exe -Force
    Write-Host "Restaurado a partir do backup. / Restored from backup." -ForegroundColor Green; Fim 0
  }
  if ($aplicado) { Write-Host "O patch ja esta aplicado. Nada a fazer. / Already applied. Nothing to do." -ForegroundColor Green; Fim 0 }
  $m = [regex]::Matches($text, (Rx $tok))
  if ($m.Count -ne 1) {
    Write-Host "ERRO: padrao encontrado $($m.Count) vezes. Versao do jogo nao suportada (o jogo pode ter sido atualizado). Nada foi alterado." -ForegroundColor Red
    Write-Host "ERROR: pattern found $($m.Count) times. Unsupported game version. Nothing was changed." -ForegroundColor Red
    Fim 1
  }
  $pos = $m[0].Index + $Off
  if (-not (Test-Path $bak)) { Copy-Item $Exe $bak; Write-Host "Backup criado / Backup created: $bak" }
  for ($i = 0; $i -lt $new.Length; $i++) { $bytes[$pos + $i] = [Convert]::ToByte($new[$i], 16) }
  [IO.File]::WriteAllBytes($Exe, $bytes)
  Write-Host ("Patch aplicado no offset 0x{0:X}. / Patch applied at offset 0x{0:X}." -f $pos) -ForegroundColor Green
  Fim 0
} catch {
  Write-Host "ERRO / ERROR: $($_.Exception.Message)" -ForegroundColor Red
  Write-Host "Feche o servidor e tente de novo. / Close the server and try again." -ForegroundColor Red
  Fim 1
}
