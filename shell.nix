let
  pkgs = import <nixpkgs> { config = { allowUnfree = true; }; };
in pkgs.mkShell {
  allowUnfree = true;
  packages = with pkgs; [
    go
    pdns
      consul
  ];
}
