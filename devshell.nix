{ pkgs, formatter }:

pkgs.mkShellNoCC {
  packages = [
    pkgs.gh
    pkgs.git
    pkgs.nix-output-monitor
    pkgs.python3
    formatter
  ];
}
