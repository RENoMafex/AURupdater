#!/usr/bin/env python3

import os
import subprocess
from sys import exit

reset: str = "\033[0m"
bold: str = "\033[1m"

black: str = "\033[30m"
red: str = "\033[31m"
green: str = "\033[32m"
yellow: str = "\033[33m"
blue: str = "\033[34m"
magenta: str = "\033[35m"
cyan: str = "\033[36m"
white: str = "\033[37m"


def cprint(value: str = "", color: str = "") -> None:
	prefix: str = bold + color
	print(f"{prefix}{value}{reset}")


def build(pkg: str):
	cprint(cyan + "Building " + green + pkg)
	return subprocess.run("makepkg", cwd=pkg, check=False).returncode == 0


# make list of subdirs
cprint("-------------------------------------", green)
cprint("Listing packages and pulling changes!", green)
cprint("-------------------------------------", green)
packages: set[str] = set()
for file in os.listdir():
	if os.path.isdir(file) and os.path.isfile(os.path.join(file, "PKGBUILD")):
		packages.add(file)

# pulliung changes
for pkg in packages:
	cprint(cyan + "Pulling " + green + pkg)
	_ = subprocess.run(["git", "pull"], cwd=pkg, check=False)
cprint("---------------------------------------", green)
cprint("Pulled all packages, building packages!", green)
cprint("---------------------------------------", green)

# build packages
packages = {pkg for pkg in packages if build(pkg)}

# exit if nothing to do from here
if len(packages) == 0:
	cprint("--------------------------------", red)
	cprint("No Packages to install, exiting!", red)
	cprint("--------------------------------", red)
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
