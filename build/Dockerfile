FROM odoo:19

USER root

# S3 dependencies for OCA fs_storage modules
# s3fs pulls in aiobotocore which pins botocore version
RUN pip3 install --no-cache-dir --break-system-packages --ignore-installed \
    "fsspec>=2025.3.0" \
    "s3fs>=2024.2.0" \
    python-slugify \
    packaging \
    beautifulsoup4 \
    "grpcio>=1.70.0" \
    "protobuf>=5.29.0"

# Copy custom addons
COPY ./addons /mnt/extra-addons

# Set permissions
RUN chown -R odoo:odoo /mnt/extra-addons

USER odoo
