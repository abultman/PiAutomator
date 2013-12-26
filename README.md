http://pi-automator.net/

PiAutomator
===========

Simple Python lib that allows you to read values from sensors etc. on the Pi and then trigger receivers into certain states.

Currently using this with a DHT22 sensor wired and a wired switch (KlikAanKlikUit) 
to switch the fan when it gets too humid in the bathroom

The setup is created in such a way that it should be easy enough to add more and different types of sensors and the
types of receivers should also be able to get a bit more variation, although I'll probably stick with kaku for now.

reads:

- LLAP sensors
- pilight events
- DHT22
- Onkyo amps

sends:

- pilight events (turn on lights etc)
- old protocol klik aan klik uit
- Prowl (ios notifs)
- Any cmd line

Open to suggestions :)

Required libs
-------------
A couple of python modules were used in the writing of this software. You should install then too:

* PyYAML
* pyparsing
* schedule -> Actually is included for now, but only until I get a pull request merged
* graphitesend -> If you want to enable graphite data sending
* wiringpi2 -> If you're using the direct KAKU controller
* pyserial -> If you want to use the LLAP receivers

to get them all:

```
sudo pip install PyYAML pyparsing schedule graphitesend  pyserial wiringpi2
```

Note that wiringpi only works on raspberry pi and is only needed for pin access. So if you have no pins, don't
install wiringpi2:

```
sudo pip install PyYAML pyparsing schedule graphitesend  pyserial
```

Rules
-----
Rules are used to make stuff happen in PiAutomator. There are two kinds of rules currently supported

1. Schedule rules
2. Conditional rules

### Schedule rules
Schedule rules make something happen on set times during the day/week/hour

basic format is:
```
every <schedule> <action>
```

#### singular rules:

```
every <unit> <at optional_time> <verb> <receiver> <state>

unit: day hour second week sunday weekday weekendday
optional_time: of the format 'at 10:30' or 'at :30' , only works for day/hour/weekday/weekenday
verb: any word that makes your text look nice :) -> In the future some receivers might use this for more specificity
receiver: The name of any receiver to handle the scheduled event
state: The state to send to the receiver

Note that weekday matches on monday, tuesday, wednesday, thursday, friday so a rule with this unit will fire on all
those days
Note that weekendday matches on satureday, sunday so a rule with this unit will fire on all
those days

Example:
every day turn lights on
every weekday at 10:30 turn lights on
```

#### plural rules
like singular but with:

```
every <interval> <unit> <at optional_time> <verb> <receiver> <state>

interval: the interval to set
unit: days hours seconds weeks

Example
every 2 days turn lights on
every 2 days at 10:30 turn lights on
```

#### day rules
allows firing on specific days of the week

```
every <day(s)> <at optional_time> <verb> <receiver> <state>

day(s): monday tuesday wednesday thursday friday saturday sunday
        -> Allows for multiple days by connecting them with the 'and' keyword

example
every monday turn lights on
every monday at 10:30 turn lights on
every monday and tuesday and friday at 10:30 turn lights on
```

#### actions
In the examples above only a single action was performed every time a schedule matched. You can
execute multiple actions on a single schedule simply by defining more then one separated by 'and'

```
every day at 8:00 turn lights on and send notification "wake up!"
```

### Conditional rules
Conditional rules fire based on certain conditions being met. All conditional rules operate on the AutomationContext
which stores information about input states, rule states and receiver states. A rule condition can operate on all these.
when matching, a conditional rule will fire the associated actions (same format as with scheduled rules) once. As long
as the rule matched and keeps matching, it will only fire once (to prevent event storms)

Format:

```
when <value_path> is <operator> <value> then <action>

value_path: a path to a value in the context
operator: an operator on the value. Currently supported less than, greater than, equal to
value: the value to compare. Casting may occur depending on the operator used

example
when bathroom.humidity is greater than 60 then turn homefan on
```

#### value paths
Every input, rule and receiver in PiAutomator reports to the AutomationContext with values. If values change, a
reevaluation of all conditional rules is triggered.

value paths are nested name spaces with '.' separators. The context supports the following top level namespaces
to make sure there are no collisions:

- input
- rule
- receiver

when writing a rule with a value path, the context will always first try to find the value using the exact supplied path
when that cannot be found, it will try to find it in one of the predefined name spaces. You can look in to the dumped
state from the program if you're unsure about the path.

Example:
```
when bathroom.humidity is less than 50 then turn homefan off
```

In this case _bathroom.humidity_ is the path. When the rule matches, it will first look in the context for the exact
value, afterwards it will also look for _input.bathroom.humidity_ and _rule.bathroom.humidity_ etc. until it finds
something or it's options are exhausted.

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

take a look at the included config-example.yaml on what is possible.

To get started:

1. Install the required python libs.
2. Create a config.yaml in conf/ with your settings
3. run bin/bin/start-automator.py


pilight
-------
PiAutomator supports adding pilight as both inputs and receivers. pilight can read the DHT22 all by itself, should you not want to, you can config it directly.

example of pilight output:

```
  outsidelights:
    translate-up-down: true # If using old style KAKY will translate rule action on/off to receiver up/down
    type: PiLight
    location: frontgarden  # Location from pilight config
    device: lights  # device from pilight config
```

example of specific pilight input:
```
   bathroom:
     type: PiLight
     location: bathroom  # location from pilight config
     device: h_t_sensor  # device from pilight config
     scale: 0.1  # Optional scale you can add to receivers returning numbers (works for all receivers)
     
   # corresponding rule
   - when bathroom.humidity is greater than 70 turn homefan on
```

you van also add all pilight input to the mix:
```
   all-pilight:
     type: PiLight
     location: all
     device: all
   
   # corresponding rule
   # - when pilight.<location>.<device>.<value> is equal to on
   - when pilight.livingroom.christmastree.state is equal to 'up' then turn music on
```

Doing this will make all pilight values available for your rules to play with. Specific inputs take precedence over the all, so you can still have individual ones where you think it needed.

If you're unsure about what keys to use, the automator dumps it's state when you stop it. So have a look at the input section there.

http://www.pilight.org/

LLAP
----

PiAutomator support reading (and only readying currently) sensor data from LLAP compatible serial input devices. This is mainly usefull for remote sensors setting up a wireless network.

- Basically, setup your Pi with a wireless receiver of somekind, I use the slice of radio (http://shop.ciseco.co.uk/slice-of-radio-wireless-rf-transciever-for-the-raspberry-pi/)
- Use other devices to transmit on the correct frequency (for instance using something like http://shop.ciseco.co.uk/xrf-wireless-rf-radio-uart-rs232-serial-data-module-xbee-shape-arduino-pic-etc/)

And set the remote up to send LLAP compatible data.
- http://openmicros.org/index.php/articles/85-llap-lightweight-local-automation-protocol/101-llap-starter
- http://openmicros.org/index.php/articles/85-llap-lightweight-local-automation-protocol/112-llap
- Example: http://www.seanlandsman.com/2013/02/the-raspberry-pi-and-wireless-rf-xrf.html

then add a LLAP receiver per device you have installed:
```
  outside1:
    type: LLAP
    device-id: AA
```

the receiver will automatically recognize and publish values for your rules to use. Currently supported are the following LLAP standard metrics:
```
    LLAP Command        Reported as         Data type/value
    BATTLOW             lowbattery          True             -> Turns on low battery state
    BATT                batterylevel        float
    STARTED             lowbattery          False            -> Low battery is turned off when STARTED is received. If there is still lowbattery, you will get the BATTLOW again
    LVAL                lightlevel          float
    TEMP                temperature         float
    TMPA                temperature         float
    ANA                 analog              int
    BUTTON              button              str              -> Unsure about this one, I don't have it and the docs are a bit unclear to me.
```

So for instance based on above config an appropriate rule would be:
```
  - when outside1.lightlevel is less than 40 then tun outsidelights on
```


DHT22 - Direct
--------------
*NOTE:* You don't have to do anything here if you're not using the direct access DHT sensor receiver

install bcm2835 library: http://www.airspayce.com/mikem/bcm2835/

To read the DHT22 sensor directly, this wonderfull piece of software was used:

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
