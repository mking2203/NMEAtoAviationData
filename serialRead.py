# Simple converter program for the NMEA protocol to aviation data
# Project by Johannes Bottema / Mark König
# July 2021, Version 1.01
#
# using Garmin Aera 660 (GPS) & DAC GDC31 (plane autopilot)
#
# on the rasp add a folder home/pi/.config/lxsession/LXDE-pi/
# then work on the autostart
# sudo nano ~/.config/lxsession/LXDE-pi/autostart
# @lxterminal -e python3 /home/pi/serialRead.py

# Import and initialize the library
import pynmea2
import serial

# normal imports
import time
from datetime import datetime
import sys

# funtion to build the aviation data
def AviationData(track=0.0, groundSpeed=0.0, crossDir = '', crossError=0.0, desiredTrack=0.0, altitude=0.0):

    # für Gerät DAC GDC31
    # <STX><id><dddd><it><id><dddd><it>…<id><dddd><it><ETX>

    # C             ddd         3           track, ddd=degrees
    # D             sss         3           ground speed, sss=knots
    # G             Rnnnn       5           crosstrack error, R=R or L or blank (when zero), nnnn=nautical miles * 100
    # I             dddd        4           desired track, dddd=degrees * 10

    # not needed for the DAC
    # z             aaaaa       5           altitude, aaaaa=feet

    it = chr(0x0D) # CR

    # start
    send = ''
    send = send + chr(0x02) # STX

    if crossDir == 'R':
        crossDir = 'L'
    elif crossDir == 'L':
        crossDir = 'R'

    print ('act. ' + crossDir)

    # data
    send = send + 'C' + '%03.0F' % track + it
    send = send + 'D' + '%03.0F' % groundSpeed + it
    send = send + 'G' + crossDir + '%04.0F' % (crossError * 100) + it
    send = send + 'I' + '%04.0F' % (desiredTrack * 10) + it
    send = send + 'z' + '%05.0F' % altitude + it

    #end
    send = send + chr(0x03) # ETX

    return send

# ------------------------- MAIN -------------------------

# hold the vars during loop's
mTrack = 0.0
mGround = 0.0
mCross = 0.0
mCrossDir = ''
mDesired = 0.0
mAltitude = 0.0

# output more dignosis
debug = True
simulation = False
simuCNT = 0

print('### Aviation converter ###')

# here we initiate the serial port
if not simulation:

    startOK = False
    while not startOK:
        try:
            #ser = serial.Serial('COM7', 9600, timeout=0.2)
            ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.2)
            #ser = serial.Serial('/dev/ttyS0', 9600, timeout=0.2)
            startOK = True
        except:
            pass

        print('wait for serial port....')
        time.sleep(5)


print('wait for GPS data')

# loop forever
while True:
    try:
        if not simulation:
            # receive from port
            recv = ser.readline().decode()
        else:
            # simulation part
            simuCNT = simuCNT + 1
            if simuCNT > 2: simuCNT = 0

            time.sleep(0.3)

            if simuCNT == 0:
                recv = "$GPRMB,A,0.66,L,003,004,4917.24,N,12309.57,W,001.3,052.5,000.5,V*20"
            elif simuCNT == 1:
                recv = "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"
            elif simuCNT == 2:
                recv = "$PGRMH,A,-4,,,,0,260.4,285.5*22"

        if recv.startswith('$'):
            # we received a NMEA string, let's parse the result
            record = pynmea2.parse(recv)

            if recv.startswith('$GPRMB'):
                if(debug):
                    print('Cross error: ', record.cross_track_error)
                    print('Cross direction: ', record.cte_correction_dir)
                if record.cross_track_error != '':
                    mCross = float(record.cross_track_error)
                if record.cte_correction_dir !='':
                    mCrossDir = record.cte_correction_dir

            elif recv.startswith('$PGRMH'):
                # data is not decoded, so we use just the data field
                if(debug):
                    print('Desired track: ', record.data[7])
                if record.data[7] is not None:
                    if(record.data[7] != ''):
                        mDesired = float(record.data[7])

            elif recv.startswith('$PGRMZ'):
                # data is not decoded, so we use just the data field
                if(debug):
                    print('Altitude: ', record.data[1])
                if record.data[1] is not None:
                    if(record.data[1] != ''):
                        mAltitude = float(record.data[1])

            elif recv.startswith('$GPRMC') or recv.startswith('$GNRMC'):
                # default NMEA message, whenever received we may send one time
                print('--------------------------------')
                if not simulation:
                    print('Time: ' + str(record.timestamp))
                else:
                    print('Time: ' + str(datetime.now().strftime("%H:%M:%S")))
                if(debug):
                    print('Fix Status: ', record.status)
                    print('Latitude: ', record.latitude)
                    print('Longitude direction: ', record.lon_dir)
                    print('Longitude: ', record.longitude)
                    print('Speed: ', record.spd_over_grnd)
                    print('Track: ', record.true_course)
                    print('Altitude: ', mAltitude)

                mGround = 0.0
                if record.spd_over_grnd is not None:
                    if(record.spd_over_grnd != ''):
                        mGround = float(record.spd_over_grnd)

                mTrack = 0.0
                if record.true_course is not None:
                    if(record.true_course != ''):
                        mTrack = float(record.true_course)

                if not simulation:

                    # check status of the NMEA
                    if(record.status == 'V') or (record.status == 'A'):

                        strSend = AviationData(track = mTrack, groundSpeed = mGround, crossDir = mCrossDir, crossError = mCross, desiredTrack = mDesired, altitude = mAltitude)
                        if debug:
                            print ('-------------------')
                            print (str(len(strSend)) + ' bytes send to DAC')
                            print ('-------------------')

                        # encode to bytes and send
                        by = strSend.encode('raw_unicode_escape')
                        ser.write(by)

                    else:
                        print ('wait for GPS data....')
                else:
                     print ('simulation is running....')


    except pynmea2.nmea.ParseError:
        print('NMEA wrong！')
    except KeyboardInterrupt:
        print ('Interrupted')
        exit()
    except:
        print("Unexpected error:", sys.exc_info()[0])
        pass
