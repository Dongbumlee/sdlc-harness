# The system E2E runner image: the scheduled/pre-release pipeline
# runs the smoke suite from this container against deployed
# services. Standard-library-only by design, so the image stays a
# slim Python with nothing to install.
FROM python:3.12-slim
WORKDIR /system
COPY system_e2e.py ./
ENTRYPOINT ["python3", "system_e2e.py"]
CMD ["--help"]
