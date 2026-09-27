#!/usr/bin/env python3
# pyright: reportAny=false

#####################################
# BEGIN OF SETTINGS FOR THIS SCRIPT #
#####################################

# Also update non-AUR packages in pacman? (Can be flipped with "-p / --pacman" flags).
ALWAYS_UPGRADE_PACMAN_PACKAGES: bool = False

# Tool to use for admin access (some people prefer other tools like doas or vsys)
ADMIN_TOOL: str = "sudo"

###################################
# END OF SETTINGS FOR THIS SCRIPT #
###################################

import argparse, os, pathlib, shutil, subprocess, textwrap  # noqa: I001
from sys import exit

if __name__ != "__main__":
	print("NOT A MODULE! CALL SCRIPT DIRECTLY")
	exit(1)

RESET: str = "\033[0m"
BOLD: str = "\033[1m"
UNDERLINE: str = "\033[4m"

BLACK: str = "\033[30m"
RED: str = "\033[31m"
GREEN: str = "\033[32m"
YELLOW: str = "\033[33m"
BLUE: str = "\033[34m"
MAGENTA: str = "\033[35m"
CYAN: str = "\033[36m"
WHITE: str = "\033[37m"

# Make scripts in own files and copy them here
SCRIPTS: dict[str, str] = {
	"BASH": textwrap.dedent(r"""	#!/usr/bin/env bash
		_update.py_complete() {
			local cur prev
			COMPREPLY=()
			cur="${COMP_WORDS[COMP_CWORD]}"
			prev="${COMP_WORDS[COMP_CWORD-1]}"
			case "$prev" in
				--completion)
					COMPREPLY=( $(compgen -W "bash zsh fish all" -- "$cur") )
					return 0
					;;
				--admintool)
					COMPREPLY=( $(compgen -c -- "$cur") )
					return 0
					;;
			esac
			COMPREPLY=( $(compgen -W "--help -h --license -l --repo --completion --check -c --rebuild -f --reinstall -r --dirty -d --pacman -p --admintool --quiet -q --silent -s" -- "$cur") )
		}
		complete -F _update.py_complete update.py update
	"""),
	"ZSH": textwrap.dedent(r"""	#compdef update.py update
		_arguments \
			'(-h --help)'{-h,--help}'[Show this help message and exit]' \
			'(-l --license)'{-l,--license}'[Show license and exit]' \
			'--repo[Show link to source and exit]' \
			'--completion[Install tab-completion for your shell and exit]:shell:(bash zsh fish all)' \
			'(-c --check)'{-c,--check}'[Only check for updates]' \
			'(-f --rebuild)'{-f,--rebuild}'[Force rebuilding of all packages]' \
			'(-r --reinstall)'{-r,--reinstall}'[Force reinstallation of all found packages, even if not fresh rebuilt]' \
			'(-d --dirty)'{-d,--dirty}'[Do not clean up old packages]' \
			'(-p --pacman)'{-p,--pacman}'[Also upgrade all out-of-date pacman packages]' \
			'--admintool[Choose another privilege tool (like "sudo" or "doas"), default is sudo]:tool:_command_names -e' \
			'(-q --quiet)'{-q,--quiet}'[Suppress output of tools (progress output still works)]' \
			'(-s --silent)'{-s,--silent}'[Suppress ALL output]'
	"""),
	"FISH": textwrap.dedent(r"""	#!/usr/bin/env fish
		complete -c update.py -f
		complete -c update.py -l completion -d "Install tab-completion for your shell" -x -a "bash zsh fish all"
		complete -c update.py -s h -l help -d "Show this help message and exit"
		complete -c update.py -s l -l license -d "Show license and exit"
		complete -c update.py -l repo -d "Show link to source and exit"
		complete -c update.py -s c -l check -d "Only check for updates"
		complete -c update.py -s f -l rebuild -d "Force rebuilding of all packages"
		complete -c update.py -s r -l reinstall -d "Force reinstallation of all found packages, even if not fresh rebuilt"
		complete -c update.py -s d -l dirty -d "Do not clean up old packages"
		complete -c update.py -s p -l pacman -d "Also upgrade all out-of-date pacman packages"
		complete -c update.py -l admintool -d "Choose another privilege tool, default is sudo" -x -a "(__fish_complete_command)"
		complete -c update.py -s q -l quiet -d "Suppress output of tools (progress output still works)"
		complete -c update.py -s s -l silent -d "Suppress ALL output"

		complete -c update -f
		complete -c update -w update.py
	"""),
}

# function definitions
# print colorized
def cprint(value: str = "", color: str = "") -> None:
	prefix: str = BOLD + color
	print(f"{prefix}{value}{RESET}")

# print a block
def bprint(value: str = "", color: str = "") -> None:
	cprint(len(value) * "-", color)
	cprint(value, color)
	cprint(len(value) * "-", color)

# dirty little helper functions
def build(pkg: str) -> bool:
	# Builds package. Returns True if makepkg didnt have any errors and build the package successfully.
	cprint(CYAN + "Building " + GREEN + pkg)
	return subprocess.run("makepkg", cwd=pkg, check=False, stdout=stdout, stderr=stdout).returncode == 0

def unconditional_build(pkg: str) -> bool:
	cprint(CYAN + "Building " + GREEN + pkg)
	return subprocess.run(["makepkg", "-f"], cwd=pkg, check=False, stdout=stdout, stderr=stdout).returncode == 0

def pull(pkg: str) -> bool:
	# git-pull a repo. Returns True if there were changes.
	commit_hash: str = (
		subprocess.run(["git", "rev-parse", "HEAD"], cwd=pkg, check=False, stdout=subprocess.PIPE)
		.stdout.decode()
		.splitlines()
		.pop()
	)
	_ = subprocess.run(["git", "pull"], cwd=pkg, check=False, stdout=stdout, stderr=stdout)
	commit_hash_new: str = (
		subprocess.run(["git", "rev-parse", "HEAD"], cwd=pkg, check=False, stdout=subprocess.PIPE)
		.stdout.decode()
		.splitlines()
		.pop()
	)
	return commit_hash != commit_hash_new

def check(pkg: str) -> bool:
	# check remote for updates. Returns True if there were changes.
	commit_hash: str = (
		subprocess.run(["git", "rev-parse", "HEAD"], cwd=pkg, check=False, stdout=subprocess.PIPE)
		.stdout.decode()
		.splitlines()
		.pop()
	)
	origin_name: str = subprocess.run(["git", "remote", "show"], cwd=pkg, check=False, stdout=subprocess.PIPE).stdout.decode().strip().splitlines()[0]
	commit_hash_new: str = (
		subprocess.run(["git", "rev-parse", origin_name], cwd=pkg, check=False, stdout=subprocess.PIPE)
		.stdout.decode()
		.splitlines()
		.pop()
	)
	return commit_hash != commit_hash_new

parser = argparse.ArgumentParser(
	description="Updates AUR packages in all subdirectories. Published under the MIT License. Copyright (c) 2026 Malte Schilling.",
	add_help=False
)
ST: str = "store_true"
informative = parser.add_argument_group("Informative options", "These options show informations about this script")
_ = informative.add_argument("-h", "--help", help="Show this help message and exit", action=ST)
_ = informative.add_argument("-l", "--license", help="Show license and exit", action=ST)
_ = informative.add_argument("--repo", help="Show link to source and exit", action=ST)
_ = informative.add_argument("--help-check", help=argparse.SUPPRESS, action=ST)
_ = informative.add_argument("--completion", help="Install tab-completion for your shell and exit", choices=["bash", "zsh", "fish", "all"])
options = parser.add_argument_group("Update options", "These options affect the update steps")
_ = options.add_argument("-c", "--check", help="Only check for updates. For further info use the \"--help-check\" flag", action=ST)
_ = options.add_argument("-f", "--rebuild", help="Force rebuilding of all packages", action=ST)
_ = options.add_argument("-r", "--reinstall", help="Force reinstallation of all found packages, even if not fresh rebuilt", action=ST)
_ = options.add_argument("-d", "--dirty", help="Don't clean up old packages", action=ST)
_ = options.add_argument("-p", "--pacman", help=f"{f"{BOLD+UNDERLINE}Don't{RESET}" if ALWAYS_UPGRADE_PACMAN_PACKAGES else "Also"} upgrade all out-of-date pacman packages", action=ST)
_ = options.add_argument("--admintool", help=f"Choose another privilege tool (like \"sudo\" or \"doas\"), the default is {ADMIN_TOOL}", metavar="TOOL")
output = parser.add_argument_group("Output options", "These options affect stdout AND stderr")
_ = output.add_argument("-q", "--quiet", help="Suppress output of tools (progress output still works)", action=ST)
_ = output.add_argument("-s", "--silent", help="Suppress ALL output", action=ST)
args = parser.parse_args()

if args.help_check:
	print(f"The -c or --check flag checks the local repo against the first remote listed by \"git remote show\".\nTo easily use the output of the check in other scripts/programs run it together with the silent option,\nthis makes the number of packages that have changes in the remote repo the returncode of this script.\n\n{BOLD}examples:{RESET}\n{parser.prog} -cs\n{parser.prog} --silent --check")
	exit(0)

if args.help:
	parser.print_help()
	if not args.repo and not args.license:
		exit(0)
	else:
		print()

if args.repo:
	print(UNDERLINE + "https://github.com/RENoMafex/AURupdater" + RESET)
	if not args.license:
		exit(0)
	else:
		print()

if args.license:
	print("MIT License\n\nCopyright (c) 2026 Malte Schilling\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the \"Software\"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\nIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\nFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\nLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\nOUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\nSOFTWARE.")
	exit(0)

# redefine print to mute everything
if args.silent:
	def print(*_a, **_b) -> None:  #pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
		pass
	args.quiet = True

if args.quiet:
	stdout: int | None = subprocess.PIPE
else:
	stdout = None

if args.admintool:
	if not shutil.which(args.admintool):
		print(f"{args.admintool} is not in your PATH.")
		exit(1)
	# redefinition if "--admintool" is set
	ADMIN_TOOL = args.admintool  # pyright: ignore[reportConstantRedefinition]
	print(f"{BOLD}Note:{RESET} You used the \"--admintool\" option. If you want to change the tool permanently you should change the \"ADMIN_TOOL\" constant at the top of this script!\n")

if args.completion:
	if args.completion in ["bash", "all"]:
		bash_dir: pathlib.Path = pathlib.Path(f"{os.getenv("HOME")}/.local/share/bash-completion/completions")
		_ = subprocess.run(["mkdir", "-p", bash_dir], check=False)
		_ = (bash_dir / "update.py").write_text(SCRIPTS["BASH"])
		bprint("Installed autocompletion for bash", GREEN)
	if args.completion in ["zsh", "all"]:
		zsh_dir: pathlib.Path = pathlib.Path(f"{os.getenv("HOME")}/.zfunc")
		_ = subprocess.run(["mkdir", "-p", zsh_dir], check=False)
		_ = (zsh_dir / "_update.py").write_text(SCRIPTS["ZSH"])
		bprint("Installed autocompletion for zsh", GREEN)
	if args.completion in ["fish", "all"]:
		fish_dir: pathlib.Path = pathlib.Path(f"{os.getenv("HOME")}/.config/fish/completions")
		_ = subprocess.run(["mkdir", "-p", fish_dir], check=False)
		_ = (fish_dir / "update.py.fish").write_text(SCRIPTS["FISH"])
		bprint("Installed autocompletion for fish", GREEN)
	exit(0)

# check if all needed programs are installed
if not shutil.which("pacman"):
	print(
		'You haven\'t got "pacman" installed. Chances that this script will not work at all on your system are very high!\n'
		+ 'Please make sure you have "pacman" installed!'
	)
	exit(1)
pacman_install: list[str] = []
if not shutil.which("git"):
	pacman_install.append("git")
if not shutil.which("paccache"):
	pacman_install.append("pacman-contrib")
if len(pacman_install):
	print(f"Need to install following package(s): {' '.join(pacman_install)}")
	_ = subprocess.run([ADMIN_TOOL, "pacman", "-S", *pacman_install], check=True, stdout=stdout, stderr=stdout)

###################
# BEGIN OF SCRIPT #
###################

# make list of subdirs
bprint("Listing packages!", GREEN)
packages: set[str] = set()
for file in os.listdir():
	if os.path.isdir(file) and os.path.isfile(os.path.join(file, "PKGBUILD")):
		packages.add(file)

if len(packages):
	bprint(f"Found {len(packages)} Packages! Looking for changes!", GREEN)
else:
	bprint("No Packages found, exiting!", RED)
	exit(0)

# pulliung changes
if args.check:
	changes: int = 0
	for pkg in packages:
		changes += check(pkg)
	if args.silent:
		exit(changes)
	else:
		bprint(f"Found {changes} changed package repos!", GREEN)
		exit(0)


num_pulled: int = 0
num_uptodate: int = 0
for pkg in packages:
	cprint(CYAN + "Pulling " + GREEN + pkg)
	pullresult: bool = pull(pkg)
	num_pulled += pullresult
	num_uptodate += not pullresult
bprint(f"Pulled {num_pulled} packages, {num_uptodate} were already up-to-date! Building packages!", GREEN)

# build packages
built_packages: set[str] = set()
if args.rebuild:
	built_packages = {pkg for pkg in packages if unconditional_build(pkg)}
else:
	if args.reinstall:
		for pkg in packages:
			_ = build(pkg)
			built_packages = set(packages)
	else:
		built_packages = {pkg for pkg in packages if build(pkg)}
bprint(f"Built {len(built_packages)} packages!", GREEN)

# clean up
if not args.dirty:
	for pkg in packages:
		_ = subprocess.run(["paccache", "-c", ".", "-rvk1"], cwd=pkg, check=False, stdout=stdout, stderr=stdout)
	bprint("Cleaning done!", GREEN)

# exit if nothing to do from here
if len(built_packages) == 0:
	bprint("No Packages to install, exiting!", RED)
	exit(0)

# getting tarball locations
installables: list[str] = []
for pkg in built_packages:
	installables.extend(
		subprocess.run(["makepkg", "--packagelist"], cwd=pkg, check=False, stdout=subprocess.PIPE)
		.stdout.decode()
		.strip()
		.splitlines()
	)

# check if tarballs actually exist
installables = [pkg for pkg in installables if os.path.exists(pkg)]

# install packages from existing tarballs
if not subprocess.run([ADMIN_TOOL, "pacman", "-U", *installables], check=False, stdout=stdout, stderr=stdout).returncode:
	bprint(f"Installed {len(installables)} packages!", GREEN)
else:
	bprint("An Error occured. Check output for Infos.", RED)

if ALWAYS_UPGRADE_PACMAN_PACKAGES != args.pacman: # != used as xor basically
	bprint("AUR upgrades finished, upgrading pacman packages now!", GREEN)
	_ = subprocess.run([ADMIN_TOOL, "pacman", "-Syu"], check=False, stdout=stdout, stderr=stdout)

exit(0)
