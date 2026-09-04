#!/usr/bin/env python3

import os
import shutil
import subprocess
from subprocess import PIPE
from sys import exit

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
	_ = subprocess.run(["sudo", "pacman", "-S", *pacman_install], check=True)


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


# dirty little helper functions
def build(pkg: str) -> bool:
	# Builds package. Returns True if makepkg didnt have any errors and build the package successfully.
	cprint(CYAN + "Building " + GREEN + pkg)
	return subprocess.run("makepkg", cwd=pkg, check=False).returncode == 0


def pull(pkg: str) -> bool:
	# git-pull a repo. Returns True if there were changes.
	commit_hash: str = (
		subprocess.run(["git", "rev-parse", "HEAD"], cwd=pkg, check=False, stdout=PIPE)
		.stdout.decode()
		.splitlines()
		.pop()
	)
	_ = subprocess.run(["git", "pull"], cwd=pkg, check=False)
	return (
		commit_hash
		!= subprocess.run(["git", "rev-parse", "HEAD"], cwd=pkg, check=False, stdout=PIPE)
		.stdout.decode()
		.splitlines()
		.pop()
	)


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
bprint(f"Pulled {num_pulled} packages, {num_uptodate} were already up-to-date! building packages!", GREEN)

# build packages
built_packages: set[str] = {pkg for pkg in packages if build(pkg)}
bprint(f"Built {len(built_packages)} packages! Cleaning up!", GREEN)

# clean up
for pkg in packages:
	_ = subprocess.run(["paccache", "-c", ".", "-rvk1"], cwd=pkg, check=False)
bprint("Cleaning done!", GREEN)

# exit if nothing to do from here
if len(built_packages) == 0:
	bprint("No Packages to install, exiting!", RED)
	exit(0)

# getting tarball locations
installables: list[str] = []
for pkg in built_packages:
	installables.extend(
		subprocess.run(["makepkg", "--packagelist"], cwd=pkg, check=False, stdout=PIPE)
		.stdout.decode()
		.strip()
		.splitlines()
	)

# check if tarballs actually exist
installables = [pkg for pkg in installables if os.path.exists(pkg)]

# install packages from existing tarballs
if not subprocess.run(["sudo", "pacman", "-U", *installables], check=False).returncode:
	bprint(f"Installed {len(installables)} packages!", GREEN)
else:
	bprint("An Error occured. Check output for Infos.", RED)

exit(0)
