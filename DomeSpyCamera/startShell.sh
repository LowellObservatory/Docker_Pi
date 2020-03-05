#!/bin/bash

# docker run -it -v /opt/vc/lib:/opt/vc/lib --rm -u root --device /dev/vchiq --device /dev/vcsm snapper /bin/bash
docker run -it -v /opt/vc/lib:/opt/vc/lib --rm -u lig --device /dev/vchiq --device /dev/vcsm snapper /bin/bash
