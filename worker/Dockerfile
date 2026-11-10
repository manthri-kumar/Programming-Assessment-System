# BASE_IMAGE must be supplied as a registry reference pinned with @sha256:...
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

ARG DEBIAN_SNAPSHOT
ARG DEBIAN_SECURITY_SNAPSHOT
RUN test -n "${DEBIAN_SNAPSHOT}" && test -n "${DEBIAN_SECURITY_SNAPSHOT}" \
    && rm -f /etc/apt/sources.list /etc/apt/sources.list.d/debian.sources \
    && printf 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/%s bookworm main\n' "${DEBIAN_SNAPSHOT}" > /etc/apt/sources.list \
    && printf 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian-security/%s bookworm-security main\n' "${DEBIAN_SECURITY_SNAPSHOT}" >> /etc/apt/sources.list \
    && apt-get update \
    && apt-get install --yes --no-install-recommends \
       "python3.11=3.11.2-6+deb12u9" \
       "clang-14=1:14.0.6-12" \
       "openjdk-17-jdk-headless=17.0.21+9-1~deb12u1" \
       ca-certificates \
    && test "$(dpkg-query -W -f='${Version}' python3.11)" = "3.11.2-6+deb12u9" \
    && test "$(dpkg-query -W -f='${Version}' clang-14)" = "1:14.0.6-12" \
    && test "$(dpkg-query -W -f='${Version}' openjdk-17-jdk-headless)" = "17.0.21+9-1~deb12u1" \
    && ln -sf /usr/bin/python3.11 /usr/local/bin/python3 \
    && ln -sf /usr/bin/clang-14 /usr/local/bin/clang \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --system --uid 65532 --no-create-home --shell /usr/sbin/nologin assessment
RUN mkdir -p /opt/assessment-worker/bin
COPY --chown=65532:65532 worker/entrypoint.py /opt/assessment-worker/bin/worker
RUN chmod 0555 /opt/assessment-worker/bin/worker \
    && printf '{"python_deb":"%s","clang_deb":"%s","java_deb":"%s"}\n' \
       "3.11.2-6+deb12u9" "1:14.0.6-12" "17.0.21+9-1~deb12u1" \
       > /opt/assessment-worker/toolchains.json \
    && chmod 0444 /opt/assessment-worker/toolchains.json
WORKDIR /work
USER 65532:65532

LABEL org.opencontainers.image.assessment.python="3.11.2-6+deb12u9" \
      org.opencontainers.image.assessment.clang="1:14.0.6-12" \
      org.opencontainers.image.assessment.java="17.0.21+9-1~deb12u1"

ENTRYPOINT ["/opt/assessment-worker/bin/worker"]
