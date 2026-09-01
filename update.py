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


# make list of subdirs
cprint("Listing packages!", cyan)
returncode_per_package: dict[str, int] = {}
for file in os.listdir():
	if os.path.isdir(file) and os.path.isfile(os.path.join(file, "PKGBUILD")):
		returncode_per_package[file] = 0

# pulliung changes
for package in returncode_per_package:
	cprint(cyan + "Pulling " + green + package)
	_ = subprocess.run(["git", "pull"], cwd=package, check=False)

cprint(cyan + "Pulled all packages, building packages!")

# build packages
for package in returncode_per_package:
	cprint(cyan + "Building " + green + package)
	returncode_per_package[package] = subprocess.run("makepkg", cwd=package, check=False).returncode

# remove failed packages from dict
num_items: int = 0
to_remove: list[str] = []
for package, returncode in returncode_per_package.items():
	if returncode == 0:
		num_items += 1
	else:
		to_remove.append(package)
for package in to_remove:
	_ = returncode_per_package.pop(package)

# exit if nothing to do from here
if num_items == 0:
	exit(0)

# getting tarball locations
installables: list[str] = []
for package in returncode_per_package:
	installables.extend(
		subprocess.check_output(["makepkg", "--packagelist"], cwd=package).decode().strip().splitlines()
	)

# check if tarballs actually exist
installables = [p for p in installables if os.path.exists(p)]

# install packages from existing tarballs
_ = subprocess.run(["sudo", "pacman", "-U", *installables], check=False)

exit(0)
