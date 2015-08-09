from __future__ import division
import time
import numpy as np
import os, sys
try:
    from wx.lib.pubsub import Publisher as pub
except ImportError:
    from wx.lib.pubsub import pub

from threading import Thread

#My Classes
import MemoryProbeStation


class WorkerThread(Thread):
    '''
    WorkerThread:
        Runs the model methods in a multithreaded manner.
    '''
    def __init__(self, model, user_programs):
        Thread.__init__(self)
        self.model = model
        self.user_programs = user_programs
            
    def run(self):
        self.model.checkInitialized()

        if hasattr(self.model, self.model.current_program):
            getattr(self.model, self.model.current_program)()
        
        elif hasattr(self.user_programs, self.model.current_program):
            getattr(self.user_programs, self.model.current_program)()

        pub.sendMessage('Finished')


    

class Model(Thread):
    """
    The Model:
        Contains all Programs and Data
        Linked to the View by the Controller
    """
    def __init__(self):        
        ### GUI Accessable Attributes
        self.data_Pulse = np.array([])
        self.data_R = np.array([])
        self.data_V = np.array([])

        self.run_number = 0 

        # Persistent Filename Memory
        try:
            path = os.path.join(self.__get_module_path(), 'program_data.npz')
            self.filename = str(np.load(path)['filename'])
        except (IOError, KeyError):
            self.filename = 'C:\Users\memory\Desktop\data.txt'

        try:
            path = os.path.join(self.__get_module_path(), 'program_data.npz')
            self.user_programs_filename = str(np.load(path)['user_programs_filename'])
        except (IOError, KeyError):
            self.user_programs_filename = 'UserProgramsDefault'



        #Run Programs
        self.initialized = False
        self.hardware_changed = False
        self.smu_changed = False
        self.current_program = ''
        self.current_pulse = 'Set'
        self.want_to_abort = False
        self.chip_type = 'Macro' 

        # Read functions
        self.Vread = 0.1
        self.Vgate = 3.0
        self.integration_time = 'MEDIUM'
        #Create pulse profiles

        # Switch Matrix Addresses
        # Bitline = PCM, Wordline = Gate
        self.bl_card = '1'
        self.wl_card = '2'
        self.pulse_bl_or_wl = 'wl'  #bl | wl
        self.bl = 1
        self.wl = 1
        self.note = ''

        self.gate_width = 100e-6 #seconds

        self.set_pulse = {'LEADING':500e-9,
                          'WIDTH':5000e-9,
                          'TRAILING':500e-9, 
                          'DELAY':self.gate_width/2, 
                          'HIGH':1.5, 
                          'IMPEDANCE':100e3,
                          'TYPE':'Voltage'}

        self.reset_pulse = {'LEADING':5e-9,
                            'WIDTH':50e-9,
                            'TRAILING':5e-9, 
                            'DELAY':self.gate_width/2, 
                            'HIGH':3.0, 
                            'IMPEDANCE':100e3,
                            'TYPE':'Voltage'}
                            
        self.gate_pulse = {'LEADING':10e-6, 
                           'WIDTH':self.gate_width, 
                           'TRAILING':10e-6,
                           'DELAY':0.0, 
                           'HIGH':3.0, 
                           'IMPEDANCE':100e3,
                           'TYPE':'Voltage'}
        # self.set_pulse['DELAY'] = self.gate_width - self.set_pulse['WIDTH']/2. - self.set_pulse['LEADING'] 
        #Convert all to strings
        # for k,v in self.set_pulse.items():
        #     self.set_pulse[k] = str(v)
        # for k,v in self.reset_pulse.items():
        #     self.reset_pulse[k] = str(v)
        # for k,v in self.gate_pulse.items():
        #     self.gate_pulse[k] = str(v)





    ### Internal Functions ###

    def __get_module_path(self):
        encoding = sys.getfilesystemencoding()
        if hasattr(sys, "frozen"):
            return os.path.dirname(unicode(sys.executable, encoding))
        return os.path.dirname(unicode(__file__, encoding))



    def __setAddress(self, bl, wl):
        """
        Always route SMU 1,3,4 to bl, and SMU2 to wl.
        Route PMU 1 to what you want to pulse, and PMU 2 to the other.
        ----------
        SMU1 (Com)    ->  (bl_card)A
        SMU2 (Gate)    -> (wl_card)A
        SMU3 (Gate)     -> (bl_card)C
        SMU4 (Read)     -> (bl_card)D
        PMU1 (Program) -> (pulse_bl_or_wl)B
        PMU2 (Access)  -> (not_pulse_bl_or_wl)B

        CS(bitline-12) -> (bl_card)11
        SX(bitline-13) -> (bl_card)12
        ----------

        Pulse:
        (bl_card)B->bl, (wl_card)B->wl, (bl_card)C->11, (bl_card)D->12
        Read:
        (bl_card)A->bl, (wl_card)A->wl, (bl_card)C->11, (bl_card)D->12

        """
        if self.chip_type == 'Macro':


            #Connect the SMU and Pulsegen like so:
            addr_smu1 = self.bl_card + 'A'   #read 
            addr_smu2 = self.wl_card + 'A'   #gate 
            addr_smu3 = self.bl_card + 'C'   #cs (common source)
            addr_smu4 = self.bl_card + 'D'   #sx (substrate body)
            addr_pmu1 = self.bl_card + 'B'   #program  
            addr_pmu2 = self.wl_card + 'B'   #access   

            #Set SMU address
            self.smu_addr =   addr_smu1 + '%02.0f'%(bl) + ',' + addr_smu2 + '%02.0f'%(wl) + ',' \
                            + addr_smu3 + '11' + ',' + addr_smu4 + '12'
            #Set Pulse address
            self.pulse_addr = addr_pmu1 + '%02.0f'%(bl) + ',' + addr_pmu2 + '%02.0f'%(wl)

           #  #Connect the SMU and Pulsegen like so:
           #  addr_smu1 = self.bl_card + 'D'   #ground 
           #  addr_smu2 = None
           #  addr_smu3 = self.wl_card + 'A'   #gate
           #  addr_smu4 = self.bl_card + 'A'   #read
           #  addr_pmu1 = self.bl_card + 'B'   #program  
           #  addr_pmu2 = self.wl_card + 'B'   #access   

           #  #Set SMU address
           #  self.smu_addr =   addr_smu4 + '%02.0f'%(bl) + ',' + addr_smu3 + '%02.0f'%(wl) + ',' \
           #                  + addr_smu1 + '11' + ',' + addr_smu1 + '12'
           #  #Set Pulse address
           #  self.pulse_addr = addr_pmu1 + '%02.0f'%(bl) + ',' + addr_pmu2 + '%02.0f'%(wl)

           # # print "SMU ADDR (Read,Gate,Common,Common):", self.smu_addr; print "PMU ADDR (Program,Access):", self.pulse_addr


        if self.chip_type == 'Kilobit':
            # print bl
            # print wl

            bl=int( bin(bl)[2:] )
            wl=int( bin(wl)[2:] )
            addr_binary = '%06d'%(bl)+'%05d'%(wl)
            print "combined addr:%s" %addr_binary

            addr_temp=addr_binary.replace('1','B')
            addr = addr_temp.replace('0','A')
            # print addr

            switchAddr = ''
            for i in range(0,11):
                switchAddr = switchAddr + '1' +addr[i]+'%02.0f'%(i+1)+','        
            switchAddr = switchAddr+'1C12,'
            switchAddr = switchAddr+'2A01,2C02,2A03,2B04,2C05,2A06,2C07,2A08,2C09,2A10,2B11,2C12'
            # print switchAddr

            #Set SMU address
            self.smu_addr = switchAddr
            self.pulse_addr = switchAddr.replace('1C12','1D12')
            # print self.pulse_addr


                   
    def __smuMeasure(self):
        #Check to see if program is aborted each measurement                       
        self.switch.reset() 
        self.switch.close(self.smu_addr)

        R = self.smu.measure()
        
        V = [self.reset_pulse['HIGH'], self.set_pulse['HIGH']][self.current_pulse == 'Set']        
        return R

    def __pulse(self, count=1):      
        self.switch.reset()
        self.switch.close(self.pulse_addr)

        for i in range(count):            
            if self.pulsegen.external_trigger:
                #External Trigger
                self.smu.measure()
            else:
                #Manual Trigger
                self.pulsegen.trigger()

    def __pulseAndMeasure(self):      
        self.switch.reset()
        self.switch.close(self.pulse_addr)
        
        if self.pulsegen.external_trigger:
            #External Trigger
            self.smu.measure()
        else:
            #Manual Trigger
            self.pulsegen.trigger()

        #Measure Resistance
        R = self.__smuMeasure()
        return R

    def __addPulseToSavefile(self, newPulse, newR, ReadOnly=False):
        if ReadOnly:
            self.savefile.write(  str(newPulse) + '\t' +str(newR) + '\t' \
                                + 'Read' + '\t' + 'x' + '\t' \
                                + 'x' + '\t' + 'x' + '\t' + 'x' + '\t' \
                                + str(self.bl) +'\t' +str(self.wl) + '\t' + str(self.note) + '\n')
            newV = 0
        else:
            if self.current_pulse == 'Reset':
                p = self.reset_pulse
            else:
                p = self.set_pulse

            self.savefile.write(  str(newPulse) + '\t' +str(newR) + '\t' \
                                + self.current_pulse + '\t' + str(p['HIGH']) + '\t' \
                                + str(p['LEADING']) + '\t' + str(p['WIDTH']) + '\t' + str(p['TRAILING']) + '\t' \
                                + str(self.bl) +'\t' +str(self.wl) + '\t' + str(self.note) + '\n')
            newV = p['HIGH']

        self.data_Pulse = np.append(self.data_Pulse, newPulse)
        self.data_R = np.append(self.data_R, float(newR))
        self.data_V = np.append(self.data_V, float(newV))
        
        print 'R:%s\tV:%.2f\tBlWl:(%d,%d)' % (newR, newV, self.bl, self.wl)  
        pub.sendMessage('RefreshPlots')        



    ### USER FUNCTIONS ###        


    def checkInitialized(self):
        if self.initialized == False:
            self.Initialize() 
        if self.hardware_changed == True:
            pub.sendMessage('RefreshHardware')



    def Initialize(self):
        print "\n\nInitializing..."
        #Initilize the Instruments
        self.switch = MemoryProbeStation.Keithley_700B("GPIB::20")
        self.smu = MemoryProbeStation.Agilent_4155C("GPIB::18")
        self.pulsegen = MemoryProbeStation.Agilent_81110A("GPIB::11", external_trigger = True)

        print self.switch.ask("*IDN?")
        print self.smu.ask("*IDN?")
        print self.pulsegen.ask("*IDN?")

        self.ConfigureHardware()

        self.NewFile()
        self.initialized = True
        print 'Initialized!\n\n'
        

    def ConfigureHardware(self):
        #Configure the instruments
        self.smu.Vread = self.Vread
        self.smu.Vgate = self.Vgate
        self.smu.config()

        self.pulsegen.Pulse1 = self.set_pulse
        self.pulsegen.Pulse2 = self.gate_pulse
        self.pulsegen.config()


    def NewFile(self):
        self.run_number = int(self.run_number) + 1

        #Create data arrays
        self.data_Pulse = np.array([])
        self.data_R = np.array([])
        self.data_V = np.array([])

        try:
            self.savefile.close()
        except (NameError, AttributeError):
            pass

        #Open the file and write a header
        if self.filename.endswith('.txt'):
            self.full_filename = self.filename[:-4] + '_PS_' + str(self.run_number) + '.txt'
        else:
            self.full_filename = self.filename + '_PS_' + str(self.run_number) + '.txt'


        # pub.sendMessage('OverwriteWarning')

        self.savefile = open(self.full_filename, 'w')
        self.savefile.write(self.full_filename + '\n')
        self.savefile.write('%s/%02.0f/%02.0f %02.0f:%02.0f:%02.0f\n' % time.localtime()[0:6])
        self.savefile.write('Vread:%s, Vgate:%s\n\n' % (self.Vread, self.Vgate)) 
        self.savefile.write('Pulse\tR\tType\tV\tLead\tWidth\tTrail\tBitline\tWordline\tNote\n')   

        print "New File: %s" % self.full_filename
        pub.sendMessage('RefreshControls')



    def MeasureR(self):        
        self.checkInitialized()
        #Measure a new point
        self.__setAddress(self.bl, self.wl)
        newR = self.__smuMeasure()
        newPulse = self.data_Pulse.size
        #Append Data to File
        self.__addPulseToSavefile(newPulse, newR, ReadOnly=True)
     

    def Pulse(self):
        self.checkInitialized()
        #Measure a new point
        self.__setAddress(self.bl, self.wl)
        newR = self.__pulseAndMeasure()
        newPulse = self.data_Pulse.size
        #Append Data to File
        self.__addPulseToSavefile(newPulse, newR)

    def PulseManyTimes(self, count=10):
        self.checkInitialized()
        self.__setAddress(self.bl, self.wl)
        self.__pulse(count=count)