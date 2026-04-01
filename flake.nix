{
  description = "KCL Ticketing System flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        python = pkgs.python312;

        backendEnv = python.withPackages (ps: with ps; [
          django
          djangorestframework
          django-cors-headers
          djangorestframework-simplejwt
          dj-database-url
          faker
          python-dotenv
          requests
          httpx
          pillow
          psycopg2
          whitenoise
          gunicorn
          coverage
          cryptography
          cffi
          protobuf
          grpcio
          google-auth
          google-api-python-client
          google-generativeai
          openai
          reportlab
          tqdm
          pydantic
          typing-extensions
          sqlparse
          bleach
        ]);

        nodeEnv = pkgs.nodejs_20;

        commonInputs = [
          backendEnv
          nodeEnv
          pkgs.sqlite
          pkgs.libpq
          pkgs.openssl
          pkgs.libffi
          pkgs.zlib
          pkgs.git
        ];

        mkScript = name: text:
          pkgs.writeShellApplication {
            inherit name;
            runtimeInputs = commonInputs;
            text = ''
              set -e
              ${text}
            '';
          };

      in {
        packages = {

          init = mkScript "init" ''
            echo "== Backend setup =="

            echo "== Running migrations =="
            python manage.py migrate || true

            echo "== Seeding database =="
            python manage.py seed

            echo "== Frontend setup =="
            cd frontend

            if [ -f package-lock.json ]; then
              npm ci
            else
              npm install
            fi          

            cd ..

            echo "Initialization complete"
          '';

          run = mkScript "run" ''
            echo "Starting backend and frontend..."

            if [ -f .env ]; then
              set -a
              # shellcheck disable=SC1091
              source .env
              set +a
              echo "Loaded .env file!"
            fi

            (
              python manage.py runserver 0.0.0.0:8000
            ) &

            (
              cd frontend
              npm start
            ) &

            wait
          '';

          tests = mkScript "tests" ''
            echo "Running frontend + backend tests..."

            if [ -f package.json ]; then
              npm run test:run || true
              npm run test:coverage || true
            else
              echo "Fallback test execution"

              coverage run manage.py test
              coverage html

              cd frontend
              npm run test -- --coverage --watchAll=false || true
            fi       

            echo "Tests complete"
          '';

          seed = mkScript "seed" ''
            python manage.py seed
          '';

          unseed = mkScript "unseed" ''
            npm run unseed
          '';
        };

        apps = {
          init = flake-utils.lib.mkApp { drv = self.packages.${system}.init; };
          run = flake-utils.lib.mkApp { drv = self.packages.${system}.run; };
          tests = flake-utils.lib.mkApp { drv = self.packages.${system}.tests; };
          seed = flake-utils.lib.mkApp { drv = self.packages.${system}.seed; };
          unseed = flake-utils.lib.mkApp { drv = self.packages.${system}.unseed; };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = commonInputs;

          shellHook = ''
            if [ -f .env ]; then
              set -a
              # Load local env vars (including GEMINI_API_KEY) without committing secrets.
              source .env
              set +a
            fi

            if [ -n "$GEMINI_API_KEY" ]; then
              echo "Dev shell ready (GEMINI_API_KEY loaded)"
            else
              echo "Dev shell ready (GEMINI_API_KEY not set; AI chatbot remains optional)"
            fi
          '';
        };
      }
    );
}