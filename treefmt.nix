{
  projectRootFile = "flake.nix";
  programs = {
    deadnix.enable = true;
    nixfmt.enable = true;
    ruff-check.enable = true;
    ruff-format.enable = true;
    shellcheck.enable = true;
    shfmt.enable = true;
    statix.enable = true;
  };
  settings.formatter = {
    shfmt = {
      options = [ "-w" ];
      includes = [
        "*.sh"
        "**/*.sh"
        ".envrc"
        "**/.envrc"
      ];
    };
  };
}
