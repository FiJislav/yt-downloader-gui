param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Url,

    [ValidateSet('mp3','mp4','mkv','4k','4k-no-av1','list-formats','subs','embed-subs')]
    [string]$Mode = 'mp4',

    [string]$AudioLang,

    [string]$SubLang = 'en',

    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command yt-dlp -ErrorAction SilentlyContinue)) {
    Write-Error 'yt-dlp is not installed or not in PATH.'
}

$audioSelector = if ($AudioLang) { "bestaudio[lang=$AudioLang]" } else { 'bestaudio' }
$argsList = @()

switch ($Mode) {
    'mp3' {
        $argsList += '-f', $audioSelector, '--extract-audio', '--audio-format', 'mp3', '--audio-quality', '0'
    }
    'mp4' {
        if ($AudioLang) {
            Write-Warning 'Audio language filtering is not used in mp4 mode. Use mode 4k or mkv for explicit audio track selection.'
        }
        $argsList += '-f', 'best'
    }
    'mkv' {
        $argsList += '-f', "bestvideo+$audioSelector", '--merge-output-format', 'mkv'
    }
    '4k' {
        $argsList += '-f', "bestvideo[height<=2160]+$audioSelector/best", '--merge-output-format', 'mp4'
    }
    '4k-no-av1' {
        $argsList += '-f', "bestvideo[height>=2160][vcodec!=av01]+$audioSelector/best", '--merge-output-format', 'mkv'
    }
    'list-formats' {
        $argsList += '-F'
    }
    'subs' {
        $argsList += '--write-subs', '--sub-lang', $SubLang, '--convert-subs', 'srt'
    }
    'embed-subs' {
        $argsList += '-f', "bestvideo+$audioSelector", '--merge-output-format', 'mp4', '--embed-subs', '--sub-lang', $SubLang, '--convert-subs', 'srt'
    }
}

$argsList += $Url

if ($DryRun) {
    Write-Host ('yt-dlp ' + ($argsList -join ' '))
    exit 0
}

& yt-dlp @argsList
