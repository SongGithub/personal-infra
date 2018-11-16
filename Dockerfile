# using this disposable builder in order to reduce Docker image size upto 21MB
FROM ruby:2.5.3-alpine3.7 as builder

RUN mkdir -p /app
WORKDIR /app

ADD ./app-sinatra/ /app/
RUN bundle install


FROM ruby:2.5.3-alpine3.7
RUN mkdir -p /app
WORKDIR /app
COPY --from=builder /usr/local/bundle/ /usr/local/bundle/
COPY --from=builder /app/ /app/

RUN apk add curl
HEALTHCHECK --interval=5s --timeout=3s CMD curl --fail http://localhost:9292 || exit 1

EXPOSE 9292
CMD ["bundle","exec","rackup","--host","0.0.0.0"]
