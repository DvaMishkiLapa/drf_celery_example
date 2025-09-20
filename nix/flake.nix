{
  description = "DRF Celery example";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  };

  outputs = { self, nixpkgs }:
    let
      lib = nixpkgs.lib;
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      perSystem = system:
        let
          pkgs = import nixpkgs { inherit system; };
          pythonBase = pkgs.python312;
          postgresql = pkgs.postgresql_17;
          redis = pkgs.redis;
          processCompose = pkgs.process-compose;
          yamlWriter = pkgs.formats.yaml { };
          postgresPort = 5432;
          redisPort = 6379;
          webPortDefault = 8081;
          stateDirName = ".nix-state";

          renderText = src: vars:
            let
              keys = builtins.attrNames vars;
              placeholders = map (k: "@${k}@") keys;
              values = map (k: vars.${k}) keys;
            in lib.replaceStrings placeholders values (builtins.readFile src);

          commonScript = pkgs.writeText "common.sh" (renderText ./scripts/common.sh { });

          postgresRunner = pkgs.writeShellApplication {
            name = "postgres-runner";
            runtimeInputs = [ postgresql pkgs.coreutils ];
            text = renderText ./scripts/postgres-runner.sh {
              state_dir = stateDirName;
              postgres_port = toString postgresPort;
            };
          };

          redisRunner = pkgs.writeShellApplication {
            name = "redis-runner";
            runtimeInputs = [ redis pkgs.coreutils ];
            text = renderText ./scripts/redis-runner.sh {
              state_dir = stateDirName;
              redis_port = toString redisPort;
            };
          };

          migrateRunner = pkgs.writeShellApplication {
            name = "migrate-runner";
            runtimeInputs = [ pkgs.uv pkgs.coreutils pkgs.bash pythonBase postgresql ];
            text = renderText ./scripts/migrate-runner.sh {
              state_dir = stateDirName;
              postgres_port = toString postgresPort;
              common = toString commonScript;
            };
          };

          appRunner = pkgs.writeShellApplication {
            name = "app-runner";
            runtimeInputs = [ pkgs.bash pkgs.coreutils ];
            text = ''
              set -euo pipefail

              default_port=${toString webPortDefault}
              web_port="''${NIX_DAPHNE_PORT:-$default_port}"
              exec daphne \
                -b 0.0.0.0 \
                -p "$web_port" \
                app.asgi:application \
                --http-timeout 30 \
                --verbosity 0
            '';
          };

          processComposeConfig = yamlWriter.generate "process-compose.yaml" {
            version = "0.5";
            processes = {
              postgres = {
                command = "${postgresRunner}/bin/postgres-runner";
                availability = { restart = "always"; };
                readiness_probe = {
                  exec.command = "${postgresql}/bin/pg_isready -h 127.0.0.1 -p ${toString postgresPort}";
                  initial_delay_seconds = 2;
                  period_seconds = 3;
                  timeout_seconds = 2;
                  success_threshold = 1;
                  failure_threshold = 5;
                };
                environment = [
                  "POSTGRES_HOST=127.0.0.1"
                  "PGHOST=127.0.0.1"
                  "PGPORT=${toString postgresPort}"
                ];
                working_dir = ".";
              };

              redis = {
                command = "${redisRunner}/bin/redis-runner";
                availability = { restart = "always"; };
                readiness_probe = {
                  exec.command = "${redis}/bin/redis-cli -h 127.0.0.1 -p ${toString redisPort} ping";
                  initial_delay_seconds = 1;
                  period_seconds = 5;
                  timeout_seconds = 2;
                  success_threshold = 1;
                  failure_threshold = 5;
                };
                environment = [
                  "REDIS_HOST=127.0.0.1"
                ];
                working_dir = ".";
              };

              migrate = {
                command = "${migrateRunner}/bin/migrate-runner";
                availability = { restart = "no"; };
                depends_on = {
                  postgres = { condition = "process_healthy"; };
                };
                environment = [
                  "DJANGO_SETTINGS_MODULE=app.settings"
                  "POSTGRES_HOST=127.0.0.1"
                  "CELERY_BROKER_URL=redis://127.0.0.1:${toString redisPort}/0"
                  "CELERY_RESULT_BACKEND=redis://127.0.0.1:${toString redisPort}/1"
                  "CACHE_URL=redis://127.0.0.1:${toString redisPort}/2"
                ];
                working_dir = ".";
              };

              app = {
                command = "${appRunner}/bin/app-runner";
                availability = { restart = "always"; };
                depends_on = {
                  postgres = { condition = "process_healthy"; };
                  redis = { condition = "process_healthy"; };
                  migrate = { condition = "process_completed_successfully"; };
                };
                environment = [
                  "DJANGO_SETTINGS_MODULE=app.settings"
                  "POSTGRES_HOST=127.0.0.1"
                  "API_HOST=localhost"
                  "CELERY_BROKER_URL=redis://127.0.0.1:${toString redisPort}/0"
                  "CELERY_RESULT_BACKEND=redis://127.0.0.1:${toString redisPort}/1"
                  "CACHE_URL=redis://127.0.0.1:${toString redisPort}/2"
                ];
                working_dir = ".";
              };

              worker = {
                command = lib.concatStringsSep " " [
                  "celery"
                  "-A"
                  "app"
                  "worker"
                  "--loglevel=info"
                ];
                availability = { restart = "always"; };
                depends_on = {
                  postgres = { condition = "process_healthy"; };
                  redis = { condition = "process_healthy"; };
                  migrate = { condition = "process_completed_successfully"; };
                  app = { condition = "process_started"; };
                };
                environment = [
                  "DJANGO_SETTINGS_MODULE=app.settings"
                  "POSTGRES_HOST=127.0.0.1"
                  "CELERY_BROKER_URL=redis://127.0.0.1:${toString redisPort}/0"
                  "CELERY_RESULT_BACKEND=redis://127.0.0.1:${toString redisPort}/1"
                  "CACHE_URL=redis://127.0.0.1:${toString redisPort}/2"
                ];
                working_dir = ".";
              };

              beat = {
                command = lib.concatStringsSep " " [
                  "celery"
                  "-A"
                  "app"
                  "beat"
                  "--loglevel=info"
                  "--scheduler"
                  "django_celery_beat.schedulers:DatabaseScheduler"
                ];
                availability = { restart = "always"; };
                depends_on = {
                  postgres = { condition = "process_healthy"; };
                  redis = { condition = "process_healthy"; };
                  migrate = { condition = "process_completed_successfully"; };
                };
                environment = [
                  "DJANGO_SETTINGS_MODULE=app.settings"
                  "POSTGRES_HOST=127.0.0.1"
                  "CELERY_BROKER_URL=redis://127.0.0.1:${toString redisPort}/0"
                  "CELERY_RESULT_BACKEND=redis://127.0.0.1:${toString redisPort}/1"
                  "CACHE_URL=redis://127.0.0.1:${toString redisPort}/2"
                ];
                working_dir = ".";
              };
            };
          };


          baseRuntimeInputs = [ pkgs.uv pkgs.coreutils pkgs.bash pythonBase postgresql processCompose ];

          runtimeScript = pkgs.writeTextFile {
            name = "runtime.sh";
            executable = true;
            text = renderText ./scripts/runtime.sh {
              state_dir = stateDirName;
              postgres_port = toString postgresPort;
              process_compose_config = toString processComposeConfig;
              common = toString commonScript;
              web_port_default = toString webPortDefault;
            };
          };

          initDbScript = pkgs.writeShellApplication {
            name = "init-db";
            runtimeInputs = baseRuntimeInputs;
            text = ''
              exec ${runtimeScript} init-db "$@"
            '';
          };

          stackScript = pkgs.writeShellApplication {
            name = "stack";
            runtimeInputs = baseRuntimeInputs;
            text = ''
              exec ${runtimeScript} stack "$@"
            '';
          };

        in
        {
          devShell = pkgs.mkShell {
            packages = [ pkgs.uv processCompose postgresql redis pkgs.coreutils ];
            inputsFrom = [ pythonBase ];
            shellHook = ''
              echo "nix run .#stack      # start postgres, redis, web, celery worker & beat"
              echo "nix run .#init-db    # run after stack is up (creates DB and applies migrations)"
            '';
          };

          packages = {
            stack = stackScript;
            init-db = initDbScript;
          };

          apps = {
            stack = {
              type = "app";
              program = "${stackScript}/bin/stack";
            };
            init-db = {
              type = "app";
              program = "${initDbScript}/bin/init-db";
            };
          };
        };
    in
    {
      devShells = lib.genAttrs systems (system: { default = (perSystem system).devShell; });
      packages = lib.genAttrs systems (system: (perSystem system).packages);
      apps = lib.genAttrs systems (system: (perSystem system).apps);
    };
}
