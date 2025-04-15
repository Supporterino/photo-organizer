# builder layer
FROM python:3.13-slim AS builder

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install build
RUN python -m build

# actual image
FROM python:3.13-slim

LABEL org.opencontainers.image.source=https://github.com/f18m/photo-organizer

# install the wheel
WORKDIR /app
COPY --from=builder /app/dist/*.whl .
RUN pip3 install --no-cache-dir *.whl

ENV PYTHONUNBUFFERED=1
ENTRYPOINT [ "photo-organizer" ]
