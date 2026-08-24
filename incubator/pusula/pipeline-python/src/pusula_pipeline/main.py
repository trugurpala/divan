"""Canonical Dagger pipeline for Divan Pusula.

GitHub Actions, Forgejo Actions, local development, and future runners call
these same functions. CI provider YAML remains a thin trigger only.
"""

import dagger
from dagger import dag, function, object_type


@object_type
class PusulaPipeline:
    @function
    async def backend(self, source: dagger.Directory) -> str:
        """Run the canonical backend contract against PostgreSQL 17.10."""
        postgres = (
            dag.container()
            .from_("postgres:17.10")
            .with_env_variable("POSTGRES_DB", "pusula")
            .with_env_variable("POSTGRES_USER", "pusula")
            .with_env_variable("POSTGRES_PASSWORD", "pusula-test")
            .with_exposed_port(5432)
            .as_service()
        )

        return await (
            dag.container()
            .from_("python:3.12-slim")
            .with_directory("/src", source)
            .with_workdir("/src")
            .with_service_binding("postgres", postgres)
            .with_env_variable("PUSULA_DB_NAME", "pusula")
            .with_env_variable("PUSULA_DB_USER", "pusula")
            .with_env_variable("PUSULA_DB_PASSWORD", "pusula-test")
            .with_env_variable("PUSULA_DB_HOST", "postgres")
            .with_env_variable("PUSULA_DB_PORT", "5432")
            .with_env_variable("PUSULA_DJANGO_SECRET_KEY", "dagger-test-only")
            .with_env_variable(
                "PUSULA_ALLOWED_HOSTS", "testserver,localhost,127.0.0.1"
            )
            .with_env_variable("PUSULA_DEBUG", "0")
            .with_exec(
                [
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "-r",
                    "incubator/pusula/backend/requirements.txt",
                ]
            )
            .with_exec(["python", "scripts/pusula_app_verify.py"])
            .stdout()
        )

    @function
    async def web(self, source: dagger.Directory) -> str:
        """Type-check and build the Pusula web application."""
        return await (
            dag.container()
            .from_("node:24-alpine")
            .with_directory("/src", source)
            .with_workdir("/src/incubator/pusula/web")
            .with_env_variable("VITE_LOGTO_ENDPOINT", "https://logto.invalid")
            .with_env_variable("VITE_LOGTO_APP_ID", "pusula-dagger")
            .with_env_variable(
                "VITE_PUSULA_API_RESOURCE", "https://api.pusula.invalid"
            )
            .with_exec(["npm", "install", "--no-audit", "--no-fund"])
            .with_exec(["npm", "run", "check"])
            .with_exec(["npm", "run", "build"])
            .stdout()
        )

    @function
    async def check(self, source: dagger.Directory) -> str:
        """Run the provider-neutral Pusula application verification pipeline."""
        backend_result = await self.backend(source)
        web_result = await self.web(source)
        return f"backend:\n{backend_result}\nweb:\n{web_result}"
