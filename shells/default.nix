{ pkgs, perSystem }:
{
  default = import ./base.nix {
    inherit pkgs perSystem;
  };

  develop = import ./develop.nix {
    inherit pkgs perSystem;
  };
}
