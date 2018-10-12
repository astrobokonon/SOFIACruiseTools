
### Cruise Director Instructions

#### Overview
CruiseDirector is a tool for recording notes during flights. It features:
- Tool to record notes throughout the flight
- Reads in FITS headers from observations for easy checking
- Timers for current leg
- Timers for flight

#### Starting the program
To run the code, use:
./runDirector

The first window that opens will allow for the setup of the code. There are six
fields to set up, but not all are required:

- **Flight Plan**: Select the .mis file for the current flight. The program will
  parse this for information about each leg. The instrument is also pulled from
  the name of this file.
- **Instrument**: In case the wrong instrument is parsed from the flight plan, 
set it
  here. The choice of instrument alters both the default FITS keywords to present
  and how the code searches for observations. FORCAST, FIFI-LS, EXES, and HAWC+
  (Ground) search for .fits files while HAWC+ (Flight) searches for .grabme 
  files. 
- **Log Output**: This is where the comment log will be stored. The default naming
  convention is "SILog_<utc date stamp>.txt". This is the only required field. 
- **Log Data Output**: This file will contain a csv version of the FITS  
keywords parsed from observations during the flight. 
- **Data Location**: Where observations will be read in from. FORCAST, EXES, and
  either HAWC settings will search for the corresponding file type in this
  directory only, while FIFI-LS searches for all FITS files in all subdirectories. 
  FORCAST data is stored in two channels, r and b. To avoid having to set up 
  separate runs of Cruise Director every time the channel being used is 
  changed, Cruise Director instead always looks in both. For FORCAST 
  observations, the *data location* should be set to the parent directory of 
  the r and b directories. 
- **FITS Keywords**: This opens a new dialog where the initial keywords to be
  monitored are defined. Each instrument has a default list, but this can be 
  customized.
  A personalized list can be curated then saved to file
  for future use. This file can later be read in for quick 
  personalization. Regardless of the keywords chosen, three keywords are 
  added automatically:
  + NOTES: For recording notes for a specific files.
  + BADCAL: A column for designating which files you have flagged for later 
  inspection with the "Flag File" button. 
  + HEADER_CHECK: Shows the result of passing the file through header_checker.
  A pass indicates there were no problems while "FAIL" indicates one or 
  more warnings were found. Details can be found in the header_checker_<utc 
  date stamp>.log file. 

Once the setup is complete, the main Cruise Director window opens. There are six
panels:

- **Setup**: This contains both the control buttons and the settings defined 
during
  startup. To change the setting, click the "Set Up" button. The "Start" button
  begins the flight timers and starts the collection of data, while "End" performs
  a final write of all log files and closes the program.

- **Current Flight Progress**: This contains two timers, the Mission Elapsed 
Time
  (MET) and Time Until Landing (TTL), both of which are initiated by the "Start"
  button.

- **Flight Plan Information**: Details each leg of the flight as parsed from the
  selected .mis file. The "Previous Leg" and "Next Leg" buttons can be used to
  step through the flight. These also control the leg timers. 

- **World Times**: The current time in both UTC and Local time zones. 

- **Leg Timers**: Timers for the current leg, as defined by the contents of the
  "Flight Plan Information" panel. Controls are present to start, pause, and
  reset the timer, as well as to control the counting direction (up or down).
  If you need to make small adjustments to the leg timer, there are buttons to
  add or subtract one minute from the time. Above the leg timer are the leg start
  time and duration from the flight plan for reference. 

- **Logging**: This is the main panel and has two tabs. 
    - *Cruise Director Log*: This is the open log for recording events/comments
      during the flight. It is saved to the file defined with the "Log Output"
      step of setup. There are quick buttons for common events, such as "Takeoff" and
      "Landing", as well as a text box to enter text into at the bottom. All comments
      are posted in the window of the tab as well as written to file as soon as they
      are made. 
    - *Data Log*: This window displays the FITS keywords read in during the 
     flight.
      The rate at which the program looks for new files is controlled by the
      "Autoupdate every: " control. As new files are found, the table is populated with
      the files sorted by modification time. There are a few quick controls
      available: 
        + To alter the contents of any field, click in the cell and enter the 
          modification. The corresponding file header is not altered, only the 
          local log. 
        + To search for files immediately, use the "Force Update" button. Any time 
          the table is altered, either by finding a new file or by changing a keyword 
          property, the log file is written to the filename specified by the "Data Log" field. 
        + If a file read in that you want to flag for future investigation, 
          select the desired row and click the "Flag File" button. This 
          changes the content of the "BADCAL" column to "FLAG". 
        + A blank line can be added to the log with the "Add a Blank Row" button. 
        + To delete a row, select the row by clicking on any cell in the desired row
          and use the "Remove Highlighted Row" button. 
        + To alter the keywords being used, use the "Edit Keywords..." button. 
          This opens the same dialog shown during the setup step. Adding a keyword
          during the flight will only look for that keyword in all new files. It
          will not fill it for past files until "Force Update" is pressed. 
    - The default set up does not allow the user to see both logs at the same
      time. If you want to see both simultaneously, there is a button on the Data
      Log tab to pop-out the Director Log called "Open Director Log". This opens
      a new window mimicing the Director Log and works the same. When this window
      is closed, the contents of the log are copied to the Cruise Director Log
      tab. 

To start the MET/TTL timers and start gathering data files, click the "Start"
button. To end the program, use the "End" button. Upon confirmation of exiting,
both the Director's Log and the Data Log are written to file once again, then
 the window is closed. 

