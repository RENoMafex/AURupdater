# AURupdater

> [!WARNING]
> Use at your own risk, this is just a hacked together script of someone who doesn't really know python. If you know, how to make this script better in any way, i'd appreciate pull requests!

<details>
<summary>tl;dr</summary>
Updates all your AUR packages, removes old tarballs and installs everything. Just drop the script into your AUR directory and run it.
</details>

If you have an AUR directory like me, you can simply use this script to update all your AUR packages in an easy way. All this script does is to check all direct subdirs for an `PKGBUILD` file. In every direct subdir where that file could be found updates will be pulled through `git`, after that the packages which need to be rebuilt are built using `makepkg`. After that all the packages get installed through `sudo pacman -U`.

## Example of how to use this script

Given the following example directory:

```
user@machine:~$ tree -L2 AUR
AUR
├── NotAPackage1
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
├── package4
│   ├── PKGBUILD
│   ├── .SRCINFO
│   └── LICENSE
├── package5
│   ├── PKGBUILD
│   └── .SRCINFO
├── package6
│   ├── PKGBUILD
│   └── .SRCINFO
└── update.py

```

You could now run the script by invoking `./update.py` inside the AUR directory.

## Acknowledgments

Special thanks to Jan, who would rather like to stay anonymous, for proofreading this script since i have no idea how to code in python.

## TODO

Implement cleanup before rebuild using `paccache -c directory -rvk1`
