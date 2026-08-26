{
  description = "cocofarm: personal CocoIndex workflow";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";
    treefmt-nix.url = "github:numtide/treefmt-nix";
  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      treefmt-nix,
      ...
    }:
    let
      inherit (nixpkgs) lib;

      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
      ];

      eachSystem = lib.genAttrs systems;

      pkgsFor = eachSystem (system: import nixpkgs { inherit system; });

      packageNames = builtins.attrNames (
        lib.filterAttrs (
          name: type: type == "directory" && builtins.pathExists (./packages + "/${name}/package.nix")
        ) (builtins.readDir ./packages)
      );

      mkPackagesFor =
        pkgs:
        let
          scope = lib.makeScope pkgs.newScope (
            self:
            {
              inherit inputs lib;
            }
            // lib.genAttrs packageNames (name: self.callPackage (./packages + "/${name}/package.nix") { })
          );
        in
        lib.genAttrs packageNames (name: scope.${name});

      packages = eachSystem (system: mkPackagesFor pkgsFor.${system});

      treefmtEval = eachSystem (
        system:
        treefmt-nix.lib.evalModule pkgsFor.${system} {
          projectRootFile = "flake.nix";
          programs = {
            deadnix.enable = true;
            nixfmt.enable = true;
            ruff-check.enable = true;
            ruff-format.enable = true;
            statix.enable = true;
          };
        }
      );
    in
    {
      inherit packages;

      checks = eachSystem (
        system:
        lib.mapAttrs' (name: package: lib.nameValuePair "package-${name}" package) packages.${system}
        // {
          formatting = treefmtEval.${system}.config.build.check self;
        }
      );

      devShells = eachSystem (
        system:
        let
          pkgs = pkgsFor.${system};
          python = pkgs.python3.withPackages (_: [
            (pkgs.python3Packages.toPythonModule packages.${system}.cocoindex)
          ]);
        in
        {
          default = pkgs.mkShellNoCC {
            packages = [
              pkgs.gh
              pkgs.git
              pkgs.nix-output-monitor
              python
              treefmtEval.${system}.config.build.wrapper
            ];
          };
        }
      );

      formatter = eachSystem (system: treefmtEval.${system}.config.build.wrapper);
    };
}
