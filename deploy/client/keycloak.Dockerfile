# Keycloak image for the CLIENT stack (production mode: `start --optimized`).
# Build context is src/keycloak (see docker-compose.build.yml); the dev and VPS image is
# src/keycloak/Dockerfile and is not touched.
#
# Build-time options (baked in here; changing one needs a new image):
#   --db=postgres            the client uses the postgres service, not the embedded dev database
#   --health-enabled=true    /health endpoints (management interface)
#   --http-relative-path=/auth   every URL lives under /auth (nginx, realm, frontend settings)
# No extra --features: the realm uses only default-enabled features.
# The audit event listener (custom provider) and the wims-bfp login/email theme are part of
# the build; the theme is copied in because the realm sets loginTheme/emailTheme to wims-bfp.
FROM maven:3.9.9-eclipse-temurin-17 AS provider-builder

WORKDIR /workspace
COPY wims-audit-event-listener/pom.xml wims-audit-event-listener/pom.xml
COPY wims-audit-event-listener/src wims-audit-event-listener/src
RUN mvn -f wims-audit-event-listener/pom.xml -B package

FROM quay.io/keycloak/keycloak:26.6.4

COPY --from=provider-builder /workspace/wims-audit-event-listener/target/wims-audit-event-listener.jar /opt/keycloak/providers/wims-audit-event-listener.jar
COPY themes/wims-bfp /opt/keycloak/themes/wims-bfp
RUN /opt/keycloak/bin/kc.sh build --db=postgres --health-enabled=true --http-relative-path=/auth
