# PSM Inversion Tool - Software change log

### 0.10.4 - 2026.02.25
- fix pandas FutureWarnings: replace inplace fillna with direct assignment, use iloc for calibration_df last-row assignment, add observed=False to groupby calls, replace deprecated rolling axis=1 with transposed equivalent
- fix SettingWithCopyWarning: copy Nbinned slice before assigning columns in step_inversion
- add pandas=2.3.3 to environment.yaml (temporary exe build fix until pandas 3 scan number bug is fixed)

### 0.10.3 - 2026.02.24
- new default bin limits (ACTRIS binning)
- set default bin amount to 8
- set min Dp to 1.2 if calibration file's lowest Dp <= 1.2
- set max Dp to 12 if calibration file's highest Dp >= 11

### 0.10.2 - 2026.01.20
- 10 Hz files: handle special characters in file path

### 0.10.1 - 2026.01.12
- apply external dilution factor to concentration above max bin (save data)
- sort loaded file names alphabetically, i.e. by timestamp (note: this was automatically done on Windows, but on Mac it was possible to load files in wrong order)
- improved 10 Hz data conversion speed (expand_cpc_data)

### 0.10.0 - 2025.12.11
- input for CPC time lag in seconds (1 decimal place, round if 1 Hz data)
- shift concentration when inverting data (raw data is unshifted)
- use copy of data_df in inversion

### 0.9.5 - 2025.12.09
- keep settings when loading and refreshing files (average number, dilution factor, number of bins)

### 0.9.4 - 2025.12.05
- changed scan status detection: rising 1 & 2 (was 0 & 1), falling 3 & 0 (was 2 & 3)

### 0.9.3 - 2025.11.27
- 10 Hz CPC filename lookup fix (device nickname compatibility)
- removed scan min/max flow check from quality filter (Raw data quality filtering)

### 0.9.2 - 2025.11.24
- 10 Hz file lookup with multiple CPC IDN values

### 0.9.1 - 2025.11.24
- 10 Hz 'Remove data with errors' support
- Fixed file label sizes

### 0.9.0 - 2025.11.20
- 10 Hz conversion (controls and functions)

### 0.8.9 - 2025.09.10
- Set negative values to NaN

### 0.8.8 - 2025.09.03
- Average plot toggle (change view instantly)

### 0.8.7 - 2025.09.03
- Plot fixes (uniform layouts and titles)

### 0.8.6 - 2025.09.01
- New logo

### 0.8.5 - 2025.09.01
- Logarithmic diameter axis

### 0.8.4 - 2025.08.29
- Filename split bug fix (error output message)

### 0.8.3 - 2025.08.27
- Scan detection numbering bug fix

### 0.8.2 - 2025.06.26
- Scan validation bug fix (when no faulty scans)
- Scan validation GUI info message

### 0.8.1 - 2025.06.26
- Marker sync and initial position fix

### 0.8.0 - 2025.06.19
- Scan validation (check scan length and min/max satflow values)
- Min Dp from calibration file

### 0.7.4 - 2025.06.09
- CPC time lag correction fix (incorrect values before data gaps)
- Skip metadata index bug fix (first scan missing in plot)

### 0.7.3 - 2025.04.30
- Replace inf values with nan

### 0.7.2 - 2025.04.16
- File load error handling (skip error files)

### 0.7.1 - 2025.04.15
- Timestamp fractional seconds support (10 Hz data)
- Partial inversion bug fix
- Clear button focus after click (reponsive arrow keys)

### 0.7.0 - 2025.04.02
- Custom bin limit input
- Max Dp from calibration file

### 0.6.0 - 2025.03.25
- Multi-file inversion
- Loading cursor for lengthy processes
- Load data filter for PSM data files (*PSM*.dat)
- Improved raw data processing speed (reduced color resolution)
- Daily file saving
- Inversion plot day markers

### 0.5.5 - 2025.03.11
- 'Remove data with errors' button fix
- Added CPC error code 9 (pulse quality)

### 0.5.4 - 2025.02.07
- Save software version and calibration filename to file
- Filename suggestion bug fix

### 0.5.3 - 2024.08.13
- Improved file reading flexibility

### 0.5.2 - 2024.07.02
- Improved robustness of scan detection