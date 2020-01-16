Readme
======

Some zerotier admin tools to support [nixos-secure-factory] based projects.


Prerequisites
-------------

 -  A posix system (e.g: Linux, Unix)
 -  [nix](https://nixos.org/nix/download.html)


Building and running
--------------------

```bash
$ nix build -f release.nix
# ..
$ ./result/bin/nixos-sf-zerotier --help
# TODO: Helper output here
```


Entering a user environment
---------------------------

This is an environment that simulates the conditions occurring when this
application is installed on a system. For example it allows one to test packaged
shell completions (bash / zsh / etc).

```bash
$ nix-shell env.nix
# ..
$ nixos-sf-zerotier --help
# .. (same as above)
$ nixos-sf-zerotier [Hit Tab Here]
```


Entering a development environment
----------------------------------

```bash
$ cd /this/directory
# ..
$ nix-shell
# ..
$ nixos-sf-zerotier --help
# .. (same as above)
```


Updating the dependencies
-------------------------

```bash
$ ./update_nix_requirements.sh
# ..
```

Both `requirements.nix` and `requirements_frozen.txt` should have been updated.


[nixos-secure-factory]: https://github.com/jraygauthier/nixos-secure-factory
