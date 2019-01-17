FROM node:alpine
COPY ./src /opt/app
WORKDIR /opt/app
EXPOSE 80
CMD [ "node", "index.js" ]
