FROM node:alpine
COPY ./src /opt/app
WORKDIR /opt/app
EXPOSE 80
ENTRYPOINT [ "node", "index.js" ]
