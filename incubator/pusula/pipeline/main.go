// Pusula's canonical CI pipeline.
//
// The module intentionally keeps CI business logic provider-neutral. GitHub
// Actions, Forgejo Actions, local development, and future runners call these
// same Dagger functions instead of re-implementing checks in YAML.
package main

import (
	"context"
	"dagger/pusula-pipeline/internal/dagger"
	"fmt"
)

type PusulaPipeline struct{}

func (m *PusulaPipeline) Backend(ctx context.Context, source *dagger.Directory) (string, error) {
	postgres := dag.Container().
		From("postgres:17.10").
		WithEnvVariable("POSTGRES_DB", "pusula").
		WithEnvVariable("POSTGRES_USER", "pusula").
		WithEnvVariable("POSTGRES_PASSWORD", "pusula-test").
		WithExposedPort(5432).
		AsService()

	container := dag.Container().
		From("python:3.12-slim").
		WithMountedDirectory("/src", source).
		WithWorkdir("/src").
		WithServiceBinding("postgres", postgres).
		WithEnvVariable("PUSULA_DB_NAME", "pusula").
		WithEnvVariable("PUSULA_DB_USER", "pusula").
		WithEnvVariable("PUSULA_DB_PASSWORD", "pusula-test").
		WithEnvVariable("PUSULA_DB_HOST", "postgres").
		WithEnvVariable("PUSULA_DB_PORT", "5432").
		WithEnvVariable("PUSULA_DJANGO_SECRET_KEY", "dagger-test-only").
		WithEnvVariable("PUSULA_ALLOWED_HOSTS", "testserver,localhost,127.0.0.1").
		WithEnvVariable("PUSULA_DEBUG", "0").
		WithExec([]string{"pip", "install", "--disable-pip-version-check", "-r", "incubator/pusula/backend/requirements.txt"}).
		WithExec([]string{"python", "scripts/pusula_app_verify.py"})

	return container.Stdout(ctx)
}

func (m *PusulaPipeline) Web(ctx context.Context, source *dagger.Directory) (string, error) {
	container := dag.Container().
		From("node:24-alpine").
		WithMountedDirectory("/src", source).
		WithWorkdir("/src/incubator/pusula/web").
		WithEnvVariable("VITE_LOGTO_ENDPOINT", "https://logto.invalid").
		WithEnvVariable("VITE_LOGTO_APP_ID", "pusula-dagger").
		WithEnvVariable("VITE_PUSULA_API_RESOURCE", "https://api.pusula.invalid").
		WithExec([]string{"npm", "install", "--no-audit", "--no-fund"}).
		WithExec([]string{"npm", "run", "check"}).
		WithExec([]string{"npm", "run", "build"})

	return container.Stdout(ctx)
}

func (m *PusulaPipeline) Check(ctx context.Context, source *dagger.Directory) (string, error) {
	backend, err := m.Backend(ctx, source)
	if err != nil {
		return "", fmt.Errorf("backend verification failed: %w", err)
	}
	web, err := m.Web(ctx, source)
	if err != nil {
		return "", fmt.Errorf("web verification failed: %w", err)
	}
	return "backend:\n" + backend + "\nweb:\n" + web, nil
}
