FROM telegraf:1.26-alpine
COPY telegraf.conf /etc/telegraf/telegraf.conf.template
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["telegraf"]
