FROM python:3.10-slim as base

RUN mkdir -p /img_root/app

COPY . /img_root/app/

RUN mv /img_root/app/shipping/* /img_root/ && \
    chmod +x /img_root/*.sh && \
    rm -rf /img_root/app/shipping

FROM python:3.10-slim

RUN mkdir /app
WORKDIR /app
COPY --from=base /img_root/ /

RUN python -m pip install pip --upgrade && \
    python -m pip install --no-cache-dir -r /app/requirements.txt

ENV PYTHONPATH=/app

EXPOSE 8000

# no root user
RUN adduser --disabled-password --gecos "" appuser
USER appuser

CMD ["/start.sh"]
