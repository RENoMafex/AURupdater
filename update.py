#!/usr/bin/env python3

import os
import subprocess
from sys import exit


# ansi escapes for coloring
class colors:
	default: str = "\033[0m"
	bold: str = "\033[1m"

	black: str = "\033[30m"
	red: str = "\033[31m"
	green: str = "\033[32m"
	yellow: str = "\033[33m"
	blue: str = "\033[34m"
	magenta: str = "\033[35m"
	cyan: str = "\033[36m"
	white: str = "\033[37m"

	# maybe a func to make the prints shorter? (cls.default needs to be called at the end of every print, every print uses bold, so maybe makes some lines shorter)


# make list of subdirs
print(colors.bold + colors.cyan + "Listing packages!" + colors.default)
returncode_per_package: dict[str, int] = {}
for file in os.listdir():
	if os.path.isdir(file) and os.path.isfile(os.path.join(file, "PKGBUILD")):
		returncode_per_package[file] = 0

# pulliung changes
for package in returncode_per_package:
	print(colors.bold + colors.cyan + "Pulling " + colors.green + package + colors.default)
	_ = subprocess.run(["git", "pull"], cwd=package, check=False)

print(colors.bold + colors.cyan + "Pulled all packages, building packages!" + colors.default)

# build packages
for package in returncode_per_package:
	print(colors.bold + colors.cyan + "Building " + colors.green + package + colors.default)
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
		subprocess.check_output(["makepkg", "--packagelist"], cwd=package)
		.decode()
		.strip()
		.splitlines()
	)

# check if tarballs actually exist
installables = [p for p in installables if os.path.exists(p)]

# install packages from existing tarballs
_ = subprocess.run(["sudo", "pacman", "-U", *installables], check=False)

exit(0)
