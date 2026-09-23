# AURupdater
> [!WARNING]
> Use at your own risk, this is just a hacked together script of someone who doesn't really know python. If you know, how to make this script better in any way, i'd appreciate pull requests!

<details>
<summary>tl;dr</summary>
Updates all your AUR packages, removes old tarballs and installs everything. Just drop the script into your AUR directory and run it.
</details>

# Prerequisites
This script runs only under Linux distros, which use `pacman` (like Arch, CachyOS, EndeavourOS, Manjaro or SteamOS)
To run this script you will need the following tools: git, pacman, paccache, makepkg and python, as long as pacman and python are installed, the script will install all other needed tools for you. If python is not installed, call `sudo pacman -S python`

# About
If you have an AUR directory like me, you can simply use this script to update all your AUR packages in an easy way. All this script does is to check all direct subdirs for an `PKGBUILD` file. In every direct subdir where that file could be found updates will be pulled through `git`, after that the packages which need to be rebuilt are built using `makepkg`, if there are old tarballs, that are not needed anymore, they will get deleted. After that all the packages get installed through `sudo pacman -U`.

# Installation
Just drop the `update.py` script into your top level AUR directory.

# Usage
<details>
<summary>Given the following example directory: <ins>(click)</ins></summary>

```bash
user@machine:~$ tree -L1 AUR
AUR
├── NotAPackage/
├── package1/
├── package2/
├── package3/
└── update.py

user@machine:~$ tree -L2 AUR
AUR
├── NotAPackage
│   ├── somefile
│   └── someotherfile
├── package1
│   ├── PKGBUILD
│   ├── LICENSE
│   ├── README.md
│   ├── go.mod
│   ├── go.sum
│   └── src/
├── package2
│   ├── PKGBUILD
│   ├── LICENSE
│   ├── Makefile
│   ├── README.md
│   └── src/
├── package3
│   ├── PKGBUILD
│   └── .SRCINFO
└── update.py

user@machine:~$ cd AUR
user@machine:~/AUR$ ./update.py
# output of update.py here
```

</details>

You can run the script by invoking `./update.py` inside the AUR directory. It would update `package1`, `package2` and `package3` but not `NotAPackage`, because it has no `PKGBUILD` inside it.

## Launch options and settings
### Options
To see all available options call the script with the `-h` or the `--help` flag.

### Settings
At the top of the script you can change the standard behaviour of this script.

#### Include non-AUR packages
##### Don't upgrade non-AUR packages (standard behaviour)
```python
ALWAYS_UPGRADE_PACMAN_PACKAGES: bool = False
```

##### Also upgrade non-AUR packages
```python
ALWAYS_UPGRADE_PACMAN_PACKAGES: bool = True
```
> [!NOTE]
> the `-p` and the `--pacman` flags flip the behaviour of the `ALWAYS_UPGRADE_PACMAN_PACKAGES` constant. If you change the constant the help message gets updated accordingly automatically!

#### Admin tool
This script normally uses sudo to get root rights for needed actions. If you prefer other tools like for example `doas` you can simply change the constant to 
```python
ADMIN_TOOL: str = "doas"
```

# Acknowledgments
Special thanks to Jan, who would rather like to stay anonymous, for proofreading this script since i have no idea how to code in python.
