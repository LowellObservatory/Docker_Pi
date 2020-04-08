FROM ligpibase

USER lig
RUN mkdir /home/lig/domeTattler && \
    mkdir /home/lig/domeTattler/config && \
    mkdir /home/lig/domeTattler/snaps && \
    mkdir /home/lig/domeTattler/logs

WORKDIR /home/lig/domeTattler
COPY --chown=lig:lig domeTattler.py .

CMD ["python", "domeTattler.py"]
