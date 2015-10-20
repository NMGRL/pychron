Dashboard
================
The dashboard plugins (Server and Client) provide a mechanism for monitoring and displaying a
series of hardware values, for example laboratory temperature or the pneumatic air pressure.
The dashboard is also used to check conditions, issue warnings and take actions. For example if the
air pressure drops between a threshold value, runs experiments can be canceled and all valves locked in
current configuration. Another example is if the bone pressure goes above a threshold the mass spectrometer inlet valve can be
locked closed.


Server
----------------
configure using ``setupfiles/dashboard.xml``

Client
----------------
configure server host and port using Preferences

Labspy
----------------
The dashboard plugin may also integrate with the Labspy web application using the LabspyClientPlugin.
