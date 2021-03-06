#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# yokogawa7651.py: Driver for the Yokogawa 7651 power supply.
##
# © 2014 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
##
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
##

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

import quantities as pq
from flufl.enum import Enum
from flufl.enum._enum import EnumValue

from instruments.abstract_instruments import (
    PowerSupply,
    PowerSupplyChannel,
)
from instruments.abstract_instruments import Instrument
from instruments.util_fns import assume_units, ProxyList

## CLASSES #####################################################################

class _Yokogawa7651Channel(PowerSupplyChannel):
    '''
    Class representing the only channel on the Yokogawa 7651.
    
    This class inherits from `PowerSupplyChannel`.
    
    .. warning:: This class should NOT be manually created by the user. It is 
        designed to be initialized by the `Yokogawa7651` class.
    '''
    
    def __init__(self, yoko, name):
        self._yoko = yoko
        self._name = name
    
    ## PROPERTIES ##
    
    @property
    def mode(self):
        """
        Sets the output mode for the power supply channel.
        This is either constant voltage or constant current.
        
        Querying the mode is not supported by this instrument.
        
        :type: `Yokogawa7651.Mode`
        """
        raise NotImplementedError('This instrument does not support querying '
                                  'the operation mode.')
    @mode.setter
    def mode(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                           Yokogawa7651.Mode):
            raise TypeError("Mode setting must be a `Yokogawa7651.Mode` "
                            "value, got {} instead.".format(type(newval)))
        self._yoko.sendcmd('F{};'.format(newval.value))
        self._yoko.trigger()
        
    @property
    def voltage(self):
        """
        Sets the voltage of the specified channel. This device has a voltage
        range of 0V to +30V.
        
        Querying the voltage is not supported by this instrument.
        
        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Volts.
        :type: `~quantities.Quantity` with units Volt
        """
        raise NotImplementedError('This instrument does not support querying '
                                  'the output voltage setting.')
    @voltage.setter
    def voltage(self, newval):
        newval = float(assume_units(newval, pq.volt).rescale(pq.volt).magnitude)
        self.mode = self._yoko.Mode.voltage
        self._yoko.sendcmd('SA{};'.format(newval))
        self._yoko.trigger()
        
    @property
    def current(self):
        """
        Sets the current of the specified channel. This device has an max
        setting of 100mA.
        
        Querying the current is not supported by this instrument.
        
        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Amps.
        :type: `~quantities.Quantity` with units Amp
        """
        raise NotImplementedError('This instrument does not support querying '
                                  'the output current setting.')
    @current.setter
    def current(self, newval):
        newval = float(assume_units(newval, pq.amp).rescale(pq.amp).magnitude)
        self.mode = self._yoko.Mode.current
        self._yoko.sendcmd('SA{};'.format(newval))
        self._yoko.trigger()
        
    @property
    def output(self):
        """
        Sets the output status of the specified channel. This either enables
        or disables the output.
        
        Querying the output status is not supported by this instrument.
        
        :type: `bool`
        """
        raise NotImplementedError('This instrument does not support querying '
                                  'the output status.')
    @output.setter
    def output(self, newval):
        if newval is True:
            self._yoko.sendcmd('O1;')
            self._yoko.trigger()
        else:
            self._yoko.sendcmd('O0;')
            self._yoko.trigger()

class Yokogawa7651(PowerSupply, Instrument):

    def __init__(self, filelike):
        super(Yokogawa7651, self).__init__(filelike)
        self._outputting = 0 # TODO: Do we want to track output status anymore?
        
    ## ENUMS ##
    
    def Mode(Enum):
        voltage = 1
        current = 5
        
    ## PROPERTIES ##
    
    @property
    def channel(self):
        """
        Gets the specific power supply channel object. Since the Yokogawa7651
        is only equiped with a single channel, a list with a single element
        will be returned.
        
        This (single) channel is accessed as a list in the following manner::
        
        >>> yoko = ik.other.Yokogawa7651.open_gpibusb('/dev/ttyUSB0', 10)
        >>> yoko.channel[0].voltage = 1 # Sets output voltage to 1V
        
        :rtype: `_Yokogawa7651Channel`
        """
        return ProxyList(self, _Yokogawa7651Channel, [0])
        
    @property
    def voltage(self):
        """
        Sets the voltage. This device has a voltage range of 0V to +30V.
        
        Querying the voltage is not supported by this instrument.
        
        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Volts.
        :type: `~quantities.Quantity` with units Volt
        """
        raise NotImplementedError('This instrument does not support querying '
                                  'the output voltage setting.')
    @voltage.setter
    def voltage(self, newval):
        self.channel[0].voltage = newval
        
    @property
    def current(self):
        """
        Sets the current. This device has an max setting of 100mA.
        
        Querying the current is not supported by this instrument.
        
        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Amps.
        :type: `~quantities.Quantity` with units Amp
        """
        raise NotImplementedError('This instrument does not support querying '
                                  'the output current setting.')
    @current.setter
    def current(self, newval):
        self.channel[0].current = newval
    
    ## METHODS ##
        
    def trigger(self):
        '''
        Triggering function for the Yokogawa 7651.
        
        After changing any parameters of the instrument (for example, output 
        voltage), the device needs to be triggered before it will update.
        '''
        self.sendcmd('E;')
        
