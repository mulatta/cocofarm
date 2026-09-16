{ pkgs, perSystem }:
let
  inherit (perSystem.self) cocoindex formatter;
  pythonEnv = pkgs.python3.withPackages (_: [ cocoindex ]);
in
pkgs.mkShellNoCC {
  packages = [
    pkgs.coreutils
    pkgs.git
    cocoindex
    formatter
    pythonEnv
  ];

  PYTHON_ENV = pythonEnv;

  shellHook = ''
    REPO_ROOT="$(git rev-parse --show-toplevel)"
    export REPO_ROOT

    skills_dir="$REPO_ROOT/.agents/skills"
    skill_source="${cocoindex}/share/skills/cocoindex/cocoindex"
    skill_target="$skills_dir/cocoindex"

    mkdir -p "$skills_dir"
    rm -rf -- "$skill_target"
    mkdir -p "$skill_target"

    (
      shopt -s dotglob nullglob
      for entry in "$skill_source"/*; do
        ln -s "$entry" "$skill_target/"
      done
    )
  '';
}
