FROM alpine:3.8
RUN apk --update add --no-cache nodejs

COPY ./entrypoint.sh ./src /opt/app/
RUN chmod +x /opt/app/entrypoint.sh
WORKDIR /opt/app
EXPOSE 80
ENTRYPOINT [ "./entrypoint.sh" ]
