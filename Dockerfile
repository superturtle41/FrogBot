FROM python:3.7-stretch

ARG DBOT_ARGS
ARG ENVIRONMENT=production
ARG COMMIT=""

RUN useradd --create-home dndbot
USER dndbot
WORKDIR /home/dndbot

ENV GIT_COMMIT_SHA=${COMMIT}

COPY --chown=dndbot:dndbot requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt

COPY --chown=dndbot:dndbot dndbot .
COPY --chown=dndbot:dndbot . .

#COPY --chown=nodom:nodom docker/credentials-${ENVIRONMENT}.py credentials.py

# Download AWS pubkey to connect to documentDB
#RUN if [ "$ENVIRONMENT" = "production" ]; then wget https://s3.amazonaws.com/rds-downloads/rds-combined-ca-bundle.pem; fi

WORKDIR /home/dndbot
ENTRYPOINT python dndbot/dbot.py $DBOT_ARGS