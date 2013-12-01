PiAutomator
===========

Simple Python lib that allows you to read values from sensors etc. on the Pi and then trigger receivers into certain states.

Currently using this with a DHT22 sensor wired and a wired switch (KlikAanKlikUit) 
to switch the fan when it gets too humid in the bathroom

The setup is created in such a way that it should be easy enough to add more and different types of sensors and the
types of receivers should also be able to get a bit more variation, although I'll probably stick with kaku for now.

Required libs
-------------
A couple of python modules were used in the writing of this software. You should install then too:

* schedule
* PyYAML
* graphitesend
* pyparsing

Graphite
--------
Automatically sends collected sensor data to Graphite so you can keep an eye on your data.
I used https://github.com/ghoulmann/rpi-graphite/blob/master/rpi-graphite.sh to quickly get graphite on the pi.

DHT22
-----
install bcm2835 library: http://www.airspayce.com/mikem/bcm2835/

To read the DHT22 sensor, this wonderfull piece of software was used:
https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code/tree/master/Adafruit_DHT_Driver_Python
the python lib is included in this release

Please note the following notice about that library:
Copyright (c) 2012-2013 Limor Fried, Kevin Townsend and Mikey Sklar for Adafruit Industries. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met: * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer. * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution. * Neither the name of the nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

