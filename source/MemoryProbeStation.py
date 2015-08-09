"""A simple series of classes to extend the pyvisa.py package to the equipment
at the memory probe station.

Jesse Engel
10/22/2013
"""
try:
    from pyvisa import visa


    import numpy as np

    #better compartamentalize config functions
    class Agilent_81110A(visa.GpibInstrument):
        """
        PULSEGEN
        Subclass for Agilent 81110A Pulse Generator
        PARENT:pyvisa.visa.GpibInstrument
        """
        def __init__(self, GpibAddress, external_trigger=False):
            visa.GpibInstrument.__init__(self, GpibAddress)
            
            self.external_trigger = external_trigger
            
            self.Pulse1 = {'LEADING':1e-5, 'WIDTH':10e-3, 'TRAILING':1e-5, \
            'DELAY':0.0, 'HIGH':2.0, 'IMPEDANCE':999e3, 'TYPE':'Voltage'}

            self.Pulse2 = {'LEADING':1e-6, 'WIDTH':10e-6, 'TRAILING':1e-6, \
            'DELAY':5e-3, 'HIGH':3.0, 'IMPEDANCE':999e3, 'TYPE':'Voltage'}

            self.init()
            self.config()


        def init(self):
            self.write('*RST')
            # print self.Pulse1['TYPE'], self.Pulse2['TYPE']

            if self.external_trigger:
                # External Trigger
                tmp = ":ARM:SOUR EXT;" \
                "SLOP POS;" \
                ":TRIG:SOUR IMM;" \
                ":TRIG:COUN 1;" \
                ":OUTP1 ON;" \
                ":OUTP2 ON;" 
                print 'Pulsegen External Trigger'
            else:
                # Computer Trigger
               tmp = ":ARM:SOUR MAN;" \
                "SLOP POS;" \
                ":TRIG:SOUR MAN;" \
                ":TRIG:COUN 1;" \
                ":OUTP1 ON;" \
                ":OUTP2 ON;" 

            self.write(tmp)


        def config(self):
            for channel, Pulse in enumerate((self.Pulse1, self.Pulse2)):
                #Need to change modes for V < 0, Make LOW always 0
                if float(Pulse['HIGH']) >= 0.0:
                    HIGH = float(Pulse['HIGH'])
                    LOW = 0
                    polarity = 'NORM'
                elif float(Pulse['HIGH']) < 0.0:
                    HIGH = 0
                    LOW = float(Pulse['HIGH'])
                    polarity = 'INV'


                tmp =   ':SOUR:PULS:WIDT<C> <Width>SEC;' \
                        ':SOUR:PULS:TRAN<C>:TRA:AUTO OFF;' \
                        ':SOUR:PULS:TRAN<C>:UNIT SEC;' \
                        ':SOUR:PULS:TRAN<C>:LEAD <Leading>SEC;' \
                        ':SOUR:PULS:TRAN<C>:TRA <Trailing>SEC;' \
                        ':OUTP<C>:POL <Polarity>;' \
                        ':SOUR:HOLD<C> <Type>;' \
                        ':SOUR:<Type><C>:LEV:HIGH <High>;' \
                        ':SOUR:<Type><C>:LEV:LOW <Low>;' \
                        ':SOUR:PULS:DEL<C>:UNIT SEC;' \
                        ':SOUR:PULS:DEL<C> <Delay>;' \
                        ':OUTP<C>:IMP:EXT <Imp>'

                tmp = tmp.replace('<C>', '%d' % (channel+1))
                tmp = tmp.replace('<Leading>', '%.2e' % Pulse['LEADING'])
                tmp = tmp.replace('<Width>', '%.2e' % Pulse['WIDTH'])
                tmp = tmp.replace('<Trailing>', '%.2e' % Pulse['TRAILING'])
                tmp = tmp.replace('<Delay>', '%.12f' % Pulse['DELAY'])
                tmp = tmp.replace('<High>', '%.2e' % HIGH)
                tmp = tmp.replace('<Low>', '%.2e' % LOW)
                tmp = tmp.replace('<Polarity>', '%s' % polarity)
                tmp = tmp.replace('<Imp>', '%.2f' % Pulse['IMPEDANCE'])
                tmp = tmp.replace('<Type>', '%s' % Pulse['TYPE'])

                # print tmp
                self.write(tmp)


        def trigger(self):
            self.write('*TRG')
            #self.wait_for_srq()


        # def __choose_pulse(self, pulse_num):
        #     try:
        #         return [self.Pulse1, self.Pulse2][int(channel)-1]
        #     except IndexError:
        #         print 'Channel must be 1 or 2'


        # def setPulseType(self, channel= 1, pulse_type='CURR'):
        #     '''
        #     Set pulse Type

        #     Keywords
        #     --------
        #     Channel : int
        #         1 or 2

        #     Type : string
        #         'CURR' or 'VOLT'
        #     '''
        #     p = __choose_pulse(channel)
        #     p['TYPE'] = pulse_type
        #     self.config()







    class Keithley_700B(visa.GpibInstrument):
        """SWITCH
        Subclass for Keithley 700B Switch Matrix
        PARENT:pyvisa.visa.GpibInstrument
        """
        def __init__(self, GpibAddress):
            visa.GpibInstrument.__init__(self, GpibAddress)
            self.reset()

        def reset(self):
            self.write('errorqueue.clear() localnode.prompts = 0 localnode.showerrors = 0 reset()')
            self.ask('*OPC?') #Wait for Operation Complete

        def close(self,close_string):
            self.write('channel.close(\'%s\')' % close_string)
            self.ask('*OPC?')

        def open(self,open_string):
            self.write('channel.open(\'%s\')' % open_string)
            self.ask('*OPC?')











    class Agilent_4155C(visa.GpibInstrument):
        """
        SMU
        Subclass for Agilent 4155C Semiconductor Parameter Analyzer
        PARENT:pyvisa.visa.GpibInstrument

        This instrument is just used for measuring the DUT, not pulsing.
        """
        def __init__(self, GpibAddress):
            visa.GpibInstrument.__init__(self, GpibAddress)

            #Create SMU attributes
            self.Vread = 0.1 #Volts
            self.Vgate = 3.0 #Volts

            #Sweep Charecteristics
            self.sweep = False
            self.Vlow = 0.0
            self.Vstep = 10e-3
            self.Vhigh = 1.0
            self.sweep_mode = 'SINGLE' # SINGLE | DOUBLE
            self.linlog = 'LIN' # LIN | L10 | L25 | L50 (steps/decade)
            self.compliance = 100e-3
            self.integration_time = 'LONG' #  SHORT, MEDIUM, LONG

            self.chip_type = 'Macro' # Macro | Kilobit

            #Reconfigure the SMU
            self.config()


        def config(self):
            if self.chip_type == 'Macro':
                self.SMU1 = {'FUNCTION':'VAR1', 'INAME':'\'Iread\'', 'VNAME':'\'Vread\'', \
                'MODE':'V', 'SRES':'0', 'STANDBY': 'OFF'}

                self.SMU2 = {'FUNCTION':'CONSTANT', 'INAME':'\'Igate\'', 'VNAME':'\'Vgate\'', \
                'MODE':'V', 'SRES':'0', 'STANDBY':'OFF'}

                self.SMU3 = {'FUNCTION':'CONSTANT', 'INAME':'\'Isx\'', 'VNAME':'\'Vsx\'', \
                'MODE':'COMMON', 'STANDBY':'OFF'}

                self.SMU4 = {'FUNCTION':'CONSTANT', 'INAME':'\'Ics\'', 'VNAME':'\'Vcs\'', \
                'MODE':'COMMON', 'STANDBY':'OFF'}

                #Reset
                self.write('*RST')

                #Turn on the output trigger
                self.write('PAGE:MEAS:OSEQ:TRIG ON')
                self.write('PAGE:MEAS:OSEQ:TRIG:TIME 1E-3')

                #Make the Integration Time Long
                self.SetIntegrationTime(self.integration_time)

                #Turn off autocalibrate
                self.write('CAL:AUTO OFF')
                
                #Show the channel page
                self.write('PAGE:CHAN:ALL:DIS')


                #Set All Channels
                for channel, SMU in enumerate((self.SMU1, self.SMU2, self.SMU3, self.SMU4)):
                        for key in SMU:
                                self.write(":PAGE:CHAN:SMU%d:%s %s" % (channel+1, key, SMU[key]))
                                #print ":PAGE:CHAN:SMU%d:%s %s" % (channel+1, key, SMU[key])

                #Set User Function (Read Resistance)
                self.write(":PAGE:CHAN:UFUN:DEL:ALL")
                self.write(":PAGE:CHAN:UFUN:DEF \'Rread\',\'OHMS\',\'%s/%s\'" % \
                        (self.SMU1['VNAME'].strip("\'"), self.SMU1['INAME'].strip("\'")))

                #Set autorange for all smus
                for i in range(1,5):
                    self.write('PAGE:MEAS:MSET:SMU%s:RANG:MODE AUTO' % i)

                if not self.sweep:
                    #Set Read Voltage (Bitline)
                    self.write('PAGE:MEAS:SWE:VAR1:START %.4f' % self.Vread)
                    self.write('PAGE:MEAS:SWE:VAR1:STOP %.4f' % self.Vread)
                else:
                    #Set Read Voltage (Bitline)
                    self.write('PAGE:MEAS:SWE:VAR1:START %.4f' % self.Vlow)
                    if self.linlog == 'LIN':
                        self.write('PAGE:MEAS:SWE:VAR1:STEP %.4f' % self.Vstep)
                    self.write('PAGE:MEAS:SWE:VAR1:STOP %.4f' % self.Vhigh)
                    self.write('PAGE:MEAS:SWE:VAR1:SPACING %s' % self.linlog)
                    self.write('PAGE:MEAS:SWE:VAR1:COMPLIANCE %.4f' % self.compliance)
                    self.write('PAGE:MEAS:SWE:VAR1:MODE %s' % self.sweep_mode)


                #Set Gate Voltage (Wordline)
                self.write('PAGE:MEAS:CONS:SMU2:SOUR  %.4f' % self.Vgate)

            else:
                self.SMU1 = {'FUNCTION':'CONSTANT', 'INAME':'\'Ignd\'', 'VNAME':'\'Vgnd\'', \
                'MODE':'COMMON', 'STANDBY':'OFF'}

                self.SMU2 = {'FUNCTION':'CONSTANT', 'INAME':'\'Iint1\'', 'VNAME':'\'Vint1\'', \
                'MODE':'V', 'STANDBY':'OFF'}

                self.SMU3 = {'FUNCTION':'CONSTANT', 'INAME':'\'Iint2\'', 'VNAME':'\'Vint2\'', \
                'MODE':'V', 'SRES':'0', 'STANDBY':'OFF'}

                self.SMU4 = {'FUNCTION':'VAR1', 'INAME':'\'Iread\'', 'VNAME':'\'Vread\'', \
                'MODE':'V', 'SRES':'0', 'STANDBY': 'OFF'}

                #Reset
                self.write('*RST')

                #Turn on the output trigger
                self.write('PAGE:MEAS:OSEQ:TRIG ON')
                self.write('PAGE:MEAS:OSEQ:TRIG:TIME 1E-3')

                #Make the Integration Time Long
                self.SetIntegrationTime(self.integration_time)

                #Turn off autocalibrate
                self.write('CAL:AUTO OFF')
                
                #Show the channel page
                self.write('PAGE:CHAN:ALL:DIS')


                #Set All Channels
                for channel, SMU in enumerate((self.SMU1, self.SMU2, self.SMU3, self.SMU4)):
                        for key in SMU:
                                self.write(":PAGE:CHAN:SMU%d:%s %s" % (channel+1, key, SMU[key]))
                                #print ":PAGE:CHAN:SMU%d:%s %s" % (channel+1, key, SMU[key])

                #Set User Function (Read Resistance)
                self.write(":PAGE:CHAN:UFUN:DEL:ALL")
                self.write(":PAGE:CHAN:UFUN:DEF \'Rread\',\'OHMS\',\'%s/%s\'" % \
                        (self.SMU4['VNAME'].strip("\'"), self.SMU4['INAME'].strip("\'")))

                #Set autorange for all smus
                for i in range(1,5):
                    self.write('PAGE:MEAS:MSET:SMU%s:RANG:MODE AUTO' % i)

                if not self.sweep:
                    #Set Read Voltage (Bitline)
                    self.write('PAGE:MEAS:SWE:VAR1:START %.4f' % self.Vread)
                    self.write('PAGE:MEAS:SWE:VAR1:STOP %.4f' % self.Vread)
                else:
                    #Set Read Voltage (Bitline)
                    self.write('PAGE:MEAS:SWE:VAR1:START %.4f' % self.Vlow)
                    if self.linlog == 'LIN':
                        self.write('PAGE:MEAS:SWE:VAR1:STEP %.4f' % self.Vstep)
                    self.write('PAGE:MEAS:SWE:VAR1:STOP %.4f' % self.Vhigh)
                    self.write('PAGE:MEAS:SWE:VAR1:SPACING %s' % self.linlog)
                    self.write('PAGE:MEAS:SWE:VAR1:COMPLIANCE %.4f' % self.compliance)
                    self.write('PAGE:MEAS:SWE:VAR1:MODE %s' % self.sweep_mode)


                #Set Gate Voltage (Wordline)
                self.write('PAGE:MEAS:CONS:SMU2:SOUR  %.4f' % self.Vgate)
                self.write('PAGE:MEAS:CONS:SMU3:SOUR  %.4f' % self.Vgate)



        def SetIntegrationTime(self, integration_time):
            """Options: SHORT, MEDIUM, LONG"""
            self.write(':PAGE:MEAS:MSET:ITIM %s' % str(integration_time))
            self.integration_time = integration_time
    #        print integration_time


        def measure(self):
            #Take a measurement
            self.write('*CLS;*ESE 1;*SRE 32;:PAGE:SCON:SING;*OPC;')
            self.wait_for_srq()
            self.ask('*ESR?;*SRE 0;*ESE 0;')

            #Read the device resistance
            R = self.ask(":DATA? \'%s\'" % 'Rread')
            return R



        def measureTrace(self, read_all=False):
            #Take a measurement
            self.write('*CLS;*ESE 1;*SRE 32;:PAGE:SCON:SING;*OPC;')
            self.wait_for_srq()
            self.ask('*ESR?;*SRE 0;*ESE 0;')

            if not read_all:
                #Read the IV curve
                V = self.ask(":DATA? %s" % self.SMU1['VNAME'])
                I = self.ask(":DATA? %s" % self.SMU1['INAME'])

                V = np.array(V.split(',')).astype('float')
                I = np.array(I.split(',')).astype('float')        
                return np.array([V, I])

            else:
                #Read the IV curve
                V1 = self.ask(":DATA? %s" % self.SMU1['VNAME'])
                I1 = self.ask(":DATA? %s" % self.SMU1['INAME'])
                V1 = np.array(V1.split(',')).astype('float')
                I1 = np.array(I1.split(',')).astype('float')    

                V2 = self.ask(":DATA? %s" % self.SMU2['VNAME'])
                I2 = self.ask(":DATA? %s" % self.SMU2['INAME'])
                V2 = np.array(V2.split(',')).astype('float')
                I2 = np.array(I2.split(',')).astype('float')    

                V3 = self.ask(":DATA? %s" % self.SMU3['VNAME'])
                I3 = self.ask(":DATA? %s" % self.SMU3['INAME'])
                V3 = np.array(V3.split(',')).astype('float')
                I3 = np.array(I3.split(',')).astype('float')    

                V4 = self.ask(":DATA? %s" % self.SMU4['VNAME'])
                I4 = self.ask(":DATA? %s" % self.SMU4['INAME'])
                V4 = np.array(V4.split(',')).astype('float')
                I4 = np.array(I4.split(',')).astype('float')    
                return np.array([[V1, I1], [V2, I2], [V3, I3], [V4, I4]])

except OSError:
    print 'You have no LabView VISA Installed'



                
if __name__ == "__main__":
    switch = Keithley_700B("GPIB::20")
    smu = Agilent_4155C("GPIB::18")
    pulsegen = Agilent_81110A("GPIB::11")

    print switch.ask("*IDN?")
    print smu.ask("*IDN?")
    print pulsegen.ask("*IDN?")
