# #!/usr/bin/bash

pyuic5 directorStartupDialog.ui -o directorStartupDialog.py
pyuic5 FITSKeywordPanel.ui -o FITSKeywordPanel.py
pyuic5 SOFIACruiseDirectorPanel.ui -o SOFIACruiseDirectorPanel.py
pyuic5 directorLogDialog.ui -o directorLogDialog.py
pyuic5 flightMapDialog.ui -o flightMapDialog.py
pyuic5 flightMapWidget.ui -o flightMapWidget.py

