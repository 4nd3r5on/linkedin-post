{
  description = "mcp-server-linkedin plus create_post and delete_post tools";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
      ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in
    {
      # uv owns the Python dependencies (uv.lock); Nix supplies the toolchain.
      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = [
            pkgs.python312
            pkgs.uv
          ];

          env = {
            # Use the Nix Python instead of letting uv download its own.
            UV_PYTHON = "${pkgs.python312}/bin/python3";
            UV_PYTHON_DOWNLOADS = "never";
          }
          // nixpkgs.lib.optionalAttrs pkgs.stdenv.isLinux {
            # Prebuilt manylinux wheels expect these on the loader path.
            LD_LIBRARY_PATH = nixpkgs.lib.makeLibraryPath [
              pkgs.stdenv.cc.cc.lib
              pkgs.zlib
            ];
          };

          # The ruff wheel is a prebuilt binary that needs /lib64/ld-linux, absent
          # on NixOS without nix-ld, so put nixpkgs' ruff ahead of the venv. Its
          # version must equal the ruff pin in pyproject.toml (select = ["ALL"]).
          # The browser-backed tests also need Chromium from `patchright install`,
          # which on NixOS needs nix-ld as well.
          shellHook = ''
            uv sync --locked
            source .venv/bin/activate
            export PATH=${pkgs.ruff}/bin:$PATH
          '';
        };
      });

      formatter = forAllSystems (pkgs: pkgs.nixfmt-rfc-style);
    };
}
