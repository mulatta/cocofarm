{ pkgs, perSystem }:

pkgs.mkShellNoCC {
  packages = [
    pkgs.gh
    pkgs.git
    pkgs.nix-output-monitor
    pkgs.python3
    perSystem.self.formatter
  ];
}
