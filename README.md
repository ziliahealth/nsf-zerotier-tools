Readme
======

Some zerotier admin tools to support [nixos-secure-factory] based projects.


Features
--------

### Zerotier network members management

 -  Authorizing a device to a zerotier network giving it a short name and a
    description:

    ```bash
    $ nixos-sf-zerotier network member authorize --name "my-device-short-name" --description "My description."
    Api token:
    Network id: 23958b0631e6f452
    Member id: 1b76419d42
    ```

    Note that the naming / description part required *Modify* privileges, so if you
    only have *Auth* privileges you will receive a the following warning:

    ```bash
    WARNING: Insufficient privileges to 'modify' network member 'name' field. Proceding with member authorization.
    ```

    The authorization part should however have been performed.

 -  Listing network members:

    ```bash
    $ nixos-sf-zerotier network member ls
    Api token:
    Network id: 23958b0631e6f452
    auth: True, id: 1b76419d42, ip: ['172.25.172.34'], name: "my-device-short-name", last-seen: "ONLINE", phys-ip: 24.37.197.186, desc: "My description."
    auth: False, id: 7cecb0fa96, ip: [], name: "", last-seen: "80d 23h 1388m 52s", phys-ip: 24.38.194.192, desc: ""
    auth: True, id: b8578b7853, ip: ['172.25.145.242'], name: "my-other-device-short-name", last-seen: "31d 17h 1036m 8s", phys-ip: 70.49.203.78, desc: "My other description."
    # ..
    ```

 -  Deauthorize a device from a zerotier network:

    ```bash
    $ nixos-sf-zerotier network member deauthorize
    Api token:
    Network id: 23958b0631e6f452
    Member id: 1b76419d42

    ```

 -  Listing network members filtered by online status and name:

    ```bash
    $ nixos-sf-zerotier network member ls --online --name "my-device"
    Api token:
    Network id: 23958b0631e6f452
    auth: False, id: 1b76419d42, ip: [], name: "my-device-short-name", last-seen: "ONLINE", phys-ip: 24.37.197.186, desc: "My description."
    ```


Prerequisites
-------------

 -  A posix system (e.g: Linux, Unix)
 -  [nix](https://nixos.org/nix/download.html)


Building and running
--------------------

```bash
$ nix build -f release.nix default
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


Contributing
------------

Contributing implies licensing those contributions under the terms of [LICENSE](./LICENSE), which is an *Apache 2.0* license.


[nixos-secure-factory]: https://github.com/jraygauthier/nixos-secure-factory
