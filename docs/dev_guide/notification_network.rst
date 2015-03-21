Notification Network
========================

Dashboard + Labspy.js

.. image:: images/lab_graph.*


- **M1. Experiment - Database** -- Experiment uses Database to save data
- **M2. Database - PychronDB** -- Database saves data to a MySQL db
- **M3. Experiment - LabspyClient** -- Experiment uses LabspyClient to update Labspy.js
- **M4. DashClient - Experiment** -- Experiment tests DashClient error flag
- **W1. ExtractionLine - DashServer** -- DashServer displays devices/values exposed by ExtractionLine
- **W2. DashServer - DashClient** -- DashServer pushes notifications to DashClient
- **W3. DashServer - LabspyClient** -- DashServer uses LabspyClient to update Labspy.js
- **L1. LabspyClient - MongoDB** -- LabspyClient writes to MongoDB
- **L2. LabspyClient - MongoDB**