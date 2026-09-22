{
  lib,
  fetchFromGitHub,
  rustPlatform,
  python3Packages,
}:

python3Packages.buildPythonPackage (finalAttrs: {
  pname = "pdf-inspector";
  version = "1.23.0";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "firecrawl";
    repo = "pdf-inspector";
    tag = "v${finalAttrs.version}";
    hash = "sha256-QU946O1BJZicrBWoVQ+gQshOHxzQCRxSWDQhirLzw7g=";
  };

  cargoDeps = rustPlatform.importCargoLock {
    lockFile = ./Cargo.lock;
  };

  postPatch = ''
    cp ${./Cargo.lock} Cargo.lock
  '';

  nativeBuildInputs = [
    rustPlatform.cargoSetupHook
    rustPlatform.maturinBuildHook
  ];

  postBuild = ''
    cargo build --profile release --bins --no-default-features
  '';

  postInstall = ''
    install -Dm755 target/release/pdf2md "$out/bin/pdf2md"
    install -Dm755 target/release/detect-pdf "$out/bin/detect-pdf"
    install -Dm755 target/release/dump_ops "$out/bin/dump_ops"
  '';

  pythonImportsCheck = [ "pdf_inspector" ];

  doInstallCheck = true;
  installCheckPhase = ''
    runHook preInstallCheck

    python -c 'import pdf_inspector; assert callable(pdf_inspector.process_pdf)'
    pdf2md_status=0
    "$out/bin/pdf2md" --help >/dev/null 2>&1 || pdf2md_status=$?
    test "$pdf2md_status" -eq 1

    detect_status=0
    "$out/bin/detect-pdf" --help >/dev/null 2>&1 || detect_status=$?
    test "$detect_status" -eq 1

    runHook postInstallCheck
  '';

  passthru.updateScript = ./update.py;

  meta = {
    description = "PDF inspection, classification, and text extraction";
    homepage = "https://github.com/firecrawl/pdf-inspector";
    changelog = "https://github.com/firecrawl/pdf-inspector/releases/tag/v${finalAttrs.version}";
    license = lib.licenses.mit;
    mainProgram = "pdf2md";
    platforms = lib.platforms.unix;
  };
})
