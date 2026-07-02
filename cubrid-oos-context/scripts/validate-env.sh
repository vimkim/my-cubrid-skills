#!/usr/bin/env bash
# validate-env.sh - Check that the current CUBRID worktree is ready for OOS development.
# Exits 0 if all required checks pass, 1 if any fail. Prints warnings/errors to stderr.
# Usage: bash validate-env.sh [directory]
#   directory: path to check (defaults to $PWD)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON="$SCRIPT_DIR/../../cubrid-common/scripts/cubrid-common.sh"

if [[ ! -f "$COMMON" ]]; then
  echo "FAIL: shared CUBRID helpers not found: $COMMON" >&2
  echo "Install the full my-cubrid-skills collection so cubrid-common is present." >&2
  exit 1
fi

# shellcheck source=../../cubrid-common/scripts/cubrid-common.sh
source "$COMMON"

DIR="${1:-$PWD}"
ERRORS=0
WARNINGS=0

if [[ -t 2 ]]; then
  RED='\033[0;31m'; YELLOW='\033[0;33m'; GREEN='\033[0;32m'; BOLD='\033[1m'; RESET='\033[0m'
else
  RED=''; YELLOW=''; GREEN=''; BOLD=''; RESET=''
fi

ok()   { printf '%b[OK]%b    %s\n' "$GREEN" "$RESET" "$1" >&2; }
warn() { printf '%b[WARN]%b  %s\n' "$YELLOW" "$RESET" "$1" >&2; WARNINGS=$((WARNINGS + 1)); }
fail() { printf '%b[FAIL]%b  %s\n' "$RED" "$RESET" "$1" >&2; ERRORS=$((ERRORS + 1)); }
info() { printf '        %s\n' "$1" >&2; }

printf '%b=== CUBRID OOS Environment Validation ===%b\n' "$BOLD" "$RESET" >&2
printf 'Checking: %s\n\n' "$DIR" >&2

if cubrid_is_git_worktree "$DIR"; then
  branch=$(git -C "$DIR" branch --show-current 2>/dev/null || echo "(detached)")
  ok "Git worktree (branch: $branch)"
else
  fail "Not a git worktree - code search and git features will be limited"
  info "Run from a CUBRID repo clone or worktree"
fi

if cubrid_is_source_tree "$DIR" && [[ -f "$DIR/CMakePresets.json" ]]; then
  ok "CUBRID source tree detected (project(CUBRID) + CMakePresets.json)"
else
  fail "Not a complete CUBRID source tree"
  info "Expected CMakeLists.txt with project(CUBRID) and CMakePresets.json"
fi

if [[ -d "$DIR/src" ]]; then
  oos_file=$(find "$DIR/src" -maxdepth 5 -name "oos_file.cpp" -type f 2>/dev/null | head -1 || true)
else
  oos_file=""
fi
if [[ -n "$oos_file" ]]; then
  rel_oos=$(realpath --relative-to="$DIR" "$oos_file" 2>/dev/null || echo "$oos_file")
  ok "OOS source found: $rel_oos"
else
  warn "oos_file.cpp not found - are you on the feat/oos branch?"
  info "OOS code lives on feat/oos or derived branches"
fi

if [[ -n "${PRESET_MODE:-}" ]]; then
  if cubrid_preset_mode_is_valid "$DIR"; then
    ok "PRESET_MODE=$PRESET_MODE"
  else
    warn "PRESET_MODE=$PRESET_MODE is not a valid CMake preset for this worktree"
    info "Available presets:"
    cubrid_list_cmake_presets "$DIR" | sed 's/^/        /' >&2
  fi
else
  warn "PRESET_MODE not set - build directory detection may be ambiguous"
  info "Source .envrc or set PRESET_MODE (e.g., release_gcc, debug_clang)"
fi

build_dir=$(cubrid_find_build_dir "$DIR")
if [[ -n "$build_dir" && -d "$build_dir" ]]; then
  ok "Build directory exists: $(basename "$build_dir")/"
else
  fail "No build directory found (build_preset_*)"
  info "Run: just build"
fi

ccj_root="$DIR/compile_commands.json"
ccj_build=""
if [[ -n "$build_dir" ]]; then
  ccj_build="$build_dir/compile_commands.json"
fi

if [[ -f "$ccj_root" || -L "$ccj_root" ]]; then
  if [[ -L "$ccj_root" ]]; then
    target=$(readlink "$ccj_root")
    if [[ -f "$ccj_root" ]]; then
      ok "compile_commands.json symlink at root -> $target"
    else
      fail "compile_commands.json symlink broken -> $target"
      info "Rebuild or run: ln -sf build_preset_\${PRESET_MODE}/compile_commands.json ."
    fi
  else
    ok "compile_commands.json exists at project root"
  fi
elif [[ -n "$ccj_build" && -f "$ccj_build" ]]; then
  warn "compile_commands.json found in build dir but not symlinked to root"
  info "LSP may not find it. Run: ln -sf build_preset_\${PRESET_MODE}/compile_commands.json ."
else
  fail "compile_commands.json not found - LSP features will not work"
  info "Build with: just build (CMake generates it with CMAKE_EXPORT_COMPILE_COMMANDS=ON)"
fi

if command -v clangd >/dev/null 2>&1; then
  clangd_ver=$(clangd --version 2>/dev/null | head -1)
  ok "clangd available: $clangd_ver"
else
  warn "clangd not found - LSP hover/references/goto-def will not work"
  info "Install clangd (e.g., sudo dnf install clang-tools-extra)"
fi

if command -v just >/dev/null 2>&1; then
  ok "just available"
else
  warn "just not found - build shortcuts (just build, just ctest) unavailable"
  info "Install: cargo install just"
fi

printf '\n' >&2
if [[ "$ERRORS" -gt 0 ]]; then
  printf '%b%b%d error(s), %d warning(s)%b - environment not ready\n' "$RED" "$BOLD" "$ERRORS" "$WARNINGS" "$RESET" >&2
  printf 'Fix the errors above before relying on OOS development tooling.\n' >&2
  exit 1
elif [[ "$WARNINGS" -gt 0 ]]; then
  printf '%b%b%d warning(s)%b - environment partially ready\n' "$YELLOW" "$BOLD" "$WARNINGS" "$RESET" >&2
  printf 'OOS context loading can proceed, but some features may be limited.\n' >&2
  exit 0
else
  printf '%b%bAll checks passed%b - environment ready for OOS development\n' "$GREEN" "$BOLD" "$RESET" >&2
  exit 0
fi
