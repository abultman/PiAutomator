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
* wiringpi2

Graphite
--------
Automatically sends collected sensor data to Graphite so you can keep an eye on your data.
I used https://github.com/ghoulmann/rpi-graphite/blob/master/rpi-graphite.sh to quickly get graphite on the pi.

General Concepts
----------------

Configures a set of rules that

1. Take input from configured  receivers (like the DHT22)
2. Take a fixed schedule

and then execute (a series of) actions when input meets criteria.

An example of a rule could be:

- when kitchen.temperature is greater than 25 then turn airconditioning on
- every day at 20:00 turn outsidelights on


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

Stubs
-----
The project contains a couple of stubs to allow for development/testing on other machines than the pi

Specifically:

* /stubs/wiringpi2.py
    basically noops all used wiringpi2 methods. Needed in order to run the python version of the KlikAanKlikUitReceivef
* /stubs/dhtreader.py
    For the DHT22 input. Returns random numbers between 10 and 25 for temperature and random numbers between 45 and 95 for humidity (full ints)

Legal
-----
Distrubuted under Apache 2.0 license (see LICENSE.txt)