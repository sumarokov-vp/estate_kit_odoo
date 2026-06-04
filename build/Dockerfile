FROM odoo:19

USER root

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
