FROM maven:3-openjdk-18-slim

RUN apt-get update && \
    apt-get install -y bzip2 python3-pip curl && \
    pip3 install --upgrade flask werkzeug gunicorn

ARG NODE_VERSION=20.10.0
ARG TARGETPLATFORM
RUN if [ "$TARGETPLATFORM" = "linux/arm64" ]; then ARCH="arm64"; else ARCH="x64"; fi \
 && curl https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-$ARCH.tar.gz | tar -xz -C /usr/local --strip-components 1

WORKDIR /usr/src/parser
ADD . /usr/src/parser
RUN mvn -q -f /usr/src/parser/pom.xml clean install -U

# Add wrapper API and entrypoint script
COPY wrapper_api.py /usr/src/wrapper_api.py
COPY run_wrapper.sh /usr/src/run_wrapper.sh
RUN chmod +x /usr/src/run_wrapper.sh

EXPOSE 5600
EXPOSE 5700

CMD ["/usr/src/run_wrapper.sh"]
