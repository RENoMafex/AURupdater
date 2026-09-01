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
packages: list[str] = []
for file in os.listdir():
    if os.path.isdir(file) and os.path.isfile(os.path.join(file, "PKGBUILD")):
        packages.append(file)

# pulliung changes
for package in packages:
    print(
        colors.bold + colors.cyan + "Pulling " + colors.green + package + colors.default
    )
    _ = subprocess.run(["git", "pull"], cwd=package, check=False)

print(
    colors.bold
    + colors.cyan
    + "Pulled all packages, building packages!"
    + colors.default
)

# build packages
for package in packages:
    print(
        colors.bold
        + colors.cyan
        + "Building "
        + colors.green
        + package
        + colors.default
    )
    _ = subprocess.run("makepkg", cwd=package, check=False)

# getting tarball locations
installables: list[str] = []
for package in packages:
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
