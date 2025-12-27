FROM odoo:19

USER root

# Install additional Python dependencies if needed
# RUN pip3 install --no-cache-dir <package>

# Copy custom addons
COPY ./addons /mnt/extra-addons

# Set permissions
RUN chown -R odoo:odoo /mnt/extra-addons

USER odoo
