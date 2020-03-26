FROM ligpibase

USER root

RUN pip3 install w1thermsensor

USER lig
RUN mkdir /home/lig/onewireTemps && \
    mkdir /home/lig/onewireTemps/config && \
    mkdir /home/lig/onewireTemps/logs

WORKDIR /home/lig/onewireTemps
COPY --chown=lig:lig onewireTemps.py .  
COPY --chown=lig:lig setPrecision.py .  

CMD ["python", "onewireTemps.py"]
