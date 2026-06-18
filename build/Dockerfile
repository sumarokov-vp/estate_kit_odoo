FROM odoo:19

USER root

ARG TYPST_VERSION=0.14.2

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        xz-utils \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL "https://github.com/typst/typst/releases/download/v${TYPST_VERSION}/typst-x86_64-unknown-linux-musl.tar.xz" \
        -o /tmp/typst.tar.xz \
    && tar -xJf /tmp/typst.tar.xz -C /tmp \
    && mv "/tmp/typst-x86_64-unknown-linux-musl/typst" /usr/local/bin/typst \
    && chmod +x /usr/local/bin/typst \
    && rm -rf /tmp/typst.tar.xz "/tmp/typst-x86_64-unknown-linux-musl" \
    && typst --version

RUN pip3 install --no-cache-dir --break-system-packages --ignore-installed \
    python-slugify \
    packaging \
    beautifulsoup4 \
    "grpcio>=1.70.0" \
    "protobuf>=6.33.5"

# Copy custom addons
COPY ./addons /mnt/extra-addons

# Set permissions
RUN chown -R odoo:odoo /mnt/extra-addons

USER odoo
