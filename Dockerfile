# using this disposable builder in order to reduce Docker image size upto 21MB
FROM ruby:2.5.3-alpine3.7 as builder

RUN mkdir -p /app
WORKDIR /app

ADD ./app-sinatra/ /app/
RUN bundle install


FROM ruby:2.5.3-alpine3.7
COPY --from=builder /usr/local/bundle/ /usr/local/bundle/
COPY --from=builder /app/ /app/

EXPOSE 9292
CMD ["bundle","exec","rackup","--host","0.0.0.0"]
