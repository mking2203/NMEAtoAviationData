# NMEAtoAviationData
NMEA protocol to aviation data

Description:
Simple converter program for the NMEA protocol to aviation data
Project by Johannes Bottema / Mark König
July 2021, Version 1.01

Hardware:
using Garmin Aera 660 (GPS) & DAC GDC31 (plane autopilot)

Installation:
on the rasp add a folder home/pi/.config/lxsession/LXDE-pi/
then work on the autostart

sudo nano ~/.config/lxsession/LXDE-pi/autostart
add this to the file
@lxterminal -e python3 /home/pi/serialRead.py
