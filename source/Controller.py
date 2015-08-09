# Controller and Model imports
from __future__ import division
import wx
import os, sys, importlib
import numpy as np
try:
    from wx.lib.pubsub import Publisher as pub
except ImportError:
    from wx.lib.pubsub import pub


#My Classes
import Model
import View

try:
    #Add ../scripts/ to PYTHONPATH
    scripts_path = os.path.join(os.path.dirname(__file__), '..', 'scripts')
    sys.path.append(scripts_path)
except:
    print 'No ../scripts/ folder detected!'

# #Import the first non __init__.py python file in ../scripts/
# filename = [f for f in os.listdir(scripts_path) if f.endswith('.py') and not f.startswith('__')][0]
# filename = os.path.splitext(filename)[0]
# try:
#     UserPrograms = importlib.import_module(filename)
# except ImportError:
import UserProgramsDefault as UserPrograms



class Controller(object):
    def __init__(self, app):
        #Create objects
        self.model = Model.Model()
        self.view = View.View()

        self.user_programs = UserPrograms.UserPrograms(self)
        self.load_user_programs()

        #pub Subscriptions
        pub.subscribe(self.RefreshControls, "RefreshControls")
        pub.subscribe(self.RefreshPlots, "RefreshPlots")
        pub.subscribe(self.RefreshHardware, "RefreshHardware")
        pub.subscribe(self.Finished, "Finished")
        pub.subscribe(self.Abort, "Abort")
        pub.subscribe(self.OverwriteWarning, "OverwriteWarning")
        
        # Initialize the GUI
        self.model.current_program = self.user_programs.list[0]
        self.RefreshControls('')
        self.RefreshTextSetupInstructions('')
        self.worker = None

        ### BINDINGS ###

        #Button Bindings
        self.view.button_run.Bind(wx.EVT_BUTTON, self.on_button_run)
        self.view.button_abort.Bind(wx.EVT_BUTTON, self.on_button_abort)
        self.view.button_reload.Bind(wx.EVT_BUTTON, self.on_button_reload)
        self.view.button_filename.Bind(wx.EVT_BUTTON, self.on_button_filename)
        self.view.button_userprograms.Bind(wx.EVT_BUTTON, self.on_button_userprograms)
        self.view.button_new_file.Bind(wx.EVT_BUTTON, self.on_button_new_file)
        self.view.button_set_pulse.Bind(wx.EVT_BUTTON, self.on_button_set_pulse)
        self.view.button_reset_pulse.Bind(wx.EVT_BUTTON, self.on_button_reset_pulse)
        self.view.button_measure.Bind(wx.EVT_BUTTON, self.on_button_measure)

        # self.view.button_update.Bind(wx.EVT_BUTTON, self.on_button_update_pulses)

        #Combobox Bindings
        self.view.combo_chip_type.Bind(wx.EVT_COMBOBOX, self.on_combo_chip_type)
        self.view.combo_program.Bind(wx.EVT_COMBOBOX, self.on_combo_program)
        self.view.combo_bl_card.Bind(wx.EVT_COMBOBOX, self.on_combo_bl_card)
        self.view.combo_program_pulse.Bind(wx.EVT_COMBOBOX, self.on_combo_program_pulse)
        self.view.combo_integration_time.Bind(wx.EVT_COMBOBOX, self.on_combo_integration_time)


        #Textctrl Bindings
        self.BindTextCtrl(self.view.textctrl_filename, self.on_textctrl_filename)
        self.BindTextCtrl(self.view.textctrl_run_number, self.on_textctrl_run_number)
        self.BindTextCtrl(self.view.textctrl_bl, self.on_textctrl_blwl)
        self.BindTextCtrl(self.view.textctrl_wl, self.on_textctrl_blwl)
        self.BindTextCtrl(self.view.textctrl_vread, self.on_textctrl_vread)


        #Pulse Bindings
        self.BindPulsebox(self.view.pulsebox_set, self.UpdateModelPulses)
        self.BindPulsebox(self.view.pulsebox_reset, self.UpdateModelPulses)
        self.BindPulsebox(self.view.pulsebox_gate, self.UpdateModelPulses)


        #display the main frame
        self.view.Show()
        print 'Program Finished Loading!'






    ### Binding Convenience Functions 
    def BindTextCtrl(self, textctrl, function):
        """Convenience function to bind view.textctrl
        """
        event_list = [wx.EVT_TEXT_ENTER, wx.EVT_TEXT]
        for event in event_list:
            textctrl.Bind(event, function)



    def BindPulsebox(self, pulsebox, function):
        """Convenience function to bind view.pulsebox
        """
        event_list = [wx.EVT_TEXT_ENTER, wx.EVT_TEXT]
        # event_list = [wx.EVT_KEY_DOWN, wx.EVT_TEXT_ENTER]
        for event in event_list:
            pulsebox.textctrl_width.Bind(event, function)
            pulsebox.textctrl_lead.Bind(event, function)
            pulsebox.textctrl_trail.Bind(event, function)
            pulsebox.textctrl_delay.Bind(event, function)
            pulsebox.textctrl_voltage.Bind(event, function)
            pulsebox.textctrl_impedance.Bind(event, function)

        pulsebox.combo_type.Bind(wx.EVT_COMBOBOX, function)







    ### Subscribed Functions [Model Controls View]###

    def RefreshPlots(self, message):
        """This method is the handler for "RefreshPlots" messages,
        which pubsub will call as messages are sent from the model.
        """
        # print 'Plotting!'
        # print message.data
        self.view.R_plot.Refresh(self.model.data_Pulse, self.model.data_R)
        self.view.V_plot.Refresh(self.model.data_Pulse, self.model.data_V)


    def RefreshControls(self, message):
        """This method is the handler for "RefreshControls" messages
        which pubsub will call as messages are sent from the model.
        Bassically put any commands in here to Refresh the view controls.
        """
        if self.model.current_program in self.user_programs.list:
            self.view.combo_program.Clear()
            self.view.combo_program.AppendItems(self.user_programs.list)
            self.view.combo_program.SetValue(self.model.current_program)

        self.view.textctrl_filename.ChangeValue(str(self.model.filename))
        self.view.textctrl_run_number.ChangeValue(str(self.model.run_number))
        self.view.textctrl_bl.ChangeValue(str(int(self.model.bl)))
        self.view.textctrl_wl.ChangeValue(str(int(self.model.wl)))

        self.view.textctrl_vread.ChangeValue(str(float(self.model.Vread)))
        self.view.combo_chip_type.SetValue(str(self.model.chip_type))
        self.view.combo_bl_card.SetValue(str(self.model.bl_card))
        self.view.combo_program_pulse.SetValue(str(self.model.pulse_bl_or_wl))
        self.view.combo_integration_time.SetValue(str(self.model.integration_time))

        for pulsebox, pulse_dict in zip([self.view.pulsebox_set, self.view.pulsebox_reset, self.view.pulsebox_gate], \
                                       [self.model.set_pulse, self.model.reset_pulse, self.model.gate_pulse]):
            pulsebox.textctrl_lead.ChangeValue( str(pulse_dict['LEADING']) )
            pulsebox.textctrl_trail.ChangeValue( str(pulse_dict['TRAILING']) )
            pulsebox.textctrl_width.ChangeValue( str(pulse_dict['WIDTH']) )
            pulsebox.textctrl_delay.ChangeValue( str(pulse_dict['DELAY']) )
            pulsebox.textctrl_impedance.ChangeValue( '%.2e' % int(pulse_dict['IMPEDANCE']) )
            pulsebox.textctrl_voltage.ChangeValue(str(pulse_dict['HIGH']))
            pulsebox.combo_type.SetValue( str(pulse_dict['TYPE']) )



    def RefreshTextSetupInstructions(self, message):
        chip_type = self.view.combo_chip_type.GetValue()

        # Determine program_pulse
        if self.model.pulse_bl_or_wl == 'bl':
            program_pulse = self.model.bl_card
            access_pulse = self.model.wl_card
        elif self.model.pulse_bl_or_wl == 'wl':
            program_pulse = self.model.wl_card
            access_pulse = self.model.bl_card

        # Initialize the setup text        
        if chip_type == 'Macro':
            tmp = """
            Macro Setup:
            ------------
            SMU1 (Read)    -> (bl_card)A
            SMU2 (Gate)     -> (wl_card)A
            SMU3 (Com)     -> (bl_card)C
            SMU4 (Com)     -> (bl_card)D
            CS(bitline-12)    -> (bl_card)(11)
            SX(bitline-13)    -> (bl_card)(12)

            PMU1 (Program) -> (program_pulse)B
            PMU2 (Access)   -> (access_pulse)B
            
            BL:1-10
            WL:1-10
            """

        else:
            tmp = """
            Kilobit Setup:
            --------------
            SMU1 (Ground)    -> 1A and 2A
            SMU2 (<Gate>)   -> 1B and 2B
            SMU3 (<Gate>)   -> (wl_card)C
            SMU4 (Read)       -> (bl_card)C
            CS(bitline-12)      -> (bl_card)(11)
            SX(bitline-13)      -> (bl_card)(12)

            PMU1 (Program) -> (program_pulse)D 
            PMU2 (Access)   -> (access_pulse)D

            BL:0-63
            WL:0-31
            """


        #Update label_config
        tmp = tmp.replace('(bl_card)', '%s' % self.model.bl_card)
        tmp = tmp.replace('(wl_card)', '%s' % self.model.wl_card)
        tmp = tmp.replace('(program_pulse)', '%s' % program_pulse)
        tmp = tmp.replace('(access_pulse)', '%s' % access_pulse)
        self.view.label_config.SetLabel(tmp)            


        
    def RefreshHardware(self, message):
        """This method is the handler for "RefreshHardware" messages
        which pubsub will call as messages are sent from the model.
        Basically put any commands in here to reconfig the hardware.
        """
        if self.model.current_pulse == 'Reset':
            self.model.pulsegen.Pulse1 = self.model.reset_pulse
        else:
            self.model.pulsegen.Pulse1 = self.model.set_pulse

        self.model.pulsegen.Pulse2 = self.model.gate_pulse
        self.model.pulsegen.config()

        if self.model.smu_changed:
            self.model.smu.integration_time = self.model.integration_time
            self.model.smu.Vread = self.model.Vread
            self.model.smu.chip_type = self.model.chip_type
            self.model.smu.config()
            self.model.smu_changed = False

        self.model.hardware_changed = False
#        print 'Hardware Refreshed!'
        

    ### Pulse Functions ###

    def UpdateModelPulses(self, event):
        """Updates the model pulse values.
        Activated any time any of the Pulse TextBoxes are changed. 
        """

        for pulsebox, model_pulse in zip([self.view.pulsebox_set, self.view.pulsebox_reset, self.view.pulsebox_gate], \
                            [self.model.set_pulse, self.model.reset_pulse, self.model.gate_pulse]) :



            try:
                Width = pulsebox.textctrl_width.GetValue()
                Leading = pulsebox.textctrl_lead.GetValue()
                Trailing = pulsebox.textctrl_trail.GetValue()
                Delay = pulsebox.textctrl_delay.GetValue()
                Impedance = pulsebox.textctrl_impedance.GetValue()
                High = pulsebox.textctrl_voltage.GetValue()
                # Type =  ['VOLT', 'CURR'][ pulsebox.combo_type.GetValue() == 'Current' ]
                Type =  pulsebox.combo_type.GetValue()

                tmp_dict = dict(WIDTH=Width, LEADING=Leading, \
                    TRAILING=Trailing, DELAY=Delay, IMPEDANCE=Impedance, HIGH=High, TYPE=Type)


                #Change all to floats except TYPE
                for k, v in tmp_dict.items():
                    if k != 'TYPE':
                        model_pulse[k] = float(v)

                model_pulse['TYPE'] = Type
                # print 'view', tmp_dict
                # print 'model', model_pulse


            except ValueError:
                """Don't spit out errors mid-typing"""
                pass

        # print self.model.set_pulse
        # print self.model.reset_pulse
        # print self.model.gate_pulse

        self.model.hardware_changed = True



    def Finished(self, message):
        """Kill the active thread upon receiving "Finished" pub message.
        BUG: Doesn't currently join (Kill) the thread, not a fatal bug, but accumulates...
        """
        self.view.statusbar.SetStatusText('')
#        self.worker.join()
        self.worker = None
        self.model.want_to_abort = False
        
        
    def Abort(self, message):
        """Kill the active thread upon receiving "Abort" pub message.
        BUG: Doesn't currently join (Kill) the thread, not a fatal bug, but accumulates...
        """
        self.view.statusbar.SetStatusText('')
        print self.worker.getName() #Prints Thread Number
#        self.worker.join()
        self.worker = None
        self.model.want_to_abort = False
        
    def OverwriteWarning(self, message):
        """Warn of Overwriting
        """
        name = self.model.full_filename

        dialog = wx.MessageDialog(None, 
            'Warning!! Do you want to overwrite file?\n%s' % name, 
            'Ovewriting File...', 
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
        result = dialog.ShowModal()
        dialog.Destroy()

        if result == wx.ID_OK:
             pass
        


    ### Event Handlers for Controlling Instruments / Collecting Data ###
    ### Program Controls ###

    def run(self, program_name=''):
        #Only one thread at a time
        if not self.worker:
    
            #Only set combobox with valid entries
            if program_name:
                self.model.current_program = program_name
            
            #Change statusbar
            print '\nRunning: %s' % self.model.current_program
            self.view.statusbar.SetStatusText('Running: %s' % self.model.current_program)
            
            #Create and run thread
            self.worker = Model.WorkerThread(self.model, self.user_programs)
            self.worker.start()        


    def on_button_run(self, event):
        self.model.current_program = self.view.combo_program.GetValue()
        self.run()

    def on_button_abort(self, event):
        if self.worker:
            self.view.statusbar.SetStatusText('Aborting...')
            self.model.want_to_abort = True

    def on_button_reload(self, event):
        self.load_user_programs()


    def on_button_set_pulse(self, event):
        if self.model.current_pulse != 'Set':        
            self.model.current_pulse = 'Set'
            self.model.hardware_changed = True    
        self.run('Pulse')

    def on_button_reset_pulse(self, event):
        if self.model.current_pulse != 'Reset':        
            self.model.current_pulse = 'Reset'
            self.model.hardware_changed = True
        self.run('Pulse')

    def on_button_measure(self, event):
        self.run('MeasureR')

    def on_combo_program(self, event):
        self.model.current_program = self.view.combo_program.GetValue()



    ### Non Program Controls ###

    ### Saving Local file 'program_data.npz' with last filename ###
    def get_this_module_path(self):
        encoding = sys.getfilesystemencoding()
        if hasattr(sys, "frozen"):
            return os.path.dirname(unicode(sys.executable, encoding))
        return os.path.dirname(unicode(__file__, encoding))

    def get_scripts_path(self):
        return os.path.join(self.get_this_module_path(), '..', 'scripts')


    def save_program_data(self):
        path = os.path.join(self.get_this_module_path(), 'program_data.npz')
        np.savez(path, 
            filename=self.model.filename, 
            user_programs_filename=self.model.user_programs_filename)


    def load_user_programs(self):
        try:
            # try:
            #     del UserPrograms
            # except:
            #     pass
            UserPrograms = importlib.import_module(self.model.user_programs_filename)

        except:
            self.model.user_programs_filename = 'UserProgramsDefault'
            import UserProgramsDefault as UserPrograms

        # print self.model.user_programs_filename 

        reload(UserPrograms)
        self.user_programs = UserPrograms.UserPrograms(self)
        self.model.current_program = self.user_programs.list[0]
        self.view.statusbar.SetStatusText('Loaded: %s' % self.model.user_programs_filename)
        self.RefreshControls('')        



    ########


    def on_button_filename(self, event):
        file_choices = "TXT (*.txt)|*.txt"
        
        dlg = wx.FileDialog(
            self.view, 
            message="Choose a Filename...",
            defaultDir=os.getcwd(),
            defaultFile=self.model.filename,
            wildcard=file_choices,
            style = wx.SAVE | wx.OVERWRITE_PROMPT)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.model.filename = path
            self.save_program_data()
            self.view.textctrl_filename.SetValue(path)


    def on_button_userprograms(self, event):
        file_choices = "Python (*.py)|*.py"
        
        dlg = wx.FileDialog(
            self.view, 
            message="Choose a User Programs File...",
            defaultDir=self.get_scripts_path(),
            defaultFile=self.model.user_programs_filename,
            wildcard=file_choices,
            style = wx.OPEN )
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            name = os.path.splitext(os.path.basename(path))[0]
            # print path, name
            self.model.user_programs_filename = name
            self.save_program_data()
            self.load_user_programs()

    def on_textctrl_filename(self,event):
        self.model.filename = self.view.textctrl_filename.GetValue()
        self.save_program_data()

    def on_textctrl_run_number(self,event):
        self.model.run_number = self.view.textctrl_run_number.GetValue()

    def on_textctrl_vread(self,event):
        self.model.Vread = float(self.view.textctrl_vread.GetValue())
        self.model.smu_changed = True
        self.model.hardware_changed = True

    def on_button_new_file(self,event):
        self.run('NewFile')

    def on_textctrl_blwl(self,event):
        bl = self.view.textctrl_bl.GetValue()
        wl = self.view.textctrl_wl.GetValue()
        try:
            self.model.bl = int(bl)
            self.model.wl = int(wl)
#            print 'bl:',bl,'wl:',wl
        except ValueError:
            print 'BitLine/Wordline should be an integer [Macro:(1-10), Kilobit:bl(0-63)wl(0-31)]'


    def on_combo_bl_card(self, event):
        bl_card = self.view.combo_bl_card.GetValue()
        if bl_card == '1':
            wl_card = '2'
        elif bl_card == '2':
            wl_card = '1'

        self.model.bl_card = bl_card
        self.model.wl_card = wl_card
        self.RefreshTextSetupInstructions('')


    def on_combo_program_pulse(self, event):
        self.model.pulse_bl_or_wl = self.view.combo_program_pulse.GetValue()
        self.RefreshTextSetupInstructions('')


    def on_combo_chip_type(self, event):
        chip_type = self.view.combo_chip_type.GetValue()
        self.model.chip_type = chip_type
        self.model.hardware_changed = True
        self.RefreshTextSetupInstructions('')


    def on_combo_integration_time(self, event):
        self.model.integration_time = self.view.combo_integration_time.GetValue()
        self.model.smu_changed = True
        self.model.hardware_changed = True
