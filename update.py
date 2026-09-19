#!/usr/bin/env python3

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

import argparse, os, shutil, subprocess  # noqa: I001
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

parser = argparse.ArgumentParser(
	description="Updates AUR packages in all subdirectories. Published under the MIT License. Copyright (c) 2026 Malte Schilling.",
)
parser.add_argument("-l", "--license", help="show license and exit", action="store_true")
options = parser.add_argument_group("update options", "These options affect the update steps")
options.add_argument("-f", "--rebuild", help="force rebuilding of all packages", action="store_true")
options.add_argument("-r", "--reinstall", help="force reinstallation of all found packages, even if not fresh rebuilt", action="store_true")
options.add_argument("-d", "--dirty", help="don't clean up old packages", action="store_true")
options.add_argument("-p", "--pacman", help=f"{f"{BOLD+UNDERLINE}don't{RESET}" if ALWAYS_UPGRADE_PACMAN_PACKAGES else "also"} upgrade all out-of-date pacman packages", action="store_true")
output = parser.add_argument_group("output options", "These options affect stdout AND stderr")
output.add_argument("-q", "--quiet", help="suppress output of tools (progress output still works)", action="store_true")
output.add_argument("-s", "--silent", help="suppress ALL output", action="store_true")
args = parser.parse_args()

if args.license:
	print("MIT License\n\nCopyright (c) 2026 Malte Schilling\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the \"Software\"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\nIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\nFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\nLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\nOUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\nSOFTWARE.")
	exit(0)

# redefine print to mute everything
if args.silent:
	def print(*args) -> None:
		pass
	args.quiet = True

if args.quiet:
	stdout: int | None = subprocess.PIPE
else:
	stdout = None

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
	bprint(f"Found {len(packages)} Packages! Pulling changes!", GREEN)
else:
	bprint("No Packages found, exiting!", RED)
	exit(0)

# pulliung changes
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
			build(pkg)
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
