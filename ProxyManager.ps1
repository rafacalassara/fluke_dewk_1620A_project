param ( [switch]$on )

function Ligar-Proxy {
    $proxyUrl = "http://[cpf]:[senha_portal]@[endereco_proxy]:8080"

    $env:http_proxy = $proxyUrl
    $env:https_proxy = $proxyUrl

    Write-Host "Proxy ativado"
}

function Desligar-Proxy {
    $env:http_proxy = $null
    $env:https_proxy = $null

    Write-Host "Proxy desativado."
}

if ($on) {
    Ligar-Proxy
} else {
    Desligar-Proxy
}