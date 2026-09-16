FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        build-essential \
        cmake \
        ninja-build \
        pkg-config \
        libssl-dev \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin pqcshield

COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir --upgrade pip \
    && python3 -m pip install --no-cache-dir -r requirements.txt

COPY --chown=pqcshield:pqcshield . .

RUN mkdir -p /app/data /app/reports \
    && chown -R pqcshield:pqcshield /app

USER pqcshield

CMD ["python3", "-m", "collector.benchmark"]
