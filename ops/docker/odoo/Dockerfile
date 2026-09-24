# Development and CI image: the stock Odoo 18 image plus what the browser
# tours (HttpCase.start_tour) need. Production keeps the plain, digest-pinned
# odoo:18.0 image (docker-compose.prod.yml): Chrome has no business there.
#
# Build context is the repository root (see Dockerfile.dockerignore):
#   docker build -f ops/docker/odoo/Dockerfile -t rubicon-odoo:dev .
FROM odoo:18.0

USER root

# Google Chrome for the headless tours. The base image is Ubuntu 24.04, whose
# chromium package is a snap stub that cannot run in a container, so the
# browser comes from Google's .deb (apt resolves its library dependencies).
RUN curl -fsSL -o /tmp/chrome.deb \
        https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends /tmp/chrome.deb \
    && rm -rf /tmp/chrome.deb /var/lib/apt/lists/*

# Python dependencies of the addons and their tests (websocket-client drives
# Chrome over the DevTools protocol). The system interpreter is the one Odoo
# runs on, hence --break-system-packages.
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

USER odoo
