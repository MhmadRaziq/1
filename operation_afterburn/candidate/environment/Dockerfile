FROM python:3.12-slim
WORKDIR /workspace
# Offline image: evidence packet is copied at build time; no network needed at runtime.
COPY data /workspace/data
RUN mkdir -p /workspace/output \
    && chmod -R a+rX /workspace/data \
    && chmod a+rwx /workspace/output
CMD ["bash"]
