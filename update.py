#!/usr/bin/env python3

import os
import subprocess
from sys import exit

RESET: str = "\033[0m"
BOLD: str = "\033[1m"

BLACK: str = "\033[30m"
RED: str = "\033[31m"
GREEN: str = "\033[32m"
YELLOW: str = "\033[33m"
BLUE: str = "\033[34m"
MAGENTA: str = "\033[35m"
CYAN: str = "\033[36m"
WHITE: str = "\033[37m"


# print colorized
def cprint(value: str = "", color: str = "") -> None:
	prefix: str = BOLD + color
	print(f"{prefix}{value}{RESET}")


# print a block
def bprint(value: str = "", color: str = "") -> None:
	cprint(len(value) * "-", color)
	cprint(value, color)
	cprint(len(value) * "-", color)


# dirty little helper function
def build(pkg: str) -> bool:
	cprint(CYAN + "Building " + GREEN + pkg)
	return subprocess.run("makepkg", cwd=pkg, check=False).returncode == 0


# make list of subdirs
bprint("Listing packages and pulling changes!", GREEN)
packages: set[str] = set()
for file in os.listdir():
	if os.path.isdir(file) and os.path.isfile(os.path.join(file, "PKGBUILD")):
		packages.add(file)

# pulliung changes
for pkg in packages:
	cprint(CYAN + "Pulling " + GREEN + pkg)
	_ = subprocess.run(["git", "pull"], cwd=pkg, check=False)
bprint("Pulled all packages, building packages!", GREEN)


# build packages
packages = {pkg for pkg in packages if build(pkg)}

# exit if nothing to do from here
if len(packages) == 0:
	bprint("No Packages to install, exiting!", RED)
	exit(0)

# getting tarball locations
installables: list[str] = []
for pkg in packages:
	installables.extend(
		subprocess.run(["makepkg", "--packagelist"], cwd=pkg, check=False, capture_output=True)
		.stdout.decode()
		.strip()
		.splitlines()
	)

# check if tarballs actually exist
installables = [pkg for pkg in installables if os.path.exists(pkg)]

# install packages from existing tarballs
_ = subprocess.run(["sudo", "pacman", "-U", *installables], check=False)

exit(0)
