# 测试 Qwen3 Max prompt_token_details

$env:HTTP_PROXY = $null
$env:HTTPS_PROXY = $null
$env:http_proxy = $null
$env:https_proxy = $null

$DASHSCOPE_KEY = "sk-91fe1c9c529b46bb88dc200a2e97b2b6"
$url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer $DASHSCOPE_KEY"
}

$body = @{
    model = "qwen3-max-2026-01-23"
    messages = @(
        @{role = "user"; content = "你好，请简单介绍一下自己"}
    )
} | ConvertTo-Json -Depth 10

Write-Host "=" * 60
Write-Host "测试 Qwen3 Max prompt_token_details"
Write-Host "=" * 60

try {
    $resp = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body -ContentType "application/json" -TimeoutSec 30
    $respJson = $resp | ConvertTo-Json -Depth 10 -Compress
    Write-Host "Status: 200"
    Write-Host "Response: $respJson"

    if ($resp.usage) {
        Write-Host ""
        Write-Host "--- Usage Details ---"
        Write-Host "prompt_tokens: $($resp.usage.prompt_tokens)"
        Write-Host "completion_tokens: $($resp.usage.completion_tokens)"
        Write-Host "total_tokens: $($resp.usage.total_tokens)"
        Write-Host "prompt_tokens_details: $($resp.usage.prompt_tokens_details)"
        if ($resp.usage.prompt_tokens_details) {
            Write-Host "  - cached_tokens: $($resp.usage.prompt_tokens_details.cached_tokens)"
        }
    }
} catch {
    Write-Host "❌ 请求失败: $($_.Exception.Message)"
}
