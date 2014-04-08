#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# tektds5xx.py: Driver for the Tektronix TDS 5xx series oscilloscope.
##
# © 2014 Chris Schimp (silverchris@gmail.com)
#
# Modified from tektds224.py
# © 2013 Steven Casagrande (scasagrande@galvant.ca).
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

import time
import numpy as np
from flufl.enum import Enum
from flufl.enum._enum import EnumValue

from time import sleep
from datetime import datetime
import operator
import struct

from instruments.abstract_instruments import (
    OscilloscopeChannel,
    OscilloscopeDataSource,
    Oscilloscope,
)
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import ProxyList

## HELPERS #####################################################################

def _string_to_bool(string):
    """
    Converts a string containing 1 or 0 to a bool()
    
    :type: `bool`
    """
    return bool(int(string))

## CLASSES #####################################################################

class _TekTDS5xxMeasurement(object):
    """
    Class representing a measurement channel on the Tektronix TDS5xx
    """
    
    def __init__(self, tek, idx):
        self._tek = tek
        self._id = idx+1    

    @property
    def direction(self):
        """
        Gets/Sets Measurement Direction
        
        :type: `TekTDS5xx.Direction`
        """
        resp = self._tek.query("MEASU:MEAS{}:DEL:DIRE?".format(self._id))
        return TekTDS5xx.Direction[resp]
    
    @direction.setter
    def direction(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                   TekTDS5xx.Direction):
            raise TypeError("Direction setting must be a `TekTDS5xx.Direction`"
                " value, got {} instead.".format(type(newval)))

        self._tek.sendcmd("MEASU:MEAS{}:DEL:DIRE {}".format(self._id,
                                                        newval.value))
    
    @property
    def edge(self):
        """
        Gets/Sets the Edge used on Measurement Source
        
        :type: `TekTDS5xx.Edge`
        """
        resp = self._tek.query("MEASU:MEAS{}:DEL:EDGE1?".format(self._id))
        return TekTDS5xx.Edge[resp]
    
    @edge.setter
    def edge(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                   TekTDS5xx.Edge):
            raise TypeError("Edge setting must be a `TekTDS5xx.Edge`"
                " value, got {} instead.".format(type(newval)))

        self._tek.sendcmd("MEASU:MEAS{}:DEL:EDGE1 {}".format(self._id,
                                                        newval.value))
        
    @property
    def edge2(self):
        """
        Gets/Sets the Edge used on Measurement Source2
        
        :type: `TekTDS5xx.Edge`
        """
        resp = self._tek.query("MEASU:MEAS{}:DEL:EDGE2?".format(self._id))
        return TekTDS5xx.Edge[resp]
    
    @edge2.setter
    def edge2(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                   TekTDS5xx.Edge):
            raise TypeError("Edge setting must be a `TekTDS5xx.Edge`"
                " value, got {} instead.".format(type(newval)))

        self._tek.sendcmd("MEASU:MEAS{}:DEL:EDGE2 {}".format(self._id,
                                                        newval.value))
    
    @property
    def source(self):
        """
        Gets/Sets the Measurement Source
        
        :type: `TekTDS5xx.Source`
        """
        resp = self._tek.query("MEASU:MEAS{}:SOURCE?".format(self._id))
        return TekTDS5xx.Source[resp]
    
    @source.setter
    def source(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                           TekTDS5xx.Source):
            raise TypeError("Source setting must be a `TekTDS5xx.Source`"
                " value, got {} instead.".format(type(newval)))

        self._tek.sendcmd("MEASU:MEAS{}:SOURCE {}".format(self._id,
                                                          newval.value))
    
    @property
    def source2(self):
        """
        Gets/Sets the Measurement Source2
        
        :type: `TekTDS5xx.Source`
        """
        resp = self._tek.query("MEASU:MEAS{}:SOURCE2?".format(self._id))
        return TekTDS5xx.Source[resp]
    
    @source2.setter
    def source2(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                           TekTDS5xx.Source):
            raise TypeError("Source setting must be a `TekTDS5xx.Source`"
                " value, got {} instead.".format(type(newval)))

        self._tek.sendcmd("MEASU:MEAS{}:SOURCE2 {}".format(self._id,
                                                          newval.value))
    
    @property
    def state(self):
        """
        Gets/Sets if this Measurement is enabled
        
        :type: `bool`
        """
        resp = self._tek.query('MEASU:MEAS{}:STATE?'.format(self._id))
        return _string_to_bool(resp)
    
    @state.setter
    def state(self, newval):
        if not isinstance(newval, bool):
            raise ValueError("Expected bool but got"
                                            "{} instead".format(type(newval)))
        self._tek.sendcmd('MEASU:MEAS{}:STATE {}'.format(self._id, int(newval)))
    
    @property
    def type(self):
        """
        Gets/Sets the Measurement Type
        
        :type: `TekTDS5xx.Measurement`
        """
        resp = self._tek.query("MEASU:MEAS{}:TYPE?".format(self._id))
        return TekTDS5xx.Measurement[resp]
    
    @type.setter
    def type(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                        TekTDS5xx.Measurement):
            raise TypeError(
                "Measurement setting must be a `TekTDS5xx.Measurement`"
                " value, got {} instead.".format(type(newval)))

        self._tek.sendcmd("MEASU:MEAS{}:TYPE {}".format(self._id,
                                                          newval.value))
    
    @property
    def units(self):
        """
        Gets the units the measurement is in
        
        :type: `string`
        """
        resp = self._tek.query("MEASU:MEAS{}:UNITS?".format(self._id))
        return resp
    
    @property
    def value(self):
        """
        Gets the Measured value
        
        :type: `float`
        """
        resp = self._tek.query("MEASU:MEAS{}:VALUE?".format(self._id))
        return float(resp)
        

class _TekTDS5xxDataSource(OscilloscopeDataSource):
    """
    Class representing a data source (channel, math, or ref) on the Tektronix 
    TDS 5xx.
    
    .. warning:: This class should NOT be manually created by the user. It is 
        designed to be initialized by the `TekTDS5xx` class.
    """
    
    def __init__(self, tek, name):
        self._tek = tek
        self._name = name
        self._old_dsrc = None
        
    @property
    def name(self):
        """
        Gets the name of this data source, as identified over SCPI.
        
        :type: `str`
        """
        return self._name
    
    def __enter__(self):
        self._old_dsrc = self._tek.data_source
        if self._old_dsrc != self:
            # Set the new data source, and let __exit__ cleanup.
            self._tek.data_source = self
        else:
            # There's nothing to do or undo in this case.
            self._old_dsrc = None
        
    def __exit__(self, type, value, traceback):
        if self._old_dsrc is not None:
            self._tek.data_source = self._old_dsrc
        
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            return other.name == self.name
    
    def read_waveform(self, bin_format=True):
        """
        Read waveform from the oscilloscope.
        This function is all inclusive. After reading the data from the 
        oscilloscope, it unpacks the data and scales it accordingly.
        
        Supports both ASCII and binary waveform transfer. For 2500 data 
        points, with a width of 2 bytes, transfer takes approx 2 seconds for 
        binary, and 7 seconds for ASCII over Galvant Industries' GPIBUSB 
        adapter.
        
        Function returns a tuple (x,y), where both x and y are numpy arrays.
        
        :param bool bin_format: If `True`, data is transfered
            in a binary format. Otherwise, data is transferred in ASCII.
        
        :rtype: two item `tuple` of `numpy.ndarray`
        """
        with self:
            
            if not bin_format:
                # Set the data encoding format to ASCII
                self._tek.sendcmd('DAT:ENC ASCI')
                raw = self._tek.query('CURVE?')
                raw = raw.split(',') # Break up comma delimited string
                raw = map(float, raw) # Convert each list element to int
                raw = np.array(raw) # Convert into numpy array
            else:
                # Set encoding to signed, big-endian
                self._tek.sendcmd('DAT:ENC RIB')
                data_width = self._tek.data_width
                self._tek.sendcmd('CURVE?')
                # Read in the binary block, data width of 2 bytes
                raw = self._tek.binblockread(data_width)

                self._tek._file.flush_input() # Flush input buffer
            
            # Retrieve Y offset
            yoffs = self._tek.query('WFMP:{}:YOF?'.format(self.name))
            # Retrieve Y multiply
            ymult = self._tek.query('WFMP:{}:YMU?'.format(self.name))
            # Retrieve Y zero
            yzero = self._tek.query('WFMP:{}:YZE?'.format(self.name))
            
            y = ((raw - float(yoffs)) * float(ymult)) + float(yzero)
            
            # Retrieve X incr
            xincr = self._tek.query('WFMP:{}:XIN?'.format(self.name))
            # Retrieve number of data points
            ptcnt = self._tek.query('WFMP:{}:NR_P?'.format(self.name))  
            
            x = np.arange(float(ptcnt)) * float(xincr)
            
            
            return (x, y)
            
class _TekTDS5xxChannel(_TekTDS5xxDataSource, OscilloscopeChannel):
    """
    Class representing a channel on the Tektronix TDS 5xx.
    
    This class inherits from `_TekTDS5xxDataSource`.
    
    .. warning:: This class should NOT be manually created by the user. It is 
        designed to be initialized by the `TekTDS5xx` class.
    """
    
    def __init__(self, parent, idx):
        super(_TekTDS5xxChannel, self).__init__(parent, "CH{}".format(idx + 1))
        self._idx = idx + 1

    @property
    def coupling(self):
        """
        Gets/sets the coupling setting for this channel.

        :type: `TekTDS5xx.Coupling`
        """
        return TekTDS5xx.Coupling[self._tek.query("CH{}:COUPL?".format(
                                                                self._idx)
                                                                )]
    @coupling.setter
    def coupling(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                           TekTDS5xx.Coupling):
            raise TypeError("Coupling setting must be a `TekTDS5xx.Coupling`"
                " value, got {} instead.".format(type(newval)))

        self._tek.sendcmd("CH{}:COUPL {}".format(self._idx, newval.value))
        
    @property
    def bandwidth(self):
        """
        Gets/sets the Bandwidth setting for this channel.

        :type: `TekTDS5xx.Bandwidth`
        """
        return TekTDS5xx.Bandwidth[self._tek.query("CH{}:BAND?".format(
                                                                self._idx)
                                                                )]
    @bandwidth.setter
    def bandwidth(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                           TekTDS5xx.Bandwidth):
            raise TypeError("Bandwidth setting must be a `TekTDS5xx.Bandwidth`"
                " value, got {} instead.".format(type(newval)))

        self._tek.sendcmd("CH{}:BAND {}".format(self._idx, newval.value))
        
    @property
    def impedance(self):
        """
        Gets/sets the impedance setting for this channel.

        :type: `TekTDS5xx.Impedance`
        """
        return TekTDS5xx.Impedance[self._tek.query("CH{}:IMP?".format(
                                                                self._idx)
                                                                )]
    @impedance.setter
    def impedance(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                           TekTDS5xx.Impedance):
            raise TypeError("Impedance setting must be a `TekTDS5xx.Impedance`"
                " value, got {} instead.".format(type(newval)))

        self._tek.sendcmd("CH{}:IMP {}".format(self._idx, newval.value))
        
    @property
    def probe(self):
        """
        Gets the connected probe value for this channel

        :type: `float`
        """
        return round(1/float(self._tek.query("CH{}:PRO?".format(self._idx))), 0)
    
    @property
    def scale(self):
        """
        Gets/sets the scale setting for this channel.

        :type: `TekTDS5xx.Impedance`
        """
        return float(self._tek.query("CH{}:SCA?".format(self._idx)))
    
    @scale.setter
    def scale(self, newval):
        self._tek.sendcmd("CH{0}:SCA {1:.3E}".format(self._idx, newval))
        resp = float(self._tek.query("CH{}:SCA?".format(self._idx)))
        if newval != resp:
            raise ValueError("Tried to set CH{0} Scale to {1} but got {2}"
                " instead".format(self._idx, newval, resp))
        
        
class TekTDS5xx(SCPIInstrument, Oscilloscope):
    """
    Support for the TDS5xx series of oscilloscopes
     Implemented from:
      | TDS Family Digitizing Oscilloscopes
      | (TDS 410A, 420A, 460A, 520A, 524A, 540A, 544A,
      | 620A, 640A, 644A, 684A, 744A & 784A)
      | Tektronix Document: 070-8709-07
    """

    ## ENUMS ##
    
    class Coupling(Enum):
        """
        Available coupling options for input sources and trigger
        """
        ac     = "AC"
        dc     = "DC"
        ground = "GND"
        
    class Bandwidth(Enum):
        """
        Bandwidth in MHz
        """
        Twenty     = "TWE"
        OneHundred = "HUN"
        TwoHundred = "TWO"
        FULL       = "FUL"
    
    class Impedance(Enum):
        """
        Available options for input source impedance
        """
        Fifty  = "FIF"
        OneMeg = "MEG"
        
    class Edge(Enum):
        """
        Available Options for trigger slope
        """
        Rising  = "RIS"
        Falling = "FALL"
        
    class Trigger(Enum):
        """
        Available Trigger sources
        (AUX not Available on TDS520A/TDS540A)
        """
        CH1  = "CH1"
        CH2  = "CH2"
        CH3  = "CH3"
        CH4  = "CH4"
        AUX  = "AUX"
        LINE = "LINE"
    
    class Source(Enum):
        """
        Available Data sources
        """
        CH1   = "CH1"
        CH2   = "CH2"
        CH3   = "CH3"
        CH4   = "CH4"
        Math1 = "MATH1"
        Math2 = "MATH2"
        Math3 = "MATH3"
        Ref1  = "REF1"
        Ref2  = "REF2"
        Ref3  = "REF3"
        Ref4  = "REF4"
        
    class Measurement(Enum):
        """
        Available Measurement Types
        """
        Amplitude  = "AMP"
        Area       = "ARE"
        Burst      = "BUR"
        Carea      = "CAR"
        Cmean      = "CME"
        Crms       = "CRM"
        Delay      = "DEL"
        Fall       = "FALL"
        Frequency  = "FREQ"
        High       = "HIGH"
        Low        = "LOW"
        Maximum    = "MAX"
        Mean       = "MEAN"
        Minimum    = "MINI"
        Nduty      = "NDU"
        Novershoot = "NOV"
        Nwidth     = "NWI"
        Pduty      = "PDU"
        Period     =  "PERI"
        Phase      = "PHA"
        Pk2pk      = "PK2"
        Povershoot = "POV"
        Pwidth     = "PWI"
        Rise       = "RIS"
        Rms        = "RMS"
    
    class Direction(Enum):
        """
        Available Directions for Measurements
        """
        Backwards = "BAC"
        Forwards  = "FORW"
    
    ## PROPERTIES ##
    @property
    def measurement(self):
        """
        Gets a specific oscilloscope measurement object. The desired channel is
        specified like one would access a list.
        
        :rtype: `_TDS5xxMeasurement`
        """
        return ProxyList(self, _TekTDS5xxMeasurement, xrange(4))
    
    
    @property
    def channel(self):
        """
        Gets a specific oscilloscope channel object. The desired channel is 
        specified like one would access a list.
        
        For instance, this would transfer the waveform from the first channel::
        
        >>> tek = ik.tektronix.TekTDS5xx.open_tcpip('192.168.0.2', 8888)
        >>> [x, y] = tek.channel[0].read_waveform()
        
        :rtype: `_TekTDS5xxChannel`
        """
        return ProxyList(self, _TekTDS5xxChannel, xrange(4))
        
    @property
    def ref(self):
        """
        Gets a specific oscilloscope reference channel object. The desired 
        channel is specified like one would access a list.
        
        For instance, this would transfer the waveform from the first channel::
        
        >>> tek = ik.tektronix.TekTDS5xx.open_tcpip('192.168.0.2', 8888)
        >>> [x, y] = tek.ref[0].read_waveform()
        
        :rtype: `_TekTDS5xxDataSource`
        """
        return ProxyList(self,
            lambda s, idx: _TekTDS5xxDataSource(s, "REF{}".format(idx  + 1)),
            xrange(4))
        
    @property
    def math(self):
        """
        Gets a data source object corresponding to the MATH channel.
        
        :rtype: `_TekTDS5xxDataSource`
        """
        return ProxyList(self,
            lambda s, idx: _TekTDS5xxDataSource(s, "MATH{}".format(idx  + 1)),
            xrange(3))
    
    @property
    def sources(self):
        """
        Returns list of all active sources
        
        :rtype: `list`
        """
        active = []
        channels = map(int, self.query('SEL?').split(';')[0:11])
        for idx in range(0, 4):
            if channels[idx]:
                active.append(_TekTDS5xxChannel(self, idx))
        for idx in range(4, 7):
            if channels[idx]:
                active.append(_TekTDS5xxDataSource(self, "MATH{}".format(
                                                                        idx-3)))
        for idx in range(7, 11):
            if channels[idx]:
                active.append(_TekTDS5xxDataSource(self, "REF{}".format(idx-6)))
        return active
		
    @property
    def data_source(self):
        """
        Gets/sets the the data source for waveform transfer.
        
        :type: `TekTDS5xx.Source` or `_TekTDS5xxDataSource`
        :rtype: '_TekTDS5xxDataSource`
        """
        name = self.query("DAT:SOU?")
        if name.startswith("CH"):
            return _TekTDS5xxChannel(self, int(name[2:]) - 1)
        else:
            return _TekTDS5xxDataSource(self, name)
        
    @data_source.setter
    def data_source(self, newval):
        if isinstance(newval, _TekTDS5xxDataSource):
            newval = TekTDS5xx.Source[newval.name]
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                            TekTDS5xx.Source):
            raise TypeError("Source setting must be a `TekTDS5xx.Source`"
                " value, got {} instead.".format(type(newval)))

        self.sendcmd("DAT:SOU {}".format(newval.value))
        time.sleep(0.01) # Let the instrument catch up.
        
    @property
    def data_width(self):
        """
        Gets/Sets the data width for waveform transfers
        
        :type: `int`
        """
        return int(self.query("DATA:WIDTH?"))
    @data_width.setter
    def data_width(self, newval):
        if int(newval) not in [1, 2]:
            raise ValueError("Only one or two byte-width is supported.")
        
        self.sendcmd("DATA:WIDTH {}".format(newval))

    @property
    def force_trigger(self):
        raise NotImplementedError
    
    @property
    def horizontal_scale(self):
        """
        Get/Set Horizontal Scale
        
        :type: `float`
        """
        return float(self.query('HOR:MAI:SCA?'))
    
    @horizontal_scale.setter
    def horizontal_scale(self, newval):
        self.sendcmd("HOR:MAI:SCA {0:.3E}".format(newval))
        resp = float(self.query('HOR:MAI:SCA?'))
        if newval != resp:
            raise ValueError("Tried to set Horizontal Scale to {} but got {}"
                " instead".format(newval, resp))
    @property
    def trigger_level(self):
        """
        Get/Set trigger level

        :type: `float`
        """
        return float(self.query('TRIG:MAI:LEV?'))
    
    @trigger_level.setter
    def trigger_level(self, newval):
        self.sendcmd("TRIG:MAI:LEV {0:.3E}".format(newval))
        resp = float(self.query('TRIG:MAI:LEV?'))
        if newval != resp:
            raise ValueError("Tried to set trigger level to {} but got {}"
                " instead".format(newval, resp))
        
    @property
    def trigger_coupling(self):
        """
        Get/Set trigger coupling
        
        :type: `TekTDS5xx.Coupling`
        """
        return TekTDS5xx.Coupling[self.query("TRIG:MAI:EDGE:COUP?")]
    
    @trigger_coupling.setter
    def trigger_coupling(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                   TekTDS5xx.Coupling):
            raise TypeError("Coupling setting must be a `TekTDS5xx.Coupling`"
                " value, got {} instead.".format(type(newval)))

        self.sendcmd("TRIG:MAI:EDGE:COUP {}".format(newval.value))
    
    @property
    def trigger_slope(self):
        """
        Get/Set trigger slope
        
        :type: `TekTDS5xx.Edge`
        """
        return TekTDS5xx.Edge[self.query("TRIG:MAI:EDGE:SLO?")]
    
    @trigger_slope.setter
    def trigger_slope(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                   TekTDS5xx.Edge):
            raise TypeError("Edge setting must be a `TekTDS5xx.Edge`"
                " value, got {} instead.".format(type(newval)))

        self.sendcmd("TRIG:MAI:EDGE:SLO {}".format(newval.value))
    
    @property
    def trigger_source(self):
        """
        Get/Set trigger source
        
        :type: `TekTDS5xx.Trigger`
        """
        return TekTDS5xx.Trigger[self.query("TRIG:MAI:EDGE:SOU?")]
    
    @trigger_source.setter
    def trigger_source(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                   TekTDS5xx.Trigger):
            raise TypeError(
                "Trigger source setting must be a`TekTDS5xx.source` value,"
                " got {} instead.".format(type(newval)))

        self.sendcmd("TRIG:MAI:EDGE:SOU {}".format(newval.value))
    
    @property
    def clock(self):
        """
        Get/Set oscilloscope clock
        
        :type: `datetime.datetime`
        """
        resp = self.query('DATE?;:TIME?')
        return datetime.strptime(resp, '"%Y-%m-%d";"%H:%M:%S"')
    
    @clock.setter
    def clock(self, newval):
        if not isinstance(newval, datetime):
            raise ValueError("Expected datetime.datetime"
                "but got {} instead".format(type(newval)))
        self.sendcmd(newval.strftime('DATE "%Y-%m-%d";:TIME "%H:%M:%S"'))    
    
    @property
    def display_clock(self):
        """
        Get/Set the visibility of clock on the display
        
        :type: `bool`
        """
        resp = self.query('DISPLAY:CLOCK?')
        return _string_to_bool(resp)
    
    @display_clock.setter
    def display_clock(self, newval):
        if not isinstance(newval, bool):
            raise ValueError("Expected bool but got"
                                            "{} instead".format(type(newval)))
        self.sendcmd('DISPLAY:CLOCK {}'.format(int(newval)))
    
    
    def get_hardcopy(self):
        """
        Gets a screenshot of the display
        
        :rtype: `string`
        """
        self.sendcmd('HARDC:PORT GPI;HARDC:LAY PORT;:HARDC:FORM BMP')
        self.sendcmd('HARDC START')
        sleep(1)
        header = self.query("", size=54)
        #Get BMP Length in kilobytes from DIB header, because file header is bad
        length = reduce(operator.mul, struct.unpack('<iihh', header[18:30]))/8
        length = int(length)+8# Add 8 bytes for our monochrome colour table
        data = header+self.query("", size=length)
        self._file.flush_input() # Flush input buffer
        return data
        
