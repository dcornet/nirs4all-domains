# Optional workspace-local toolchain; a normal installed Rust toolchain also works.
$repoRoot = Split-Path -Parent $PSScriptRoot
$localCargo = Join-Path $repoRoot '.tools\cargo'
if (Test-Path -LiteralPath $localCargo) {
    $env:CARGO_HOME = $localCargo
    $env:RUSTUP_HOME = Join-Path $repoRoot '.tools\rustup'
    $env:PATH = (Join-Path $localCargo 'bin') + ';' + $env:PATH
    $gccBin = Join-Path $repoRoot '.tools\mingw64\bin'
    if (Test-Path -LiteralPath $gccBin) {
        $llvm = Get-ChildItem -LiteralPath (Join-Path $repoRoot '.tools') -Directory -Filter 'llvm-mingw-*' | Select-Object -First 1
        if ($llvm) {
            # Clang's linker driver handles spaces in the toolchain prefix.
            # GNU Rust also needs GCC's static exception/builtin libraries.
            $llvmBin = Join-Path $llvm.FullName 'bin'
            $gccLib = Get-ChildItem -LiteralPath (Join-Path $repoRoot '.tools\mingw64\lib\gcc\x86_64-w64-mingw32') -Directory | Select-Object -First 1
            $env:PATH = $llvmBin + ';' + $gccBin + ';' + $env:PATH
            $env:CARGO_TARGET_X86_64_PC_WINDOWS_GNU_LINKER = Join-Path $llvmBin 'x86_64-w64-mingw32-clang.exe'
            $env:CARGO_ENCODED_RUSTFLAGS = '-Lnative=' + $gccLib.FullName
        }
    }
}
$wheelLibs = Join-Path $repoRoot '.venv\Lib\site-packages\nirs4all_methods.libs'
if (Test-Path -LiteralPath $wheelLibs) { $env:PATH = $wheelLibs + ';' + $env:PATH }
$methods = Join-Path $repoRoot '.venv\Lib\site-packages\n4m\lib\n4m.dll'
if (Test-Path -LiteralPath $methods) { $env:N4DOMAINS_METHODS_LIBRARY = $methods }
