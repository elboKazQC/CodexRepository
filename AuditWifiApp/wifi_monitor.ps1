# Script de surveillance Wi-Fi simplifié
function Get-WifiStatus {
    # Structure de résultats avec valeurs par défaut
    $result = @{
        SSID              = "N/A"
        BSSID             = "00:00:00:00:00:00"
        SignalStrength    = "0%"
        SignalStrengthDBM = -100
        Channel           = 0
        Band              = "N/A"
        Status            = "Disconnected"
        TransmitRate      = "0 Mbps"
        ReceiveRate       = "0 Mbps"
        NoiseFloor        = $null
        SNR               = $null
    }

    try {
        # Utilise Start-Process pour exécuter netsh
        $pinfo = New-Object System.Diagnostics.ProcessStartInfo
        $pinfo.FileName = "netsh"
        $pinfo.RedirectStandardOutput = $true
        $pinfo.RedirectStandardError = $true
        $pinfo.UseShellExecute = $false
        $pinfo.Arguments = "wlan show interfaces"
        $p = New-Object System.Diagnostics.Process
        $p.StartInfo = $pinfo
        $p.Start() | Out-Null
        $wifiInfo = $p.StandardOutput.ReadToEnd()
        $p.WaitForExit()

        if ($p.ExitCode -eq 0) {
            # Vérifier si une interface est connectée
            if ($wifiInfo -match "State\s*:\s*connected") {
                $result.Status = "Connected"

                # SSID
                if ($wifiInfo -match "SSID\s*:\s*([^\r\n]+)") {
                    $result.SSID = $matches[1].Trim()
                }

                # BSSID
                if ($wifiInfo -match "BSSID\s*:\s*([0-9A-Fa-f:]+)") {
                    $result.BSSID = $matches[1].Trim()
                }

                # Signal
                if ($wifiInfo -match "Signal\s*:\s*(\d+)%") {
                    $signal = [int]$matches[1]
                    $result.SignalStrength = "$signal%"
                    # Conversion approximative de % en dBm
                    $result.SignalStrengthDBM = -100 + ($signal / 2)
                }

                # Channel
                if ($wifiInfo -match "Channel\s*:\s*(\d+)") {
                    $result.Channel = [int]$matches[1]
                }

                # Band
                if ($wifiInfo -match "Band\s*:\s*([^\r\n]+)") {
                    $result.Band = $matches[1].Trim()
                }

                # Rates
                if ($wifiInfo -match "Receive rate \(Mbps\)\s*:\s*(\d+)") {
                    $result.ReceiveRate = "$($matches[1]) Mbps"
                }
                if ($wifiInfo -match "Transmit rate \(Mbps\)\s*:\s*(\d+)") {
                    $result.TransmitRate = "$($matches[1]) Mbps"
                }

                # Noise floor if available
                if ($wifiInfo -match "Noise\s*:\s*(-?\d+)\s*dBm") {
                    $result.NoiseFloor = [int]$matches[1]
                }

                # SNR if provided directly
                if ($wifiInfo -match "SNR\s*:\s*(\d+)\s*dB") {
                    $result.SNR = [int]$matches[1]
                }

                # Compute SNR if not provided but noise and signal are present
                if ($null -ne $result.NoiseFloor -and $null -eq $result.SNR) {
                    $result.SNR = [int]($result.SignalStrengthDBM - $result.NoiseFloor)
                }
            }
        }
        else {
            $result.Status = "Error: netsh command failed"
        }
    }
    catch {
        $result.Status = "Error: $($_.Exception.Message)"
    }

    return $result | ConvertTo-Json
}

# Exécute une seule fois et retourne le résultat
Get-WifiStatus
