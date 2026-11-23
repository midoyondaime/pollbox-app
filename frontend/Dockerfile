# frontend/Dockerfile - nginx image carrying the pollbox page.
# A comment must be on its own line in a Dockerfile.

# a pinned nginx version, small alpine variant
FROM nginx:1.27-alpine
# our configuration replaces the default server block
COPY nginx.conf /etc/nginx/conf.d/default.conf
# the static page, in the folder nginx serves
COPY index.html /usr/share/nginx/html/index.html
