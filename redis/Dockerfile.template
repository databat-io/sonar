FROM balenalib/raspberrypi3
EXPOSE 6379
RUN install_packages wget redis
COPY redis.conf /etc

CMD /usr/bin/redis-server /etc/redis.conf
