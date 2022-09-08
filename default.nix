{ pkgs, lib, buildPythonPackage, mypy, pytest, click, requests, python-dateutil }:

let
  zerotier = buildPythonPackage {
    name = "zerotier-1.1.2";
    src = pkgs.fetchurl {
      url = "https://files.pythonhosted.org/packages/21/05/0036c2af4aa20fbb8fe666aa7a54e819a4937030b3a550f335304bed5601/zerotier-1.1.2.tar.gz";
      sha256 = "1b7587bb1e5659edc4b143248b75f5c98403953652c1bac2680579992abd12c1";
    };
    doCheck = false;
    buildInputs = [ ];
    propagatedBuildInputs = [
      requests
    ];
    meta = {
      homepage = "https://github.com/zero-os/zerotier_client";
      license = lib.licenses.asl20;
      description = "Zerotier API client";
    };
  };
in
buildPythonPackage rec {
  pname = "nsf-zerotier-tools";
  version = "0.1.0";
  name = "${pname}-${version}";
  src = pkgs.nix-gitignore.gitignoreSourcePure ./.gitignore ./.;
  buildInputs = [ ];
  checkInputs = [
    mypy
    pytest
  ];
  propagatedBuildInputs = [
    click
    zerotier
    python-dateutil
  ];

  postInstall = ''
    click_exes=( "nsf-zerotier" )

    buildPythonPath "$out"

    # Install click application bash completions.
    bash_completion_dir="$out/share/bash-completion/completions"
    mkdir -p "$bash_completion_dir"
    for e in "''${click_exes[@]}"; do
      click_exe_path="$out/bin/$e"
      patchPythonScript "$click_exe_path"
      wrapProgram "$click_exe_path" --prefix PATH ':' "$program_PATH"
      click_complete_env_var_name="_$(echo "$e" | tr "[a-z-]" "[A-Z_]")_COMPLETE"
      # TODO: For some reason, running this return a non zero (1) status code. This might
      # be a click library bug. Fill one if so.
      env "''${click_complete_env_var_name}=bash_source" "$click_exe_path" > "$bash_completion_dir/$e" || true
      # Because of the above, check that we got some completion code in the file.
      cat "$bash_completion_dir/$e" | grep "$click_complete_env_var_name" > /dev/null
    done
  '';

  # Allow nix-shell inside nix-shell.
  # See `pkgs/development/interpreters/python/hooks/setuptools-build-hook.sh`
  # for the reason why.
  shellHook = ''
    setuptoolsShellHook
  '';
}
