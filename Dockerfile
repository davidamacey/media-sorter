FROM python:3.13-alpine

LABEL org.opencontainers.image.title="EXIF Sorter"
LABEL org.opencontainers.image.description="Organize photos, videos, and audio files by EXIF/ID3 creation date"
LABEL org.opencontainers.image.authors="David A. Macey <davidamacey@gmail.com>"
LABEL org.opencontainers.image.source="https://github.com/davidamacey/exif-sorter"
LABEL org.opencontainers.image.documentation="https://github.com/davidamacey/exif-sorter#readme"
LABEL org.opencontainers.image.licenses="MIT"

# Install exiftool (perl-image-exiftool is in Alpine community repo)
RUN apk add --no-cache perl-image-exiftool

# Install exif-sorter from PyPI
RUN pip install --no-cache-dir exif-sorter

# Set working directory for mounted volumes
WORKDIR /data

# Default entrypoint is the exif-sorter CLI
ENTRYPOINT ["exif-sorter"]

# Default command shows help
CMD ["--help"]
