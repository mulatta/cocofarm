{
  lib,
  fetchFromGitHub,
  rustPlatform,
  python3Packages,
}:

python3Packages.buildPythonApplication (finalAttrs: {
  pname = "cocoindex";
  version = "1.0.20";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "cocoindex-io";
    repo = "cocoindex";
    tag = "v${finalAttrs.version}";
    hash = "sha256-gXRvEYxyr4YsuYF26BgFy0bTdKa76ruTwEwtWKqM2FA=";
  };

  cargoDeps = rustPlatform.fetchCargoVendor {
    inherit (finalAttrs) src;
    name = "${finalAttrs.pname}-${finalAttrs.version}";
    hash = "sha256-JT2GBl5XzRwnUfMFzaeGB2zE8XjZMxCM+tZ982LQlNg=";
  };

  postPatch = ''
    GITHUB_REF=refs/tags/v${finalAttrs.version} \
      ${python3Packages.python.interpreter} .github/scripts/update_version.py
  '';

  nativeBuildInputs = [
    rustPlatform.cargoSetupHook
    rustPlatform.maturinBuildHook
  ];

  dependencies = with python3Packages; [
    click
    msgspec
    numpy
    psutil
    python-dotenv
    rich
    typing-extensions
    watchdog
  ];

  pythonImportsCheck = [ "cocoindex" ];

  passthru.updateScript = ./update.py;

  meta = {
    description = "Data transformation framework for building real-time indexes";
    homepage = "https://cocoindex.io/";
    changelog = "https://github.com/cocoindex-io/cocoindex/releases/tag/v${finalAttrs.version}";
    license = lib.licenses.asl20;
    mainProgram = "cocoindex";
    platforms = lib.platforms.unix;
  };
})
