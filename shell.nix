let
  pkgs = import <nixpkgs> { config = { allowUnfree = true; }; };
in pkgs.mkShell {
  buildInputs = with pkgs; [
    python313
    python313Packages.venvShellHook

    pdns
    consul
  ];
  venvDir = "./.venv";
  postVenvCreation = ''
    unset SOURCE_DATE_EPOCH
  '';
  postShellHook = ''
    unset SOURCE_DATE_EPOCH
  '';
}
