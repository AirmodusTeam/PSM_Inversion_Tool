# Import the relevant packages
from PSM_inv.GuiImports import *
from PSM_inv.InversionFunctions import *
from PSM_inv.HelperFunctions import *

# current version number displayed in the GUI (Major.Minor.Patch or Breaking.Feature.Fix)
from config import version_number

# define file paths according to run mode (exe or script)
script_path = os.path.realpath(os.path.dirname(__file__)) # location of this file
script_path = script_path.replace('\\', '/') # replace backslashes with forward slashes
# exe (one file)
if getattr(sys, 'frozen', False):
    resource_path = script_path + "/res" # path of /res/ folder (images, icons)
# script
else:
    resource_path = os.path.dirname(script_path) + "/res" # path of /res/ folder (images, icons)

class DateTimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(value)) for value in values]

class TimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [datetime.datetime.fromtimestamp(value) for value in values]

class TimeAxisItemForRaw(pg.AxisItem):
    def __init__(self, posix_timestamps, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.posix_timestamps = posix_timestamps

    def tickStrings(self, values, scale, spacing):
        min_time = np.min(self.posix_timestamps)
        max_time = np.max(self.posix_timestamps)
        ticks = []
        for value in values:
            if min_time <= value <= max_time:
                tick = time.strftime("%H:%M:%S", time.gmtime(value))
            else:
                tick = ""
            ticks.append(tick)
        return ticks

    def tickValues(self, minVal, maxVal, size):
        values = super().tickValues(minVal, maxVal, size)
        # filter out values that are out of range
        values = [(level, [value for value in tick_values if minVal <= value <= maxVal]) for level, tick_values in values]
        return values

class TimeAxisItemForContour(pg.AxisItem):
    def __init__(self,scan_start_time, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scan_start_time = scan_start_time
    def tickStrings(self, values, scale, spacing):
        ticks = []
        for value in values:
            if 0 <= value < len(self.scan_start_time):
                value = self.scan_start_time[int(value)]
                timestamp = (value - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1, 's')
                value = time.strftime("%H:%M:%S", time.gmtime(timestamp))
            else:
                value = ""
            ticks.append(value)
        return ticks

class LogNormalAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        ticks = []
        superscript_map = {
            '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
            '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
            '+': '⁺', '-': '⁻'
        }
        for value in values:
            formatted = "{:.2e}".format(value)
            mantissa, exponent = formatted.split('e')
            exponent = str(int(exponent))
            exponent = ''.join(superscript_map[i] for i in exponent if i in superscript_map)
            mantissa = mantissa.split('.')[0]
            value = f"{mantissa}x10{exponent}"
            ticks.append(value)
        return ticks
        #return ["{:.2e}".format(np.exp(val)) for val in values]

class LogAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        ticks = []
        superscript_map = {
            '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
            '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
            '+': '⁺', '-': '⁻'
        }
        for value in values:
            formatted = "{:.2e}".format(value)
            mantissa, exponent = formatted.split('e')
            mantissa_dec = mantissa.split('.')[1]
            if mantissa_dec == '00':
                value = str(int(value))
                value = ''.join(superscript_map[i] for i in value if i in superscript_map)
                ticks.append("10{}".format(value))
            else:
                ticks.append("")
        return ticks

class ScientificAxisItemOg(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        ticks = []
        for value in values:
            formatted = "{:.2e}".format(value)
            mantissa, exponent = formatted.split('e')
            ticks.append("10^{}".format(int(exponent))) 
        return ticks

class ScientificAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        ticks = []
        for value in values:
            formatted = "{:.2e}".format(value)
            mantissa, exponent = formatted.split('e')
            exponent = str(int(exponent))
            superscript_map = {
                '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
                '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
                '+': '⁺', '-': '⁻'
            }
            if mantissa == '1.00':
                exponent = ''.join(superscript_map[i] for i in exponent if i in superscript_map)
                ticks.append("10{}".format(exponent))
            else:
                ticks.append("")
        return ticks

class ExtraFeatures(QWidget):
    def __init__(self):
        super().__init__()
        # create extra features window layout
        layout = QVBoxLayout()

        # create two scatter plots
        self.scatter1 = pg.plot()
        self.scatter1.setBackground('w')
        self.scatter1.setLabel('left', "Diameter (nm)")
        self.scatter1.setLabel('bottom', "Onset saturated flow rate")
        layout.addWidget(self.scatter1)
        self.scatter2 = pg.plot()
        self.scatter2.setBackground('w')
        self.scatter2.setLabel('left', "PSM efficiency at max. sat. flow rate")
        self.scatter2.setLabel('bottom', "Diameter (nm)")
        layout.addWidget(self.scatter2)

        # create parameters for custom binning
        custom_binning_params_layout = QGridLayout()
        # create custom binning label
        custom_binning_label = QLabel("Custom Binning")
        custom_binning_params_layout.addWidget(custom_binning_label, 0, 0, 1, 2)
        # create calibration fit label
        calibration_fit_label = QLabel("Use calibration fit")
        custom_binning_params_layout.addWidget(calibration_fit_label, 0, 2)
        # create calibration fit checkbox
        self.calibration_fit_checkbox = QCheckBox()
        custom_binning_params_layout.addWidget(self.calibration_fit_checkbox, 0, 3)
        # create inversion button
        self.inversion_btn = QPushButton("Invert and Plot")
        custom_binning_params_layout.addWidget(self.inversion_btn, 0, 4, 1, 2)
        # create min size label
        min_size_label = QLabel("Min. size (nm)")
        custom_binning_params_layout.addWidget(min_size_label, 1, 0)
        # create min size input
        self.min_size_input = QLineEdit()
        self.min_size_input.setFixedWidth(50)
        custom_binning_params_layout.addWidget(self.min_size_input, 1, 1)
        # create max size label
        max_size_label = QLabel("Max. size (nm)")
        custom_binning_params_layout.addWidget(max_size_label, 1, 2)
        # create max size input
        self.max_size_input = QLineEdit()
        self.max_size_input.setFixedWidth(50)
        custom_binning_params_layout.addWidget(self.max_size_input, 1, 3)
        # create double validator for min and max size inputs
        double_validator = QDoubleValidator()
        double_validator.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        double_validator.setNotation(QDoubleValidator.StandardNotation)
        self.min_size_input.setValidator(double_validator)
        self.max_size_input.setValidator(double_validator)
        # create number of bins label
        num_bins_label = QLabel("N. of bins")
        custom_binning_params_layout.addWidget(num_bins_label, 1, 4)
        # create number of bins input
        self.num_bins_input = QLineEdit()
        self.num_bins_input.setFixedWidth(50)
        self.num_bins_input.setValidator(QIntValidator())
        custom_binning_params_layout.addWidget(self.num_bins_input, 1, 5)
        # add custom binning parameters layout to extra features layout
        layout.addLayout(custom_binning_params_layout)

        # set layout
        self.setLayout(layout)

        # set window size
        self.resize(400, 900)

        # create variable for calibration fitting dataframe
        self.calibration_fitting_df = None
    
    def plot_calibration_file(self, main_window):
        # if calibration dataframe exists
        if main_window.calibration_df is not None:

            # reload calibration file
            main_window.reload_calibration()
            # get calibration dataframe from main window
            calibration_df = main_window.calibration_df
            
            # if extra features window is not visible, show it
            if not self.isVisible():
                self.show()
            
            self.scatter1.clear()
            self.scatter2.clear()
            self.scatter1.plot(calibration_df['cal_satflow'], calibration_df['cal_diameter'], pen=None, symbol='o')
            self.scatter2.plot(calibration_df['cal_diameter'], calibration_df['cal_maxdeteff'], pen=None, symbol='o')
            # calculate size calibration fitting curve and add it to scatter1
            size_calibration_x, size_calibration_y = calculate_size_fitting(calibration_df['cal_satflow'], calibration_df['cal_diameter'])
            self.scatter1.plot(size_calibration_x, size_calibration_y, pen='r')
            size_calibration_df = pd.DataFrame({'cal_satflow': size_calibration_x, 'cal_diameter': size_calibration_y})
            # calculate detection efficiency fitting curve and add it to scatter2
            det_eff_x, det_eff_y = calculate_deteff_fitting(calibration_df['cal_diameter'], calibration_df['cal_maxdeteff'], size_calibration_y)
            self.scatter2.plot(det_eff_x, det_eff_y, pen='r')
            det_eff_df = pd.DataFrame({'cal_diameter': det_eff_x, 'cal_maxdeteff': det_eff_y})
            # merge size calibration and detection efficiency dataframes into one dataframe
            self.calibration_fitting_df = pd.merge(size_calibration_df, det_eff_df, on='cal_diameter')
            # reverse order of rows in dataframe
            self.calibration_fitting_df.sort_values(by='cal_diameter', inplace=True, ignore_index=True)
            #print(self.calibration_fitting_df)
        else:
            print("No calibration file loaded")
    
class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()

        self.application = app # store application reference to variable

        self.grey = (46,53,61)
        self.green = (105,255,0)

        # set stylesheet from file
        with open(script_path + "/style.css", "r") as file:
            self.setStyleSheet(file.read())
        # create stylesheet for setting checkbox images
        checkbox_stylesheet = "QCheckBox::indicator::checked { image: url(" + resource_path + "/images/checkbox_checked_fill_transparent.png); } QCheckBox::indicator::unchecked { image: url(" + resource_path + "/images/checkbox_unchecked_fill_transparent.png); }"

        self.setWindowTitle("Airmodus PSM Inversion Tool v. " + version_number)
        # resizing the whole app
        self.resize(1300, 800)

        self.main_widget = QWidget()

        # Main layout
        main_layout = QVBoxLayout()

        # - main_layout/top_layout
        top_layout = QHBoxLayout()
        self.model_label = QLabel("Instrument Model:")
        top_layout.addWidget(self.model_label)
        # Create the logo
        top_layout.addStretch()
        self.logo = QLabel()
        pixmap = QPixmap(resource_path + '/images/airmodus-envea-logo.png')
        self.logo.setPixmap(pixmap)
        top_layout.addWidget(self.logo)
        main_layout.addLayout(top_layout)
        # Scale the picture so it fits in the layout while keeping the aspect ratio
        self.logo.setPixmap(pixmap.scaled(400, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        
        self.graph_layout = QHBoxLayout()

        # this will be set to True the first time invert_and_plot is called
        self.markers_added = False
        self.raw_plot_marker = pg.InfiniteLine(angle=90,movable=True,pen=pg.mkPen(color=(255, 0, 0, 255),width=2))
        self.raw_plot_marker.sigDragged.connect(self.sync_markers)

        # Plots (three plots: raw, mid, size dist)

        # raw plot

        self.raw_gl = pg.GraphicsLayoutWidget()
        self.raw_gl.setBackground('w')

        self.raw_plot = self.raw_gl.addPlot(axisItems={'left': pg.AxisItem(orientation='left'),'bottom': pg.AxisItem(orientation='bottom')})
        self.raw_plot.setLabel('left', "Concentration [#/cm3]")
        self.raw_plot.setLabel('bottom', "Time")
        self.raw_plot.showGrid(x=True, y=True)
        self.raw_plot.setTitle(f"Raw data", size="9pt")

        self.color_bar_plot = pg.PlotItem()
        self.color_bar_plot.hideAxis('bottom')
        self.color_bar_plot.hideAxis('left')

        self.raw_gl.addItem(self.color_bar_plot)
        self.raw_gl.ci.layout.setColumnFixedWidth(1, 60)

        self.graph_layout.addWidget(self.raw_gl, stretch=1)

        # mid plot

        self.mid_gl = pg.GraphicsLayoutWidget()
        self.mid_gl.setBackground('w')

        self.mid_plot_marker = pg.InfiniteLine(angle=90,movable=True,pen=pg.mkPen(color=(255, 0, 0, 255),width=2))
        self.mid_plot_marker.sigDragged.connect(self.sync_markers)
        self.mid_plot_marker.sigPositionChanged.connect(self.update_size_dist_plot)

        self.mid_plot = self.mid_gl.addPlot()
        self.mid_plot.setLabel('left', "Diameter [nm]")
        self.mid_plot.setLabel('bottom', "Time")
        self.mid_plot.showGrid(x=True, y=True)
        #self.mid_plot.setLogMode(y=True)
        self.mid_plot.setTitle(f"Inverted size distribution", size="9pt")
        
        self.mid_color_bar_plot = pg.PlotItem()
        self.mid_color_bar_plot.hideAxis('bottom')
        self.mid_color_bar_plot.hideAxis('left')
        self.mid_gl.addItem(self.mid_color_bar_plot)
        self.mid_gl.ci.layout.setColumnFixedWidth(1, 60)

        self.graph_layout.addWidget(self.mid_gl, stretch=1)

        # size dist plot

        self.size_dist_gl = pg.GraphicsLayoutWidget()
        self.size_dist_gl.setBackground('w')
        self.size_dist_plot = self.size_dist_gl.addPlot(axisItems={'left': LogAxisItem(orientation='left'),'bottom': pg.AxisItem(orientation='bottom')})
        self.size_dist_plot.setLabel('left', "dN/dlogDp [cm-3]")
        self.size_dist_plot.setLabel('bottom', "Diameter [nm]")
        self.size_dist_plot.showGrid(x=True, y=True)
        # change the y and x-axis to log scale
        self.size_dist_plot.setLogMode(x=True, y=True)
        self.size_dist_plot.getAxis('left').enableAutoSIPrefix(enable=False)

        self.graph_layout.addWidget(self.size_dist_gl, stretch=1)

        # Add the graph layout to the main layout.
        main_layout.addLayout(self.graph_layout)

        # create plot settings layout
        plot_settings_layout = QHBoxLayout()
        # create show errors button and add to plot settings layout TODO uncomment when show errors is functional
        #self.show_errors_on_raw_btn = QCheckBox("Show Errors")
        #plot_settings_layout.addWidget(self.show_errors_on_raw_btn, 0, 1)
        # add empty label for alignment TODO replace when show errors is ready
        plot_settings_layout.addWidget(QLabel(""), stretch=1)
        # create layout for middle plot settings
        mid_plot_settings = QHBoxLayout()
        # create average vs. raw combobox and add to mid_plot_settings layout
        self.avg_vs_raw_combobox = QComboBox()
        self.avg_vs_raw_combobox.setMaximumWidth(100)
        self.avg_vs_raw_combobox.addItems(["Raw","Average"])
        self.avg_vs_raw_combobox.setCurrentIndex(0)
        self.avg_vs_raw_combobox.currentIndexChanged.connect(self.update_mid_plot)
        mid_plot_settings.addWidget(self.avg_vs_raw_combobox)
        # create toggle button for day markers and add to mid_plot_settings layout
        self.day_markers_btn = QCheckBox("Day markers")
        self.day_markers_btn.setStyleSheet(checkbox_stylesheet)
        self.day_markers_btn.setChecked(True)
        self.day_markers_btn.clicked.connect(self.toggle_day_markers)
        mid_plot_settings.addWidget(self.day_markers_btn)
        mid_plot_settings.addWidget(QLabel("")) # add empty label for alignment
        # add mid_plot_settings to plot_settings_layout
        plot_settings_layout.addLayout(mid_plot_settings, stretch=1)
        # add empty label for alignment
        plot_settings_layout.addWidget(QLabel(""), stretch=1)
        # add plot settings layout to main layout
        main_layout.addLayout(plot_settings_layout)

        # controls

        controls_layout = QHBoxLayout()

        left_layout = QGridLayout()

        self.load_data_btn = QPushButton("Load data files")
        self.load_data_btn.setFixedWidth(150)
        self.load_data_btn.clicked.connect(self.load_data)
        left_layout.addWidget(self.load_data_btn,0,0)
        self.data_file_label = QLabel("No files selected")
        self.data_file_label.setObjectName("bordered")
        self.data_file_label.setFixedWidth(250)
        self.data_file_label.setAlignment(Qt.AlignRight)
        left_layout.addWidget(self.data_file_label,0,1,1,3)
        self.refresh_file_btn = QPushButton("Refresh files")
        self.refresh_file_btn.setFixedWidth(150)
        self.refresh_file_btn.clicked.connect(self.refresh_files)
        left_layout.addWidget(self.refresh_file_btn,0,4)

        self.load_cal_btn = QPushButton("Load calibration file")
        self.load_cal_btn.setFixedWidth(150)
        self.load_cal_btn.clicked.connect(self.load_calibration)
        left_layout.addWidget(self.load_cal_btn,1,0)
        self.calibration_file_label = QLabel("No file selected")
        self.calibration_file_label.setObjectName("bordered")
        self.calibration_file_label.setFixedWidth(250)
        self.calibration_file_label.setAlignment(Qt.AlignRight)
        left_layout.addWidget(self.calibration_file_label,1,1,1,3)
        self.invert_and_plot_btn = QPushButton("Invert and plot")
        self.invert_and_plot_btn.setFixedWidth(150)
        self.invert_and_plot_btn.clicked.connect(self.invert_and_plot)
        left_layout.addWidget(self.invert_and_plot_btn, 1, 4)

        # adding a space to row 2
        spacer = QSpacerItem(30, 30)
        left_layout.addItem(spacer,2,0)


        data_filtering_label = QLabel("Raw data quality filtering")
        left_layout.addWidget(data_filtering_label,3,0)
        self.data_filtering_btn = QCheckBox()
        self.data_filtering_btn.setStyleSheet(checkbox_stylesheet)
        self.data_filtering_btn.setChecked(True)
        self.data_filtering_btn.stateChanged.connect(self.checkbox_button_state_changed)
        left_layout.addWidget(self.data_filtering_btn,3,1)
        
        remove_error_data_label = QLabel("Remove data with errors")
        left_layout.addWidget(remove_error_data_label,4,0)
        self.remove_error_data_btn = QCheckBox()
        self.remove_error_data_btn.setStyleSheet(checkbox_stylesheet)
        self.remove_error_data_btn.stateChanged.connect(self.remove_errors_clicked)
        left_layout.addWidget(self.remove_error_data_btn,4,1)

        avg_n_label = QLabel("Average number")
        avg_n_label.setToolTip("Number of data points to average over")
        left_layout.addWidget(avg_n_label,5,0)
        self.avg_n_input = QLineEdit("5")
        self.avg_n_input.setFixedWidth(30)
        validator = QIntValidator()
        self.avg_n_input.setValidator(validator)
        left_layout.addWidget(self.avg_n_input,5,1)

        ext_dilution_fac_label = QLabel("External dilution factor")
        left_layout.addWidget(ext_dilution_fac_label,6,0)
        # Allow for float values in the external dilution factor input
        dil_validator = QDoubleValidator()
        # Change locale to English to allow for decimal point
        dil_validator.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        dil_validator.setNotation(QDoubleValidator.StandardNotation)
        dil_validator.setDecimals(2)
        self.ext_dilution_fac_input = QLineEdit("1")
        self.ext_dilution_fac_input.setFixedWidth(30)
        self.ext_dilution_fac_input.setValidator(dil_validator)
        left_layout.addWidget(self.ext_dilution_fac_input,6,1)

        self.inversion_method_label = QLabel("Inversion method")
        left_layout.addWidget(self.inversion_method_label,3,2)
        self.inversion_method_selection = QComboBox()
        self.inversion_method_selection.addItems(["Stepwise"]) # ,"Kernel","EM"
        left_layout.addWidget(self.inversion_method_selection,3,3)

        bin_label = QLabel("Number of bins")
        left_layout.addWidget(bin_label,4,2)
        self.bin_selection = QComboBox()
        left_layout.addWidget(self.bin_selection,4,3)

        bin_limits_label = QLabel("Bin limits")
        left_layout.addWidget(bin_limits_label,5,2)
        # input for bin limits, updated when bin_selection is changed
        self.bin_limits_edit = QLineEdit()
        bin_validator = QRegExpValidator(QRegExp("[0-9. ]+")) # allow numbers, dots and spaces
        self.bin_limits_edit.setValidator(bin_validator)
        self.bin_limits_edit.textEdited.connect(self.bin_limits_edited) # set bin selection to "custom" when edited
        left_layout.addWidget(self.bin_limits_edit,5,3,1,2)
        # connect currentTextChanged signal to show_bin_limits function
        self.bin_selection.currentTextChanged.connect(lambda text: self.show_bin_limits(text))

        CPC_time_lag_label = QLabel("CPC time lag (s)")
        left_layout.addWidget(CPC_time_lag_label,6,2)
        # input for CPC time lag in seconds
        self.CPC_time_lag_input = QLineEdit("3")
        self.CPC_time_lag_input.setFixedWidth(30)
        # add validator with 1 decimal place (10 Hz resolution)
        lag_validator = QDoubleValidator()
        lag_validator.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        lag_validator.setNotation(QDoubleValidator.StandardNotation)
        lag_validator.setDecimals(1)
        lag_validator.setBottom(0)
        self.CPC_time_lag_input.setValidator(lag_validator)
        left_layout.addWidget(self.CPC_time_lag_input,6,3)

        left_layout.setColumnStretch(5, 1) # add stretch to column 5 to push widgets to the left

        controls_layout.addLayout(left_layout)

        middle_layout = QGridLayout()

        # 10 Hz options
        self.load_10hz_files_btn = QPushButton("Load 10 Hz files")
        self.load_10hz_files_btn.setFixedWidth(150)
        self.load_10hz_files_btn.clicked.connect(self.load_10hz_files)
        middle_layout.addWidget(self.load_10hz_files_btn,0,0)
        self.cpc_idn_edit = QLineEdit()
        self.cpc_idn_edit.setPlaceholderText("CPC IDN")
        middle_layout.addWidget(self.cpc_idn_edit,1,0)
        self.dilution_parameters_edit = QLineEdit()
        self.dilution_parameters_edit.setPlaceholderText("amp,cen,sig,slope,intercept")
        middle_layout.addWidget(self.dilution_parameters_edit,2,0)
        self.convert_10hz_btn = QPushButton("Convert to 10 Hz")
        self.convert_10hz_btn.setFixedWidth(150)
        self.convert_10hz_btn.clicked.connect(self.convert_10hz)
        middle_layout.addWidget(self.convert_10hz_btn,3,0)
        middle_layout.setRowStretch(4, 1) # add stretch to row 4 to push widgets to top

        controls_layout.addLayout(middle_layout)
        
        # main_layout/controls_layout/right_layout
        right_layout = QGridLayout()

        self.error_output = QTextEdit()
        self.error_output.setReadOnly(True)
        right_layout.addWidget(self.error_output,0,0,1,3)

        right_left_widget = QWidget()
        right_left_widget.setMaximumWidth(200)
        right_left_layout = QVBoxLayout()
        right_left_widget.setLayout(right_left_layout)
        right_layout.addWidget(right_left_widget,1,0)

        self.save_button = QPushButton("Save data")
        self.save_button.clicked.connect(self.save_inversion_data)
        right_left_layout.addWidget(self.save_button)

        daily_files = QHBoxLayout()
        daily_files_label = QLabel("Create daily files")
        self.daily_files_btn = QCheckBox()
        self.daily_files_btn.setStyleSheet(checkbox_stylesheet)
        daily_files.addWidget(daily_files_label)
        daily_files.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        daily_files.addWidget(self.daily_files_btn)
        right_left_layout.addLayout(daily_files)

        matlab_time = QHBoxLayout()
        matlab_time_label = QLabel("Matlab time format")
        self.matlab_time_btn = QCheckBox()
        self.matlab_time_btn.setStyleSheet(checkbox_stylesheet)
        matlab_time.addWidget(matlab_time_label)
        matlab_time.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        matlab_time.addWidget(self.matlab_time_btn)
        right_left_layout.addLayout(matlab_time)

        right_right_widget = QWidget()
        right_right_widget.setMaximumWidth(200)
        right_right_layout = QVBoxLayout()
        right_right_widget.setLayout(right_right_layout)
        right_layout.addWidget(right_right_widget,1,2)

        # create widgets for NAIS data loading
        self.nais_data_label = QLabel("No NAIS data file selected")
        self.nais_data_label.setObjectName("bordered")
        self.nais_data_label.setAlignment(Qt.AlignRight)
        right_right_layout.addWidget(self.nais_data_label)
        self.nais_data_btn = QPushButton("Load NAIS data")
        self.nais_data_btn.clicked.connect(self.load_nais_data)
        right_right_layout.addWidget(self.nais_data_btn)

        # create plot calibration file button
        self.plot_calibration_file_btn = QPushButton("Plot calibration file")
        right_right_layout.addWidget(self.plot_calibration_file_btn)

        controls_layout.addLayout(right_layout)
        controls_layout.setStretchFactor(left_layout, 1)
        controls_layout.setStretchFactor(right_layout, 1)

        self.bordered_widget = QWidget()
        self.bordered_widget.setObjectName("bordered")
        self.bordered_widget.setLayout(controls_layout)


        # Add the bordered widget(controls_layout) to the main layout.
        main_layout.addWidget(self.bordered_widget)

        # Set the main layout to the main widget.
        self.main_widget.setLayout(main_layout)

        # Set the main widget as the central widget.
        self.setCentralWidget(self.main_widget)

        self.data_df = None
        self.calibration_df = None
        self.cpc_df = None
        self.data_df_backup = None
        self.data_df_copy = None
        self.nais_data = None
        self.current_filenames = None
        self.Ninv = None
        self.Ninv_avg = None
        self.day_markers = []
        self.model = None
        self.max_dp = None
        self.min_dp = None
        self.max_satflow_limit = None
        self.min_satflow_limit = None

        self.extra_features = ExtraFeatures()
        self.extra_features.inversion_btn.clicked.connect(self.custom_inversion)
        # connect "Plot calibration file" to plot_calibration_file function with reference to this window
        self.plot_calibration_file_btn.clicked.connect(lambda: self.extra_features.plot_calibration_file(self))

    
    def custom_inversion(self):
        # get patameters from extra features window
        min_size = float(self.extra_features.min_size_input.text())
        max_size = float(self.extra_features.max_size_input.text())
        num_bins = int(self.extra_features.num_bins_input.text())
        # calculate bin limits
        custom_bin_limits = calculate_bin_limits(min_size, max_size, num_bins)
        # call invert_and_plot with custom bin limits as kwarg
        self.invert_and_plot(bin_limits = custom_bin_limits)
    
    # clear all plots and markers
    def clear_plots(self):
        self.raw_plot.clear()
        self.color_bar_plot.clear()
        self.mid_plot.clear()
        self.mid_color_bar_plot.clear()
        self.size_dist_plot.clear()
        self.markers_added = False

    def plot_raw(self):
        """
        Plots the raw data on the left graph right after getting the data file
        """
        if self.data_df is not None:
            
            # clear all plots and markers
            self.clear_plots()

            # Convert Timestamp objects to POSIX timestamps
            self.posix_timestamps = self.data_df['t'].apply(lambda x: x.timestamp())

            concentration_values = self.data_df['concentration']
            satflow_values = self.data_df['satflow']

            # Create a colormap
            cm = pg.colormap.get('viridis')
            # normalize satflow to range 0,1 for colormap
            norm_satflow = (satflow_values - satflow_values.min()) / (satflow_values.max() - satflow_values.min())
            # round values to 1 decimal to reduce draw time
            norm_satflow = norm_satflow.round(1)
            # create brush color for each normalized satflow level
            norm_satflow_levels = [1, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0]
            colors = cm.map(norm_satflow_levels, 'qcolor')
            brushes = [pg.mkBrush(color) for color in colors]

            # Create ScatterPlotItem
            scatter_plot_item = pg.ScatterPlotItem(symbol='o', pxMode=True, pen=pg.mkPen(color=(255, 255, 255), width=.2))
            # add points one normalized satflow level at a time
            for i in range(len(norm_satflow_levels)):
                # get indices matching current normalized satflow level
                indices = np.where(norm_satflow == norm_satflow_levels[i])[0].tolist()
                # add points with matching indices and brush color
                scatter_plot_item.addPoints(self.posix_timestamps[indices], concentration_values[indices], brush=brushes[i])

            #self.raw_plot.setAxisItems({'bottom': TimeAxisItemForRaw(self.posix_timestamps,orientation='bottom')})
            self.raw_plot.setAxisItems({'bottom': pg.DateAxisItem(utcOffset=0)})
            #self.raw_plot.getAxis('bottom').setStyle(tickTextOffset=-15)
            self.raw_plot.getAxis('bottom').setGrid(0)
            self.raw_plot.getAxis('bottom').enableAutoSIPrefix(False) # disable auto SI prefix
            self.raw_plot.setLabel('bottom','Time')

            self.raw_plot.addItem(scatter_plot_item)
            self.raw_plot.showGrid(x=True, y=True)

            # putting the date in the title
            formatted_date = str(self.data_df['t'][0]).split()[0] 
            year, month, day = formatted_date.split('-')
            # if data is from multiple days, add the last day to the title
            end_date = str(self.data_df['t'].iloc[-1]).split()[0]
            if end_date != formatted_date:
                end_year, end_month, end_day = end_date.split('-')
                formatted_date = f'{day}/{month}/{year} - {end_day}/{end_month}/{end_year}'
            else:
                formatted_date = f'{day}/{month}/{year}'
            # setting the plot titles
            self.raw_plot.setTitle(f"Raw data {formatted_date}", size="9pt")
            self.mid_plot.setTitle(f"Inverted size distribution {formatted_date}", size="9pt")

            # Create color bar plot
            min_satflow = satflow_values.min()
            max_satflow = satflow_values.max()
            axis = pg.AxisItem('right')

            # Map a value x from one range to another
            def map_range(x, in_min, in_max, out_min, out_max):
                return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

            # Calculate the labels for the axis
            ticks = [(map_range(i, 0, 4, 0, 100), f"{min_satflow + (max_satflow - min_satflow) * (i / 4):.2f}") for i in range(5)]


            # Set the labels for the axis
            axis.setTicks([ticks])

            print("ticks:",ticks)
            self.color_bar_plot.setAxisItems({'right': axis})
            self.color_bar_plot.hideAxis('bottom')
            self.color_bar_plot.hideAxis('left')

            # Set the range of the color bar plot to match the color bar
            self.color_bar_plot.setRange(yRange=[0, 100])

            # Create color bar data
            color_bar_data = np.repeat(np.linspace(0, 1, 100).reshape(-1, 1), 10, axis=1).T

            # Create color bar image item
            if cm is not None:
                color_bar = pg.ImageItem(color_bar_data, lut=cm.getLookupTable())
                self.color_bar_plot.addItem(color_bar)

            # weird update hack since it wasn't updating
            width = self.color_bar_plot.width()
            height = self.color_bar_plot.height()
            self.color_bar_plot.resize(width+1, height)
            self.color_bar_plot.resize(width, height)
            self.size_dist_plot.clear()




    def invert_and_plot(self, **kwargs):

        start_time = time.time() # store start time for process time measurement

        self.invert_and_plot_btn.clearFocus()
        # set cursor to loading
        self.application.setOverrideCursor(Qt.WaitCursor)

        try:
            if self.inversion_method_selection.currentText() == "Stepwise":


                """
                Inverts the data and plots data on all three graphs,
                """
                if self.data_df is not None and self.calibration_df is not None:
                    
                    # if keyword argument 'bin_limits' was given, use it
                    if 'bin_limits' in kwargs:
                        bin_limits = kwargs['bin_limits']
                    else:
                        # convert bin limits input text to list of floats
                        bin_limits = self.convert_bin_limits()

                    # Inversion --------------------------------------------------------

                    # use copy of data_df to prevent changes to original data
                    self.data_df_copy = self.data_df.copy()

                    # apply lag correction to concentration column (i.e. shift the concentration values up)
                    time_lag = self.CPC_time_lag_input.text() # get time lag from input
                    self.data_df_copy, time_lag = shift_concentration(self.data_df_copy, time_lag)
                    self.CPC_time_lag_input.setText(time_lag) # update value in input

                    # update the measurement data by running it through inst_calib function
                    self.calibration_df, self.data_df_copy  = self.inst_calib()

                    self.Nbinned, self.n_scans, self.scan_start_time, self.Dplot = self.bin_data(bin_limits)

                    # check scans and remove faulty ones
                    if self.data_filtering_btn.isChecked():
                        self.validate_scans() # modifies: self.Nbinned, self.n_scans, self.scan_start_time, self.scan_start_times_posix

                    Sn = self.avg_n_input.text()
                    if Sn == "":
                        Sn = 5
                    else:
                        Sn = int(Sn)
                    self.avg_n_input.setText(str(Sn))
                    
                    # Averaging over scans
                    self.Nbinned_avg = self.averagedata(Sn)

                    # Invert the data and generate self.Ninv and self.Ninv_avg
                    self.step_inversion()

                    # Convert Timestamp objects to POSIX timestamps
                    self.posix_timestamps = self.data_df_copy['t'].apply(lambda x: x.timestamp())

                    # Update mid plot
                    self.update_mid_plot()

                else:
                    if self.data_df is None and self.calibration_df is None:
                        self.error_output.append("No data to plot")
                    elif self.calibration_df is None:
                        self.error_output.append("No calibration file selected")
                    else:
                        self.error_output.append("No data file selected")
            else:
                self.error_output.append("Choose inversion method first")

            # restore cursor to normal
            self.application.restoreOverrideCursor()
        
        except Exception as e:
            traceback.print_exc()
            self.error_output.append("Error inverting data:")
            self.error_output.append(str(e))
            self.application.restoreOverrideCursor() # restore cursor to normal
        
        # print processing time in seconds
        processing_time = time.time() - start_time
        print(f"Processing time: {processing_time:.2f} seconds")
    
    def read_file(self):
        # determine device model by checking if "YYYY.MM.DD hh:mm:ss" is in file header
        with open(self.temp_data_file.name, 'r') as file:
            # check if "YYYY.MM.DD hh:mm:ss" is in the first line of the file
            if "YYYY.MM.DD hh:mm:ss" in file.readline(): # PSM 2.0 / Retrofit
                print("2.0 / Retrofit")
                # set model if not set (1st file)
                if self.model is None:
                    self.model = 'PSM2.0'
                    self.model_label.setText(f"Instrument Model: {self.model}")
                # if model doesn't match current file, raise error
                elif self.model != 'PSM2.0':
                    raise Exception("Mixed data files: PSM 2.0 and A10")
            else: # A10
                print("A10")
                # set model if not set (1st file)
                if self.model is None:
                    self.model = 'A10'
                    self.model_label.setText(f"Instrument Model: {self.model}")
                # if model doesn't match current file, raise error
                elif self.model != 'A10':
                    raise Exception("Mixed data files: PSM 2.0 and A10")

        # Read the temporary file into a DataFrame and rename relevant columns
        if self.model == 'PSM2.0':
            # include header if device is PSM 2.0
            current_data_df = pd.read_csv(self.temp_data_file.name, delimiter=',', header=0) # skiprows=1, header=None)
            # rename columns by old names
            current_data_df.rename(columns={"Concentration from PSM (1/cm3)": "concentration", "Saturator flow rate (lpm)": "satflow", "Dilution correction factor": "dilution", "CPC system status errors (hex)": "CPC_system_status_error", "PSM system status errors (hex)": "PSM_system_status_error"}, inplace=True)
            # convert time column data to datetime, PSM2.0 format: YYYY.MM.DD hh:mm:ss
            try:
                current_data_df['t'] = pd.to_datetime(current_data_df.iloc[:, 0], format='%Y.%m.%d %H:%M:%S')
            except: # exception for 10 Hz data
                current_data_df['t'] = pd.to_datetime(current_data_df.iloc[:, 0], format='%Y.%m.%d %H:%M:%S.%f')
        elif self.model == 'A10':
            # skip header if device is A10
            current_data_df = pd.read_csv(self.temp_data_file.name, delimiter=',', skiprows=1, header=None)
            # rename columns by index
            current_data_df.rename(columns={1: 'concentration', 3: 'satflow', 17: 'dilution', 44: 'CPC_system_status_error', 46: 'PSM_system_status_error'}, inplace=True)
            # convert time column data to datetime, A10 format: DD.MM.YYYY hh:mm:ss
            current_data_df['t'] = pd.to_datetime(current_data_df.iloc[:, 0], format='%d.%m.%Y %H:%M:%S')

        # concatenate dataframe to self.data_df
        self.data_df = pd.concat([self.data_df, current_data_df], ignore_index=True)

    # refreshes data by reloading current files
    def refresh_files(self):
        if self.current_filenames is not None:
            self.load_data(current_filenames=self.current_filenames)
        else:
            self.error_output.setText("No files selected.")
                  
    def load_data(self, **kwargs):

        self.load_data_btn.clearFocus()
        # if keyword argument 'current_filenames' was given, use it
        if 'current_filenames' in kwargs:
            file_names = kwargs['current_filenames']
        # if no keyword argument was given, open file dialog
        else:
            options = QFileDialog.Option.ReadOnly
            file_names, _ = QFileDialog.getOpenFileNames(self, "Load data files", "", "PSM data files (*PSM*.dat);;All data files (*.dat);;All files (*)", options=options)
            file_names.sort() # sort file names alphabetically
        if file_names:
            # set cursor to loading
            self.application.setOverrideCursor(Qt.WaitCursor)
            try:
                self.error_output.clear() # clear error output text box
                self.cpc_idn_edit.clear() # clear CPC IDN input
                self.dilution_parameters_edit.clear() # clear dilution parameters input
                self.current_filenames = file_names # store file names to variable

                # set data file label information
                if len(file_names) == 1:
                    self.data_file_label.setText(file_names[0])
                    self.data_file_label.setToolTip(file_names[0])
                else:
                    self.data_file_label.setText(f"{len(file_names)} files loaded, hover to see names")
                    self.data_file_label.setToolTip("\n".join(file_names))
                
                previous_model = self.model # store previous model for comparison before resetting
                
                self.data_df = pd.DataFrame() # reset data_df
                self.data_df_backup = None # reset data_df_backup
                self.cpc_df = None # reset cpc_df
                self.model = None # reset device model variable
                self.Ninv = None # reset inversion dataframe
                self.Ninv_avg = None # reset inversion average dataframe
                # read each file and append to dataframe
                for file_name in file_names:
                    try:
                        # Create a temporary file and copy the contents of current file
                        self.temp_data_file = tempfile.NamedTemporaryFile(delete=False)
                        shutil.copy(file_name, self.temp_data_file.name)
                        # read file contents and concatenate to data_df dataframe
                        self.read_file()
                    except Exception as e:
                        # print filename and error message to error output
                        self.error_output.append(f"Error reading file {file_name.split('/')[-1]}:\n{str(e)}")
                
                self.data_df = clean_data(self.data_df) # remove inf and nan values from data
                self.display_errors(self.data_df) # display PSM and CPC errors
                self.remove_data_with_errors() # remove errors if button is checked
                self.plot_raw() # plot raw data
                if self.model != previous_model: # if model has changed, update bin selection
                    self.update_bin_selection() # update bin selection options according to model and min/max Dp

                # restore cursor to normal
                self.application.restoreOverrideCursor()
            
            except Exception as e:
                traceback.print_exc()
                self.error_output.append("Error loading data files:")
                self.error_output.append(str(e))
                self.clear_plots() # clear plots if error occurs
                self.application.restoreOverrideCursor() # restore cursor to normal

            # Replace zero or negative values with a small positive number
            #self.data_df['concentration'] = self.data_df['concentration'].apply(lambda x: 1e-6 if x <= 0 else x)

            # Assuming df is your DataFrame and 'column_name' is the name of the column with the outliers
            #Q1 = self.data_df['concentration'].quantile(0.25)
            #Q3 = self.data_df['concentration'].quantile(0.75)
            #IQR = Q3 - Q1
            # only keep rows in the dataframe that do not have outliers 
            #self.data_df = self.data_df[~((self.data_df['concentration'] < (Q1 - 1.5 * IQR)) |(self.data_df['concentration'] > (Q3 + 1.5 * IQR)))]

            #print("min:",self.data_df['concentration'].min())
            #print("max:",self.data_df['concentration'].max())

    # load new calibration file via file dialog
    def load_calibration(self):
        self.load_cal_btn.clearFocus()
        file_name, _ = QFileDialog.getOpenFileName(self, "Load calibration file", "", "Text files (*.txt);;All files (*)")
        self.cal_file_name = file_name
        self.read_calibration(file_name, new_file=True)

    # reload existing calibration file
    def reload_calibration(self):
        file_name = self.cal_file_name
        self.read_calibration(file_name)
    
    # read calibration file into calibration_df
    def read_calibration(self, file_name, new_file=False):
        if file_name:
            try:
                self.calibration_df = pd.read_csv(file_name, delimiter='\t', header=None)
                self.calibration_df.columns = ['cal_satflow'] + self.calibration_df.columns[1:].tolist()
                self.calibration_df.columns = [self.calibration_df.columns[0], 'cal_diameter'] + self.calibration_df.columns[2:].tolist()
                self.calibration_df.columns = self.calibration_df.columns[:2].tolist() + ['cal_maxdeteff'] + self.calibration_df.columns[3:].tolist()
                # store max dp and min dp values to variables
                self.max_dp = self.calibration_df['cal_diameter'].iloc[-1]
                self.min_dp = self.calibration_df['cal_diameter'].iloc[0]
                # store max satflow limit and min satflow limit values to variables
                self.max_satflow_limit = self.calibration_df['cal_satflow'].iloc[0]
                self.min_satflow_limit = self.calibration_df['cal_satflow'].iloc[-1]
                print(f"max_dp: {self.max_dp}, min_dp: {self.min_dp}, max_satflow_limit: {self.max_satflow_limit}, min_satflow_limit: {self.min_satflow_limit}")
                self.calibration_file_label.setText(file_name)
                self.calibration_file_label.setToolTip(file_name)
                if new_file: # if new file was loaded (no reload)
                    self.update_bin_selection() # update bin selection options according to model and min/max Dp
            except:
                self.error_output.append("Error: Calibration file could not be read.")

    def load_10hz_files(self):
        self.load_10hz_files_btn.clearFocus()
        # check if data files have been loaded
        if self.current_filenames is None:
            self.error_output.append("Load data files before loading 10 Hz files.")
            return
        if self.cpc_idn_edit.text() == "":
            print("looking for CPC IDN...")
            cpc_idn_options = [] # list of found CPC IDN options
            for file_name in self.current_filenames:
                par_filename = file_name[:-4] + ".par"
                print("checking for file:", par_filename)
                try:
                    par_df = pd.read_csv(par_filename, delimiter=',', header=0)
                    if 'CPC IDN' in par_df.columns:
                        # find all unique CPC IDN values in the column and add to options list
                        unique_cpc_idns = par_df['CPC IDN'].dropna().unique()
                        for cpc_idn in unique_cpc_idns:
                            if cpc_idn not in cpc_idn_options:
                                cpc_idn_options.append(str(cpc_idn))
                except:
                    print("could not read file:", par_filename)
            if len(cpc_idn_options) == 0:
                print("CPC IDN not found.")
                self.error_output.append("CPC IDN not found, enter manually.")
            else:
                print("found CPC IDN values:", cpc_idn_options)
        if self.dilution_parameters_edit.text() == "":
            print("looking for dilution parameters...")
            for file_name in self.current_filenames:
                par_filename = file_name[:-4] + ".par"
                print("checking for file:", par_filename)
                try:
                    par_df = pd.read_csv(par_filename, delimiter=',', header=0)
                    if all(param in par_df.columns for param in ['amp', 'cen', 'sig', 'slope', 'intercept']):
                        amp = par_df['amp'].dropna().iloc[0]
                        cen = par_df['cen'].dropna().iloc[0]
                        sig = par_df['sig'].dropna().iloc[0]
                        slope = par_df['slope'].dropna().iloc[0]
                        intercept = par_df['intercept'].dropna().iloc[0]
                        dilution_params = f"{amp},{cen},{sig},{slope},{intercept}"
                        print("found dilution parameters:", dilution_params)
                        self.dilution_parameters_edit.setText(dilution_params)
                        break
                except:
                    print("could not read file:", par_filename)
            if self.dilution_parameters_edit.text() == "":
                print("Dilution parameters not found.")
                self.error_output.append("Dilution parameters not found, enter manually.")

        # if CPC IDN has been entered, use that value only
        if self.cpc_idn_edit.text() != "":
            cpc_idn_options = [self.cpc_idn_edit.text()]
        # if no entered value and no options found, return
        elif len(cpc_idn_options) == 0:
            print("No CPC IDN, cannot look for 10 Hz files.")
            return

        print("looking for 10 Hz files...")
        folder_path = os.path.dirname(self.current_filenames[0])
        folder_path = folder_path.replace('\\', '/') + '/'
        print("folder path:", folder_path)
        folder_path = glob.escape(folder_path) # escape special characters ('[') for glob search below
        for cpc_idn in cpc_idn_options:
            print("using CPC IDN:", cpc_idn)
            cpc_files = [] # list to store found cpc files
            for file_name in self.current_filenames:
                try:
                    file_name = file_name.replace('\\', '/')
                    file_timestamp = file_name.split('/')[-1][:15] # first 15 characters (YYYYMMDD_HHMMSS)
                    try:
                        cpc_file = glob.glob(folder_path + '*' + file_timestamp + '*' + cpc_idn + '*_10hz*' + '*.csv')[0]
                    except:
                        file_timestamp_date = file_timestamp[:8]
                        cpc_file = glob.glob(folder_path + '*' + file_timestamp_date + '*' + cpc_idn + '*_10hz*' + '*.csv')[0]
                    cpc_file = cpc_file.replace('\\', '/')
                    cpc_files.append(cpc_file)
                    print("matching CPC 10 Hz file:", cpc_file)
                except:
                    print("file matching failed for data file:", file_name)
            if len(cpc_files) > 0:
                self.cpc_idn_edit.setText(cpc_idn)
                break # exit loop if matching files were found

        if len(cpc_files) == 0:
            print("No matching 10 Hz CPC files found.")
            self.error_output.append("No matching 10 Hz CPC files found.")
            return # TODO let user choose folder to look for 10 Hz files
        else:
            print(f"Found {len(cpc_files)} matching CPC 10 Hz files.")
            self.error_output.append(f"Found {len(cpc_files)} matching CPC 10 Hz files.")

        self.cpc_df = pd.DataFrame() # reset cpc dataframe
        # read cpc files into single dataframe
        for cpc_file in cpc_files:
            try:
                current_cpc_df = pd.read_csv(cpc_file, delimiter=',', header=0)
                # convert time column to datetime
                current_cpc_df['t'] = pd.to_datetime(current_cpc_df.iloc[:, 0], format='%Y.%m.%d %H:%M:%S')
                self.cpc_df = pd.concat([self.cpc_df, current_cpc_df], ignore_index=True)
            except Exception as e:
                print("Error reading CPC file:", cpc_file)
                self.error_output.append(f"Error reading CPC file {cpc_file.split('/')[-1]}:\n{str(e)}")

    def convert_10hz(self):

        self.convert_10hz_btn.clearFocus()

        # check if data and cpc data have been loaded
        if self.data_df is None or self.cpc_df is None:
            self.error_output.append("Load both PSM data and CPC 10 Hz data before converting to 10 Hz.")
            return

        # check if PSM data has valid scan status values (1 or 3)
        if 'Scan status' not in self.data_df.columns or not any(status in self.data_df['Scan status'].values for status in [1,3]):
            self.error_output.append("PSM data does not have valid scan status values for 10 Hz conversion.")
            return
        
        # set cursor to loading
        self.application.setOverrideCursor(Qt.WaitCursor)

        try:
            # get dilution parameters from input
            dilution_parameters = self.dilution_parameters_edit.text().split(',')
            alpha, mu, sigma, slope, intercept = [float(param) for param in dilution_parameters]

            # remove duplicate timestamps
            # # TODO fix duplicate timestamps instead of dropping them
            self.data_df = self.data_df.drop_duplicates(subset=['t'], keep='last')
            self.cpc_df = self.cpc_df.drop_duplicates(subset=['t'], keep='last')
            # reset index
            self.data_df = self.data_df.reset_index(drop=True)
            self.cpc_df = self.cpc_df.reset_index(drop=True)

            # expand dataframes to 10 Hz
            expanded_psm_df = expand_psm_data(self.data_df)
            expanded_cpc_df = expand_cpc_data(self.cpc_df)

            # prints for comparison / debugging
            # print(self.data_df)
            # print(expanded_psm_df)
            # print(self.cpc_df)
            # print(expanded_cpc_df)
            
            # merge expanded dataframes on timestamp
            merged_df = pd.merge(expanded_psm_df, expanded_cpc_df, on='t')
            # print(merged_df)

            # correct concentration values
            corrected_df = correct_concentration(merged_df, alpha, mu, sigma, slope, intercept, shift=0)
            # print(corrected_df)

            # replace self.data_df with corrected_df
            self.data_df = corrected_df
            print(self.data_df)

            # plot raw data again
            self.plot_raw()

            # restore cursor to normal
            self.application.restoreOverrideCursor()
        
        except Exception as e:
            traceback.print_exc()
            self.error_output.append("Error converting to 10 Hz:")
            self.error_output.append(str(e))
            self.application.restoreOverrideCursor() # restore cursor to normal
    
    def update_size_dist_plot_title(self):
        """
        Update the title of the size_dist_plot to show the scan start time.
        Used when the marker is moved.
        """
        sender = self.sender()
        if sender == self.mid_plot_marker:
            cur_pos_stamp = self.mid_plot_marker.getXPos()
            current_scan = int(cur_pos_stamp)
        else: # sender == self.raw_plot_marker:
            cur_pos_stamp = self.raw_plot_marker.getXPos()
            diff = np.abs(self.scan_start_times_posix - cur_pos_stamp)
            current_scan = np.argmin(diff)
            if current_scan > self.n_scans[-1]:
                current_scan -= 1


        scan_start_time = self.scan_start_time[current_scan]
        raw_time = np.datetime_as_string(scan_start_time, unit='s')
        # raw_time = 2023-05-09T00:00:11
        _date,_time = raw_time.split('T')
        _year,_month,_day = _date.split('-')
        _hour,_minute,_second = _time.split(':')
        formatted_time = f"{_day}/{_month}/{_year} {_hour}:{_minute}:{_second}"
        self.size_dist_plot.setTitle(f"Scan start time: {formatted_time}", size="9pt")

        # if nais data has been loaded, convert scan_start_time to datetime object and send to update_nais()
        if self.nais_data is not None:
            converted_start_time = pd.to_datetime(scan_start_time, format='%d-%b-%Y %H:%M:%S')
            self.update_nais(converted_start_time)

    def update_nais(self, start_time):
        #print("PSM scan start time:", start_time)
        # find timestamp index in nais_data closest to start_time
        closest_nais_index = (self.nais_data['begin_time'] - start_time).abs().argsort()[0]
        nais_time_stamp = self.nais_data['begin_time'][closest_nais_index]
        #print("Closest NAIS begin time:", nais_time_stamp)
        # get x values (diameters) as list from nais_data header and convert to float nanometers
        x_list = self.nais_data.columns.values.tolist()[4:]
        x_list = [float(i)*10e8 for i in x_list]
        #print("x (Diameter)\n", x_list)
        # get y values (dN/dlogDp) as list from closest_nais_index row
        y_list = self.nais_data.iloc[closest_nais_index, 4:].values.tolist()
        #print("y (dN/dlogDp)\n", y_list)
        # plot to size_dist_plot
        self.size_dist_plot.plot(x_list, y_list, pen=pg.mkPen(color=(60, 120, 200),width=2), symbol=None, name=f'NAIS {nais_time_stamp}')

    def load_nais_data(self):
        options = QFileDialog.Option.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "Load NAIS data file", "", "Text files (*.txt);;All files (*)", options=options)
        if file_name:
            try:
                # read NAIS file into dataframe
                self.nais_data = pd.read_csv(file_name, delimiter='\t')
                # convert dataframe's begin_time column values from string to datetime
                self.nais_data['begin_time'] = pd.to_datetime(self.nais_data['begin_time'], format='%d-%b-%Y %H:%M:%S')
                self.nais_data_label.setText(file_name)
                print("NAIS data loaded successfully")
                print(self.nais_data)
                try:
                    self.update_size_dist_plot_title()
                except:
                    print("Error updating plot title")
            except:
                print("Error loading NAIS data file")

    def display_errors(self, df):
        PSM_errors, CPC_errors = self.check_instrument_errors(df)
        if PSM_errors:
            self.error_output.append("PSM errors:")
            for error in PSM_errors:
                self.error_output.append(error)
            self.error_output.append("")
        else:
            self.error_output.append("No PSM errors.\n")
        if CPC_errors:
            self.error_output.append("CPC errors:")
            for error in CPC_errors:
                self.error_output.append(error)
            self.error_output.append("")
        else:
            self.error_output.append("No CPC errors.\n")

    def averagedata(self,Sn):
        # Averaging over scans

        skip = 7 # skip 7 metadata columns: lower, upper, bins, UpperDp, LowerDp, dlogDp, MaxDeteff

        try:
            # if Sn > 1 make a running average of dN and make a new dataframe called Nbinned_avg
            if Sn > 1:
                self.Nbinned_avg = self.Nbinned.iloc[:,0:skip]
                temp = self.Nbinned.iloc[:,skip:]
                temp = temp.T.rolling(Sn, min_periods=1).mean().T
                temp['bins'] = self.Nbinned['bins']
                self.Nbinned_avg = self.Nbinned_avg.merge(temp, how = 'left',on='bins')
                #self.error_output.append("Averaging over " + str(Sn) + " scans")
            else:
                messageStatus = 1
                message = "Can't average over one scan, please increase the number of scans to be averaged."
                self.error_output.append(message)
            return self.Nbinned_avg
        
        except:
            messageStatus = 1
            message = "Unexpected error arose during scan averaging"
            self.error_output.append(message)

    def update_mid_plot(self):

        if self.Ninv is None:
            return # if no inversion data, do nothing

        self.mid_plot.clear()

        # Creates the middle contour plot  
        x = self.scan_start_time
        #x = (x - np.datetime64('1970-01-01T00:00:00'))
        # adding bottom axis to the plot
        self.mid_plot.setAxisItems({'bottom': TimeAxisItemForContour(x,orientation='bottom')})
        self.mid_plot.setLabel('bottom','Time')
        self.mid_plot.setLabel('left', "Diameter [nm]")
        # Set the y range to the min and max of the diameter from the bin lims
        self.mid_plot.setYRange(np.min(self.Dplot),np.max(self.Dplot))

        # create ticks for left axis
        bin_ticks = []
        for i in range(len(self.Dplot)):
            # add tick as tuple (value, string)
            bin_ticks.append((len(self.Dplot) - (i + 1), str(round(self.Dplot[i], 2))))
        print("bin_ticks", bin_ticks)
        # set left axis ticks
        # https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/axisitem.html#pyqtgraph.AxisItem.setTicks
        self.mid_plot.getAxis('left').setTicks([bin_ticks])

        # add raw plot marker if not yet added
        if not self.markers_added:
            # add raw plot marker on top of data
            self.raw_plot.addItem(self.raw_plot_marker)
            self.raw_plot_marker.setBounds((self.posix_timestamps.iloc[0], self.posix_timestamps.iloc[-1]))
            self.markers_added = True

        # Convert numpy.datetime64 array to a POSIX timestamp array
        skip = 6 # skip 6 metadata columns: bins, LowerDp, UpperDp, dlogDp, MaxDeteff, binCenter
        y = self.Dplot
        print("y", y)     
        if self.avg_vs_raw_combobox.currentText() == 'Raw':
            z = np.log10(self.Ninv.iloc[:, skip:].values)
        else: # Averaged
            z = np.log10(self.Ninv_avg.iloc[:, skip:].values)
        # flip the y axis
        z = np.flip(z)
        # flip the x axis
        for i in range(len(z)):
            z[i] = np.flip(z[i])

        # # temporarily replace nan and inf values with zero for min/max calculation
        # z_no_nan = np.nan_to_num(z, nan=0.0, posinf=0.0, neginf=0.0)
        # min_z = np.min(z_no_nan)
        # max_z = np.max(z_no_nan)

        # replace nan and inf values with zero
        z = np.nan_to_num(z, nan=0.0, posinf=0.0, neginf=0.0)
        # set floor value: change all values below 0.1 to 0.1
        z[z < 0.1] = 0.1
        min_z = np.min(z)
        max_z = np.max(z)
        
        # round the max value to the next power of ten
        max_z = np.ceil(max_z)
        min_z = np.floor(min_z)

        # Scale back to correct concentration
        z_normalized = (z-min_z)/(max_z - min_z)

        # Create the color map
        cmap = pg.colormap.get('CET-R4')

        # # Set the position of the image
        # # TODO: All of this is a mess, but this is the place to adjust the scales.
        # # HOW ABOUT LOG STUFF? Is the bins even correc? Most likely not
        # tr = QTransform()  # prepare ImageItem transformation:
        # # Get the number of bins and assing it to nbin
        # nbin = len(self.Dplot)-1
        # max_size = np.nanmax(y)
        # min_size = np.nanmin(y)
        # print(min_size, max_size)  
        # len_range = max_size-min_size
        # pixel_size = len_range/nbin

        # tr.scale(1, len_range/nbin)       # scale horizontal and vertical axes
        # tr.translate(0, min_size/pixel_size) # move 3x3 image to locate center at axis origin

        self.image_item = pg.ImageItem(image=z_normalized.T)
        #self.image_item.setTransform(tr)
        self.mid_plot.addItem(self.image_item)
        #self.mid_plot.setYRange(np.min(y),np.max(y))
        # Set range for the colormap
        self.image_item.setLevels([0, 1])

        if cmap is not None:
            self.image_item.setLookupTable(cmap.getLookupTable(0.0, 1.0, 256))

        # Generate new x and y arrays with the correct scaling
        x = pd.date_range(start=x[0], end=x[-1], periods=z_normalized.shape[1])
        y = np.linspace(y[0], y[-1], z_normalized.shape[0])

        # Set the position of the image
        #self.image_item.setPos(0,np.min(y))

        # autoscale mid_plot
        self.mid_plot.enableAutoRange(axis='y', enable=True)

        # NEW
        #-------------------------------------------------------------------

        # Create color bar plot
        axis = pg.AxisItem('right')
        # Map a value x from one range to another
        def map_range(x, in_min, in_max, out_min, out_max):
            return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

        # Calculate the labels for the axis
        #ticks = [(map_range(i, 0, 4, 0, 100), f"{min_z+ (max_z - min_z) * (i / 4):.2f}") for i in range(5)]
        n_ticks = int(max_z-min_z)
        ticks = [(map_range(i, 0, n_ticks, 0, 100), f"{10**(min_z+ (max_z - min_z) * (i / n_ticks)):.0e}") for i in range(n_ticks+1)]

        # Set the labels for the axis
        axis.setTicks([ticks])

        self.mid_color_bar_plot.setAxisItems({'right':axis})
        # Set the range of the color bar plot to match the color bar
        self.mid_color_bar_plot.setRange(yRange=[0, 100])
        
        # Create color bar data
        color_bar_data = np.repeat(np.linspace(0, 1, 100).reshape(-1, 1), 10, axis=1).T

        # change the label offset
        #self.mid_color_bar_plot.getAxis('right').setStyle(tickTextOffset=-15)

        # Create color bar image item
        if cmap is not None:
            color_bar = pg.ImageItem(color_bar_data, lut=cmap.getLookupTable())
            self.mid_color_bar_plot.addItem(color_bar)

        # Add label to the color bar plot
        # self.mid_color_bar_plot.setLabel('left', "dN/dlogDp [cm-3]")

        # Update the plots in order to show the changes in the dilution factor in the single scan plot
        self.update_size_dist_plot()

        # add day markers to plot if data is from multiple days
        # find unique days in scan_start_time
        unique_days = np.unique(self.scan_start_time.astype('datetime64[D]'))
        self.day_markers = [] # reset day markers list
        if len(unique_days) > 1:
            for day in unique_days:
                # get first index of day
                day_index = np.where(self.scan_start_time.astype('datetime64[D]') == day)[0][0]
                # create label for marker
                month, day = str(day).split('-')[1:]
                day_label = f"{day}/{month}"
                # create day marker
                day_marker = pg.InfiniteLine(pos=day_index, angle=90, movable=False, pen=pg.mkPen(color=(255, 255, 255, 255), width=1), label=day_label, labelOpts={'position': 0.85, 'anchors': [(0.5, 0.2), (0.5, 0.2)], 'color': (255, 255, 255, 255), 'rotateAxis': (1, 0)})
                self.mid_plot.addItem(day_marker) # add to plot
                self.day_markers.append(day_marker) # add to list
            # show / hide day markers based on user setting
            self.toggle_day_markers()
            
        # add mid plot marker on top of data
        self.mid_plot.addItem(self.mid_plot_marker)
        self.mid_plot_marker.setBounds((0, len(x)-1))
        self.mid_plot_marker.setPos(0)
        self.sync_markers(self.mid_plot_marker)
    
    def update_size_dist_plot(self):
        """
        Update the size_dist_plot to show the selected scan.
        Used when the marker is moved.
        """
        sender = self.sender()
        if sender == self.mid_plot_marker:
            cur_pos_stamp = self.mid_plot_marker.getXPos()
            current_scan = int(cur_pos_stamp)
        else: # sender == self.raw_plot_marker:
            cur_pos_stamp = self.raw_plot_marker.getXPos()
            diff = np.abs(self.scan_start_times_posix - cur_pos_stamp)
            current_scan = np.argmin(diff)
            if current_scan > self.n_scans[-1]:
                current_scan -= 1

        # Clear the plot
        self.size_dist_plot.clear()

        # Plot only the selected dN
        x_values = self.Ninv['binCenter'].values
        y_values = self.Ninv[f'dN{current_scan}'].values
        x2_values = self.Ninv_avg['binCenter'].values
        y2_values = self.Ninv_avg[f'dN{current_scan}'].values
        self.size_dist_plot.addLegend(offset=(0, 1),labelTextSize='9pt')
        self.size_dist_plot.plot(x_values, y_values, pen=pg.mkPen(color=(126, 122, 122),style=Qt.DashLine,width=2),symbol=None, name="Single scan")
        self.size_dist_plot.plot(x2_values, y2_values, pen=pg.mkPen(color=(118, 209, 58),width=2), symbol=None, name=f'Average over {self.avg_n_input.text()} scans')

        # update plot title to show current scan start time
        self.update_size_dist_plot_title()

    # when button is clicked, reload data to apply changes
    def remove_errors_clicked(self):
        if self.data_df is not None:
            # reset inversion dataframes, remove or restore data with errors, and re-plot raw data
            self.Ninv = None
            self.Ninv_avg = None
            self.remove_data_with_errors()
            self.plot_raw()

    # Remove data with errors if button is checked
    def remove_data_with_errors(self):
        # if Remove Data with Errors button is checked, drop rows where errors are present
        if self.remove_error_data_btn.isChecked():
            if self.data_df is not None:
                # make a copy of data_df as backup
                self.data_df_backup = self.data_df.copy()
                # remove rows with PSM errors
                self.data_df = self.data_df[self.data_df['PSM_system_status_error'] == '0000000000000000']
                # remove rows with CPC errors
                self.data_df = self.data_df[self.data_df['CPC_system_status_error'] == '0000000000000000']
                # reset dataframe index
                self.data_df.reset_index(drop=True, inplace=True)
        else: # if button is unchecked, restore data from backup
            if self.data_df_backup is not None:
                self.data_df = self.data_df_backup.copy()
                self.data_df_backup = None

    def check_instrument_errors(self, df):

        # convert PSM system status hex to row of binary and handle missing values
        df['PSM_system_status_error'] = df['PSM_system_status_error'].fillna('0x00000000')
        unique_psm_hex = df['PSM_system_status_error'].unique()
        psm_hex_to_bin = {h: bin(int(str(h), 16))[2:].zfill(16) for h in unique_psm_hex}
        df['PSM_system_status_error'] = df['PSM_system_status_error'].map(psm_hex_to_bin)

        # convert CPC system status hex to row of binary and handle missing values
        df['CPC_system_status_error'] = df['CPC_system_status_error'].fillna('0x0000')
        unique_cpc_hex = df['CPC_system_status_error'].unique()
        cpc_hex_to_bin = {h: bin(int(str(h), 16))[2:].zfill(16) for h in unique_cpc_hex}
        df['CPC_system_status_error'] = df['CPC_system_status_error'].map(cpc_hex_to_bin)

        # PSM bits correspond to errors:
        # 0 CODES_STATUS_GROWTH_TUBE_TEMP
        # 1 CODES_STATUS_SATURATOR_TEMP
        # 2 CODES_STATUS_SATURATOR_FLOW
        # 3 CODES_STATUS_PREHEATER_TEMP
        # 4 CODES_STATUS_INLET_TEMP
        # 5 CODES_STATUS_MIX1_PRESS
        # 6 CODES_STATUS_MIX2_PRESS
        # 7 CODES_STATUS_ABS_PRESS
        # 8 CODES_STATUS_EXCESS_FLOW
        # 9 CODES_STATUS_DRAIN_LEVEL
        # 10 CODES_STATUS_AMBIENT_TEMP
        # 11 CODES_STATUS_DRAIN_TEMP
        # 12 CODES_STATUS_CRITICAL_PRESS
        # 13 CODES_STATUS_MFC_TEMP
        # 14 CODES_STATUS_VACUUM_FLOW

        # Make a table out of the PSM system status error based on the text above
        PSM_system_status_error = pd.DataFrame({'PSM_system_status_error': ['GROWTH TUBE TEMPERATURE', 'SATURATOR TEMPERATURE', 'SATURATOR FLOW', 'PREHEATER TEMPERATURE', 'INLET TEMPERATURE', 'MIX1 PRESSURE', 'MIX2 PRESSURE', 'ABSOLUTE PRESSURE', 'EXCESS FLOW', 'DRAIN LEVEL', 'AMBIENT TEMPERATURE', 'DRAIN TEMPERATURE', 'CRITICAL PRESSURE', 'MFC TEMPERATURE', 'VACUUM FLOW RATE']})

        # Find all unique PSM system status errors from df['PSM_system_status_error']
        PSM_system_status_error_unique = np.unique(df['PSM_system_status_error'])

        # make a 16 bit binary row of zeros
        zeros = '0000000000000000'
        # change every bit of "zeros" based on all the CPC_system_status_error_unique bit rows
        for i in range(len(PSM_system_status_error_unique)):
            for j in range(16):
                if PSM_system_status_error_unique[i][j] == '1':
                    zeros = zeros[:j] + '1' + zeros[j+1:]

        PSM_errors_list = [PSM_system_status_error.iloc[i, 0] for i in range(16) if zeros[15 - i] == '1']

        # CPC bits correspond to errors:
        # 0 CODES_STATUS_OPTICS_TEMP
        # 1 CODES_STATUS_SATURATOR_TEMP
        # 2 CODES_STATUS_CONDENSER_TEMP
        # 3 CODES_STATUS_ABS_PRESS
        # 4 CODES_STATUS_NOZ_PRESS
        # 5 CODES_STATUS_LASER_POWER
        # 6 CODES_STATUS_LIQUID_LEVEL
        # 7 CODES_STATUS_AMBIENT_TEMP
        # 8 CODES_STATUS_CRITICAL_PRESS
        # 9 CODES_STATUS_PULSE_QUALITY

        # Make a table out of the CPC system status error based on the text above
        CPC_system_status_error = pd.DataFrame({'CPC_system_status_error': ['OPTICS TEMPERATURE', 'SATURATOR TEMPERATURE', 'CONDENSER TEMPERATURE', 'ABSOLUTE PRESSURE', 'NOZZLE PRESSURE', 'LASER POWER', 'LIQUID LEVEL', 'AMBIENT TEMPERATURE', 'CRITICAL PRESSURE', 'PULSE QUALITY']})

        # Find all unique CPC system status errors
        CPC_system_status_error_unique = df['CPC_system_status_error'].unique()

        # make a 16 bit binary row of zeros
        zeros = '0000000000000000'
        # change every bit of "zeros" based on all the CPC_system_status_error_unique bit rows
        for i in range(len(CPC_system_status_error_unique)):
            for j in range(16):
                if CPC_system_status_error_unique[i][j] == '1':
                    zeros = zeros[:j] + '1' + zeros[j+1:]

        CPC_errors_list = [CPC_system_status_error.iloc[i, 0] for i in range(16) if zeros[15 - i] == '1']

        # Return PSM and CPC errors as lists
        return PSM_errors_list, CPC_errors_list

    def inst_calib(self):
        # Goes through the calibration data and calculates the calibration curves

        n_average = 20

        self.reload_calibration()

        # make a linear fit of cal_diameter as a function of cal_satflow for the last three values of the dataframe cal
        cal_fit = np.polyfit(self.calibration_df['cal_satflow'][-3:], self.calibration_df['cal_diameter'][-3:], 1)

        # add cal_satflow 0.05 to the cal dataframe
        #cal.loc[len(cal)] = [0.05, 0, 0]

        # check if calibration fit is enabled in extra features window
        if self.extra_features.calibration_fit_checkbox.isChecked():
            # plot calibration file to refresh the fitting dataframe
            self.extra_features.plot_calibration_file(self)
            # use the fitting dataframe in place of the calibration dataframe
            self.calibration_df = self.extra_features.calibration_fitting_df
        # use cal_fit to define the satflow where the diameter is the upper limit of the instrument
        elif self.model == 'PSM2.0':
            max_dp = self.max_dp # use max_dp from calibration file
            satflowlimit = (max_dp - cal_fit[1])/cal_fit[0]
            # limit satflow lower limit to 0.05
            if satflowlimit < 0.05:
                satflowlimit = 0.05
            self.calibration_df.iloc[-1, self.calibration_df.columns.get_loc('cal_satflow')] = satflowlimit
            self.calibration_df.iloc[-1, self.calibration_df.columns.get_loc('cal_diameter')] = max_dp
        else:
            max_dp = self.max_dp # use max_dp from calibration file
            satflowlimit = (max_dp - cal_fit[1])/cal_fit[0]
            # limit satflow lower limit to 0.1
            if satflowlimit < 0.1:
                satflowlimit = 0.1
            self.calibration_df.iloc[-1, self.calibration_df.columns.get_loc('cal_satflow')] = satflowlimit
            self.calibration_df.iloc[-1, self.calibration_df.columns.get_loc('cal_diameter')] = max_dp

        # sort cal dataframe by cal_satflow in descending order and reindex
        self.calibration_df = self.calibration_df.sort_values(by=['cal_satflow'], ascending=False)
        self.calibration_df = self.calibration_df.reset_index(drop=True)

        # if valid Scan status values in data, use them to define up and down scans
        if 'Scan status' in self.data_df_copy.columns and 9 not in self.data_df_copy['Scan status'].values:
            print("Scan status column found.")
            # set rising and high to upscan (1), falling and low to downscan (-1), other mode or nan to 0
            self.data_df_copy['up_scan'] = self.data_df_copy['Scan status'].apply(lambda x: 1 if x in [1,2] else -1 if x in [3,0] else 0)
            # filter up_scan 0 values out of the data (leave only 1 and -1 for scan numbering)
            self.data_df_copy = self.data_df_copy[self.data_df_copy['up_scan'] != 0]
            # add scan number from the point of changing scans
            self.data_df_copy['scan_no'] = np.cumsum(abs(self.data_df_copy['up_scan'].diff() / 2))

            # print("unique up_scan values:", self.data_df_copy['up_scan'].unique())
            # print("unique scan_no values:", self.data_df_copy['scan_no'].unique())
            # print(self.data_df_copy[['t','satflow','up_scan','scan_no']].dropna())

        # otherwise, use averaged satflow direction to define up and down scans
        else:
            # find satlow up and down transitions and average satflow_diff over 20s
            satflow_diff = np.convolve(np.diff(self.data_df_copy['satflow']), np.ones((n_average,))/n_average, mode='valid')
            # Force the times when average flow over 20 s is zero to upscan (or downscan)
            satflow_diff[satflow_diff == 0] = -0.01
            # +4 to account for the moving average start and stop
            nan_filler = np.zeros(int((n_average+4)/2))
            nan_filler[:] = np.nan
            self.data_df_copy['up_scan'] = np.append(np.append(nan_filler, np.sign(moving_average(satflow_diff,5))), nan_filler)
            # filter up_scan 0 values out of the data (leave only 1 and -1 for scan numbering)
            self.data_df_copy = self.data_df_copy[self.data_df_copy['up_scan'] != 0]
            # Add scan number from the point of changing scans
            self.data_df_copy['scan_no'] = np.cumsum(abs(self.data_df_copy['up_scan'].diff() / 2))
            # filter satflow 0 out of the data
            self.data_df_copy = self.data_df_copy[self.data_df_copy['satflow'] != 0]

            # print("unique up_scan values:", self.data_df_copy['up_scan'].unique())
            # print("unique scan_no values:", self.data_df_copy['scan_no'].unique())
            # print(self.data_df_copy[['t','satflow','up_scan','scan_no']].dropna())

        return self.calibration_df, self.data_df_copy

    # Bin the raw data to enable avaraging over scans, and to yield supplementary data for the inversion
    def bin_data(self, bin_limits):

        fixed_bin_limits = bin_limits
        num_bins = len(fixed_bin_limits) - 1 # get number of bins
        self.n = num_bins

        # calculate bins
        bins = calculateBins(self.calibration_df,fixed_bin_limits)
        print("bin saturator values", bins)
        self.bin_lims = fixed_bin_limits
        self.bin_centers = geom_means(fixed_bin_limits)

        self.lowest_bin_limit = np.min(bins)
        print("lowest bin limit", self.lowest_bin_limit)

        # add bins column
        self.data_df_copy['bins'] = pd.cut(self.data_df_copy['satflow'],bins)

        # Calculate bin mean concentration grouped by scans and flow bins
        self.data_df_copy['bin_mean_c'] = self.data_df_copy.groupby(['bins', 'scan_no'], observed=False)['concentration'].transform('mean')

        # Add the dilution factor to the dataframe
        dilution_factor = float(self.ext_dilution_fac_input.text())
        self.data_df_copy['bin_mean_c'] = self.data_df_copy['bin_mean_c'] * dilution_factor

        df_binmean = self.data_df_copy[['bins', 'scan_no','bin_mean_c']].groupby(['bins', 'scan_no'], observed=False).mean()
        df_binmean.reset_index(inplace=True)
        self.n_scans = np.unique(df_binmean['scan_no'])

        df_sorted = self.data_df_copy[['t','scan_no']].sort_values(by=['t'], ascending=True)
        df_sorted = df_sorted.groupby('scan_no').first()
        self.scan_start_time = np.array(df_sorted.reset_index(drop=True))[:,0]
        scan_start_temp = pd.to_datetime(self.scan_start_time)
        self.scan_start_times_posix = scan_start_temp.astype('int64') // 10**9 # changed int to 'int64'


        # create a new dataframe where first column is lower bin edge and second column is upper bin edge
        self.Nbinned = pd.DataFrame({'lower':bins[:-1], 'upper':bins[1:]})
        self.Nbinned['bins'] = pd.unique(df_binmean['bins'])

        # calculate new parameter called Dp by interpolating the cal_diameter as a function of cal_satflow
        self.Nbinned['UpperDp'] = np.interp(self.Nbinned['lower'], np.flip(self.calibration_df['cal_satflow']), np.flip(self.calibration_df['cal_diameter']))
        self.Nbinned['LowerDp'] = np.interp(self.Nbinned['upper'], np.flip(self.calibration_df['cal_satflow']), np.flip(self.calibration_df['cal_diameter']))
        self.Nbinned['dlogDp'] = np.log10(self.Nbinned['UpperDp']) - np.log10(self.Nbinned['LowerDp'])
        self.Nbinned['MaxDeteff'] = np.interp(self.Nbinned['UpperDp'], self.calibration_df['cal_diameter'], self.calibration_df['cal_maxdeteff'])

        self.Dplot = np.flip(fixed_bin_limits)

        # pivot from long to wide format in a single operation, then merge once
        pivot_df = df_binmean.pivot(index='bins', columns='scan_no', values='bin_mean_c')
        pivot_df.columns = [f'scanN{i}' for i in range(len(pivot_df.columns))]
        self.Nbinned = self.Nbinned.merge(pivot_df, left_on='bins', right_index=True, how='left')

        # set negative values in Nbinned to nan
        skip = 7 # skip 7 metadata columns: lower, upper, bins, UpperDp, LowerDp, dlogDp, MaxDeteff
        temp = self.Nbinned.iloc[:,skip:]
        temp[temp<0] = np.nan
        self.Nbinned.iloc[:,skip:] = temp
        
        return self.Nbinned, self.n_scans, self.scan_start_time, self.Dplot

    # validate scans by checking scan lengths and start and end values
    def validate_scans(self):

        if len(self.n_scans) < 3:
            print("Not enough scans to validate.")
            self.error_output.append("Not enough scans to validate.\n")
            return

        faulty_scans = [] # indexes of faulty scans

        # check scan lengths
        print("Validating scan lengths...")
        # get median length between scan start times
        median_length = np.median(np.diff(self.scan_start_times_posix))
        print(f"Median scan length: {median_length} seconds")
        #print("Scan lengths:", np.diff(self.scan_start_times_posix))
        time_variation_limit = median_length * 0.05 # 5% variation allowed
        for i in range(len(self.scan_start_times_posix)-1): # skip last scan, no comparison value
            # compare scan length to median length
            scan_length = self.scan_start_times_posix[i+1] - self.scan_start_times_posix[i]
            # if scan length is much longer than median length, mark as faulty scan
            if scan_length > median_length + time_variation_limit:
                scan_start_time_str = pd.to_datetime(self.scan_start_time[i], unit='s').strftime('%Y-%m-%d %H:%M:%S')
                print(f"Scan {i} at {scan_start_time_str} has faulty length: {scan_length} seconds")
                faulty_scans.append(i)
        
        # # check scan start and end values
        # print("Validating scan start and end values...")
        # max_satflow_limit = self.max_satflow_limit
        # min_satflow_limit = self.min_satflow_limit
        # print(f"Max satflow limit: {max_satflow_limit}, Min satflow limit: {min_satflow_limit}")
        # # check min and max satflow values of each scan
        # for i in range(len(self.n_scans)):
        #     scan_max_satflow = self.data_df[self.data_df['scan_no'] == i]['satflow'].max()
        #     scan_min_satflow = self.data_df[self.data_df['scan_no'] == i]['satflow'].min()
        #     # if max satflow doesn't go past max_satflow_limit, mark as faulty scan
        #     if scan_max_satflow <= max_satflow_limit:
        #         scan_start_time_str = pd.to_datetime(self.scan_start_time[i], unit='s').strftime('%Y-%m-%d %H:%M:%S')
        #         print(f"Scan {i} at {scan_start_time_str} has faulty max satflow: {scan_max_satflow}")
        #         if i not in faulty_scans:
        #             faulty_scans.append(i)
        #     # if scan min satflow doesn't go below min_satflow_limit, mark as faulty scan
        #     if scan_min_satflow >= min_satflow_limit: # lowest satflow at highest bin edge
        #         scan_start_time_str = pd.to_datetime(self.scan_start_time[i], unit='s').strftime('%Y-%m-%d %H:%M:%S')
        #         print(f"Scan {i} at {scan_start_time_str} has faulty min satflow: {scan_min_satflow}")
        #         if i not in faulty_scans:
        #             faulty_scans.append(i)

        # if no faulty scans found, return
        if len(faulty_scans) == 0:
            print("No faulty scans found.")
            self.error_output.append("No faulty scans found.\n")
            return
        # remove faulty scans from relevant dataframes and lists
        # remove matching columns of Nbinned
        skip = 7 # skip 7 metadata columns: lower, upper, bins, UpperDp, LowerDp, dlogDp, MaxDeteff
        faulty_scans_skip = faulty_scans.copy()
        for i in range(len(faulty_scans_skip)):
            faulty_scans_skip[i] += skip # increment each scan index value by skip value
        self.Nbinned.drop(self.Nbinned.columns[faulty_scans_skip], axis=1, inplace=True)
        # remove matching scan_start_time and scan_start_times_posix values
        self.scan_start_time = np.delete(self.scan_start_time, faulty_scans)
        self.scan_start_times_posix = np.delete(self.scan_start_times_posix, faulty_scans)
        # remove matching amount of n_scans values from end (keep number order)
        self.n_scans = self.n_scans[:-len(faulty_scans)]
        # reset Nbinned column numbering
        self.Nbinned.columns = ['lower', 'upper', 'bins', 'UpperDp', 'LowerDp', 'dlogDp', 'MaxDeteff'] + [f'scanN{i}' for i in range(len(self.n_scans))]

        if len(faulty_scans) == 1:
            print("Removed 1 faulty scan.")
            self.error_output.append("Removed 1 faulty scan.\n")
        else:
            print(f"Removed {len(faulty_scans)} faulty scans.")
            self.error_output.append(f"Removed {len(faulty_scans)} faulty scans.\n")

    def step_inversion(self):

        # create a new dataframe where first column is lower bin edge and second column is upper bin edge
        self.Ninv = self.Nbinned[['bins','LowerDp','UpperDp','dlogDp','MaxDeteff']].copy()

        self.Ninv['binCenter'] = np.flip(np.append(self.bin_centers,0))
        
        scan_cols = [f'scanN{i}' for i in range(len(self.n_scans))]
        divisor = self.Ninv['dlogDp'] * self.Ninv['MaxDeteff']

        # vectorized diff and division across all scan columns at once
        dn_df = self.Nbinned[scan_cols].diff().div(divisor, axis=0)
        dn_df.columns = [f'dN{i}' for i in range(len(self.n_scans))]
        self.Ninv = pd.concat([self.Ninv, dn_df], axis=1)

        # Drop the first row of the dataframe Ninv (as this is only the first bin edge)
        self.Ninv = self.Ninv.drop(self.Ninv.index[0])
        self.Ninv['UpperDp'] = np.flip(self.bin_lims[1:])
        self.Ninv['LowerDp'] = np.flip(self.bin_lims[:-1])

        # set all negative values to nan
        skip = 6 # skip 6 metadata columns: bins, LowerDp, UpperDp, dlogDp, MaxDeteff, binCenter
        temp = self.Ninv.iloc[:, skip:]
        self.Ninv.iloc[:, skip:] = temp.mask(temp < 0)

        # Repeat the process for the averaged data
        self.Ninv_avg = self.Nbinned[['bins','LowerDp','UpperDp','dlogDp','MaxDeteff']].copy()
        self.Ninv_avg['binCenter'] = np.flip(np.append(self.bin_centers,0))
        divisor_avg = self.Ninv_avg['dlogDp'] * self.Ninv_avg['MaxDeteff']

        # vectorized diff and division across all scan columns at once
        dn_avg_df = self.Nbinned_avg[scan_cols].diff().div(divisor_avg, axis=0)
        dn_avg_df.columns = [f'dN{i}' for i in range(len(self.n_scans))]
        self.Ninv_avg = pd.concat([self.Ninv_avg, dn_avg_df], axis=1)

        # Drop the first row of the dataframe Ninv (as this is only the first bin edge)
        self.Ninv_avg = self.Ninv_avg.drop(self.Ninv_avg.index[0])
        self.Ninv_avg['UpperDp'] = np.flip(self.bin_lims[1:])
        self.Ninv_avg['LowerDp'] = np.flip(self.bin_lims[:-1])

        # set all negative values to nan
        skip = 6 # skip 6 metadata columns: bins, LowerDp, UpperDp, dlogDp, MaxDeteff, binCenter
        temp = self.Ninv_avg.iloc[:, skip:]
        self.Ninv_avg.iloc[:, skip:] = temp.mask(temp < 0)

    # show / hide middle plot day markers based on user setting
    def toggle_day_markers(self):
        if len(self.day_markers) != 0:
            if self.day_markers_btn.isChecked():
                for marker in self.day_markers:
                    marker.show()
            else:
                for marker in self.day_markers:
                    marker.hide()

    def print_marker_pos(self,marker):
        marker_x = marker.getXPos()
        print("Marker position:", marker_x)

    def sync_markers(self, marker):

        # mid_plot_marker range = [0, n_scans]
        # raw_plot_marker range = [posix_timestamps[0],posix_timestamps[-1]]
        if marker is self.raw_plot_marker:
            cur_pos_stamp = self.raw_plot_marker.getXPos()
            diff = np.abs(self.scan_start_times_posix - cur_pos_stamp)
            new_pos_for_mid = np.argmin(diff)
            if new_pos_for_mid > self.n_scans[-1]:
                new_pos_for_mid -= 1
            #print("new_pos_for_mid:", new_pos_for_mid)
            self.mid_plot_marker.setPos(new_pos_for_mid)
        else:
            cur_pos_scan_index = int(self.mid_plot_marker.getXPos())
            self.raw_plot_marker.setPos(int(self.scan_start_times_posix[cur_pos_scan_index]))

    def checkbox_button_state_changed(self, state):
        print("Checkbox state changed:", state)
        # add checkbox logic here
    
    def update_bin_selection(self):
        # make sure model and max_dp are defined (data and calibration files are loaded)
        if self.model is None or self.max_dp is None:
            return
        # check if bin_selection is set to "custom"
        if self.bin_selection.currentText() == "custom":
            custom_bins = True # keep custom bins when updating bin_selection
        else:
            custom_bins = False # set bin_selection to default value
        # clear bin_selection before adding new items
        self.bin_selection.clear()

        # set largest bin limit to 12 if max_dp from calibration file is at least 11
        if self.max_dp >= 11:
            max_dp = 12
        else: # otherwise set largest bin limit to max_dp from calibration file
            max_dp = self.max_dp
        # convert max_dp to integer if it's a whole number
        if max_dp == int(max_dp):
            max_dp = int(max_dp)

        # set smallest bin limit to 1.2 if min_dp from calibration file is at most 1.2
        if self.min_dp <= 1.2:
            min_dp = 1.2
        else:
            min_dp = self.min_dp
        # convert min_dp to integer if it's a whole number
        if min_dp == int(min_dp):
            min_dp = int(min_dp)

        # define bin limits
        if self.model == 'PSM2.0':
            # TODO set min and max to 1.2 and 12 if calibration file allows
            bin_limits = [
                [min_dp, 2, 5, 8, max_dp], # 4 bins
                [min_dp, 1.5, 2, 3, 5, 8.33, max_dp], # 6 bins
                [min_dp, 1.4, 1.7, 2, 3, 4, 6, 8.33, max_dp], # 8 bins
                [min_dp, 1.5, 2, 2.5, 3.1, 4, 5, 6, 7.7, 10, max_dp], # 10 bins
                [min_dp, 1.4, 1.7, 2, 2.4, 3, 3.6, 4.4, 5.4, 6.6, 8, 10, max_dp], # 12 bins
                [min_dp, 1.4, 1.7, 2, 2.4, 2.8, 3.3, 3.8, 4.5, 5.3, 6.3, 7.4, 8.7, 10, max_dp] # 14 bins
                ]
        elif self.model == 'A10':
            bin_limits = [
                [min_dp, 1.5, 1.7, 2.5, max_dp],
                [min_dp, 1.3, 1.5, 1.7, 2.5, 3, max_dp]
                ]
        # clean up bin limits and add to dictionary
        self.bin_dict = {}
        for bin_list in bin_limits:
            bin_list.sort() # sort bin limits in ascending order
            bin_list = list(dict.fromkeys(bin_list)) # remove duplicate bin limit values
            bin_list_max_filtered = list(filter(lambda x: x <= max_dp, bin_list)) # remove bin limits larger than max_dp
            bin_list_min_filtered = list(filter(lambda x: x >= min_dp, bin_list_max_filtered)) # remove bin limits smaller than min_dp
            # add to dictionary with bin amount as key and bin limit list as value
            self.bin_dict[str(len(bin_list_min_filtered)-1)] = bin_list_min_filtered
        # add bin amounts to bin_selection
        bin_amounts = ["custom"]
        for i in self.bin_dict.keys():
            bin_amounts.append(i)
        self.bin_selection.addItems(bin_amounts)
        # if custom bins are not set by user, set bin_selection value to 8 or last item (most bins) by default
        if custom_bins == False:
            if "8" in bin_amounts:
                self.bin_selection.setCurrentText("8")
            else:
                self.bin_selection.setCurrentText(bin_amounts[-1])

    # show bin limits of selected bin amount in GUI
    def show_bin_limits(self, bin_amount):
        if bin_amount not in ["custom", ""]:
            bin_limits = self.bin_dict[bin_amount]
            bin_limits_text = " ".join(map(str, bin_limits))
            self.bin_limits_edit.setText(bin_limits_text)
    
    # change bin amount selection to "custom" when bin limits are edited
    def bin_limits_edited(self):
        self.bin_selection.setCurrentText("custom")
    
    # convert bin limits input text to list of floats
    def convert_bin_limits(self):
        # get bin limits from bin_limits_edit
        bin_limits_text = self.bin_limits_edit.text()
        # split bin limits text to list
        bin_limits = bin_limits_text.split()
        # convert bin limits to float
        bin_limits = [float(i) for i in bin_limits]
        # sort bin limits in ascending order
        bin_limits.sort()
        # remove duplicate bin limit values
        bin_limits = list(dict.fromkeys(bin_limits))
        print("bin_limits:", bin_limits)
        return bin_limits

    # save inversion data to a file or multiple files
    def save_inversion_data(self):
        self.save_button.clearFocus()
        # make sure inversion data exists
        if self.Ninv is None:
            self.error_output.append("No inverted data to save")
            return
        print("Saving inverted data...")
        daily_files = False
        # find unique days in scan_start_time
        unique_days = np.unique(self.scan_start_time.astype('datetime64[D]'))
        # if daily files is checked and data is from multiple days, select save folder
        if self.daily_files_btn.isChecked() and len(unique_days) > 1:
            # browse for save folder
            directory = QFileDialog.getExistingDirectory(self, "Select save folder")
            # if file dialog is canceled, return
            if not directory:
                return
            # set daily_files flag, create filenames and dataframes later
            daily_files = True
        else: # otherwise, select single save file
            # suggest filename based on original name if one file is selected
            if len(self.current_filenames) == 1:
                # get filename, remove file ending (.dat) and add '_dNdlogDp'
                filename_suggestion = self.current_filenames[0].replace(".dat", "") + "_dNdlogDp"
            else: # if multiple files are selected, suggest filename with day (YYYYMMDD) or days (YYYYMMDD-YYYYMMDD)
                # if only one day, suggest filename with that day
                if len(unique_days) == 1:
                    filename_suggestion = str(str(unique_days[0]).replace("-", "")) + "_dNdlogDp"
                else: # if multiple days, suggest filename with first and last day
                    filename_suggestion = str(str(unique_days[0]).replace("-", "")) + "-" + str(str(unique_days[-1]).replace("-", "")) + "_dNdlogDp"
            # open file dialog
            file_name, _ = QFileDialog.getSaveFileName(self, "Save inverted data", filename_suggestion, "csv files (*.csv);;All files (*)", options=QFileDialog.Option.ReadOnly)
            # if file dialog is canceled, return
            if not file_name:
                return
            filenames = [file_name]
        
        # set cursor to loading
        self.application.setOverrideCursor(Qt.WaitCursor)
        
        try:
            # construct headers list for the output file
            dp_headers = []
            # get LowerDp and UpperDp values on each row
            # using i+1 as index to skip index 0 (rows start from 1)
            for i in range(len(self.Ninv)):
                lower = str(round(self.Ninv['LowerDp'][i+1], 2)) # round to 2 decimals
                upper = str(round(self.Ninv['UpperDp'][i+1], 2)) # round to 2 decimals
                # construct header string and add to list
                dp_headers.append('Bin ' + lower + '-' + upper + ' nm')
            #print(dp_headers)

            # transpose the Ninv dataframe to get bins as columns and scans as rows
            save_data = self.Ninv.T
            # filter rows that start with 'dN' to leave out metadata rows
            save_data = save_data.filter(regex='^dN', axis=0)
            # add dp_headers as column names
            save_data.columns = dp_headers
            # reverse the order of columns: from smallest bin to largest bin
            save_data = save_data[save_data.columns[::-1]]

            # round values >= 1 to 2 decimals
            save_data = save_data.mask(save_data >= 1, save_data.astype(float).round(2))
            # round values < 1 to 2 significant numbers
            save_data = save_data.mask(save_data < 1, save_data.map(lambda x: float("%.2g" % x)))

            # if Matlab time format is toggled on, convert scan_start_time values to Matlab format
            if self.matlab_time_btn.isChecked():
                matlab_start_times = []
                for i in self.scan_start_time:
                    # convert numpy.datetime64 object to datetime object
                    t = pd.to_datetime(i)
                    # convert datetime object to Matlab format: dd-mmm-yyyy HH:MM:SS e.g. 19-Aug-2023 14:23:01
                    t = t.strftime('%d-%b-%Y %H:%M:%S')
                    # add time to matlab_start_times list
                    matlab_start_times.append(t)
                # add scan start times in Matlab format as first column
                save_data.insert(0, 'Scan start time', matlab_start_times)
            # if Matlab time format is toggled off, use start_scan_time as it is
            else:
                # add scan start times as first column
                save_data.insert(0, 'Scan start time', self.scan_start_time)
            
            # calculate concentration values above largest bin
            dilution_factor = float(self.ext_dilution_fac_input.text())
            larger_concentration = concentration_above_bins(self.scan_start_time, self.data_df, self.lowest_bin_limit, dilution_factor)
            # add result as column to save_data dataframe
            highest_dp = str(round(self.Ninv['UpperDp'].iloc[0], 2))
            save_data[('Dp >' + highest_dp + ' nm total number concentration')] = larger_concentration

            # if daily_files flag is set, create daily dataframes and filenames
            if daily_files:
                # find unique dates from scan start times
                unique_dates = pd.to_datetime(save_data['Scan start time']).dt.date.unique()
                # create empty lists for dataframes and filenames
                dataframes = []
                filenames = []
                # loop through all unique dates
                for date in unique_dates:
                    # filter save_data by date
                    dataframe = save_data[pd.to_datetime(save_data['Scan start time']).dt.date == date]
                    # create filename with YYYYMMDD date
                    filename = directory + '/' + date.strftime('%Y%m%d') + '_dNdlogDp' + '.csv'
                    # add filename and dataframe to lists
                    filenames.append(filename)
                    dataframes.append(dataframe)
            # if only one file, put save_data as one element into dataframes list
            else:
                dataframes = [save_data]

            # loop through all filenames and dataframes
            for i in range(len(filenames)):
                try:
                    filename = filenames[i]
                    dataframe = dataframes[i]
                    # save data to file
                    dataframe.to_csv(filename, sep=',', index=False, lineterminator='\n')
                    # add software version and calibration filename to first row of the file
                    with open(filename, 'r') as original:
                        data = original.read()
                    with open(filename, 'w') as modified:
                        modified.write(f"Software version: {version_number} ; Calibration file: {self.calibration_file_label.text().split('/')[-1]}\n")
                        modified.write(data)
                    print("Inverted data saved to", filename)
                    self.error_output.append("Inverted data saved to " + filename)
                except Exception as e:
                    self.error_output.append("Error saving inverted data:")
                    self.error_output.append(str(e))
            
            # restore cursor to normal
            self.application.restoreOverrideCursor()
        
        except Exception as e:
            self.error_output.append("Error saving inverted data:")
            self.error_output.append(str(e))
            self.application.restoreOverrideCursor() # restore cursor to normal

    def keyPressEvent(self,event):
        if self.markers_added == True:
            marker_x = self.mid_plot_marker.getXPos()
            if event.key() == Qt.Key.Key_Left:
                self.mid_plot_marker.setPos(int(marker_x) - 1)
                self.sync_markers(self.mid_plot_marker)
            elif event.key() == Qt.Key.Key_Right:
                self.mid_plot_marker.setPos(int(marker_x) + 1)
                self.sync_markers(self.mid_plot_marker)

    def export_plot(self, plot):
        exporter = pg.exporters.ImageExporter(plot.scene())
        file_name, _ = QFileDialog.getSaveFileName(None, "Save Image", "", "PNG (*.png);;JPEG (*.jpg);;All Files (*)")
        if file_name:
            exporter.export(file_name)


def main():
    app = QApplication(sys.argv)
    window = MainWindow(app)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
