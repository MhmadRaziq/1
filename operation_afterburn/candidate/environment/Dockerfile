FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
WORKDIR /workspace
# Offline image: evidence packet is copied at build time; no network needed at runtime.
COPY data /workspace/data
RUN mkdir -p /workspace/output \
    && chmod -R a+rX /workspace/data \
    && chmod a+rwx /workspace/output
CMD ["bash"]
