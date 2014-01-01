	public static bool GetParameter(string parameterName, out double value)
	{
		value = 0.0;
		if (!Instrument.GetParameter(parameterName, out value))
		{
			Logger.Log(LogLevel.UserError, String.Format("Could not get the \'{0}\' value.", parameterName));
			return false;
		}
		return true;
	}

	public static bool SetParameter(string parameterName, double value)
	{
		if (!Instrument.SetParameter(parameterName, value))
		{
			Logger.Log(LogLevel.UserError, String.Format("Could not set the \'{0}\' to {1}.", parameterName, value));
			return false;
		}
		return true;
	}

	public static bool SetTuneSetting(string tuneSettingName)
	{
		TuneSettingsManager tsm = new TuneSettingsManager(Instrument.Id);
		TuneSettings tuneSettings = tuneSettings = tsm.ReadEntry(tuneSettingName) as TuneSettings; ;
		TuneParameterBlock tuneBlock = null;
		if (tuneSettings == null)
		{
			Logger.Log(LogLevel.UserError, String.Format("Could not load tune setting \'{0}\'.", tuneSettingName));
			return false;
		}
		else
		{
			tuneBlock = tuneSettings.Object as TuneParameterBlock;
			if (tuneBlock == null)
			{
				Logger.Log(LogLevel.UserError, string.Format("Tune setting \'{0}\' could not convert to tuneblock.", tuneSettingName));
				return false;
			}
			else
			{
				Instrument.TuneParameters.Parameters = tuneBlock;
				Logger.Log(LogLevel.UserInfo, string.Format("Tune setting : \'{0}\' successfully load!", tuneSettingName));
			}
		}
		return true;
	}
	
	public static void ChangeIntegrationTimeForMonitorScan(double integrationTimeInMilliseconds)
	{
		// Get the old integration time to restore the original monitor integration time.
		IRMSBaseMeasurementInfo restoreMeasurementInfo = Instrument.MeasurementInfo;

		// Set the new integration time for the monitor scan
		IRMSBaseMeasurementInfo newMeasurementInfo = new IRMSBaseMeasurementInfo(Instrument.MeasurementInfo);
		newMeasurementInfo.IntegrationTime = integrationTimeInMilliseconds;

		if (!Instrument.ScanTransitionController.StartMonitoring(newMeasurementInfo))
		{
			Logger.Log(LogLevel.UserError, "Could not start the modified monitor scan.");
		}

		// Wait for a little time to look at the changes.
		Thread.Sleep(20000);

		if (!Instrument.ScanTransitionController.StartMonitoring(restoreMeasurementInfo))
		{
			Logger.Log(LogLevel.UserError, "Could not start the restored monitor scan.");
		}
	}
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// This function runs a single scan on a specific cup / sub cup configuration.
	///	Readable output from this function is a list of string with following format:
	///		CupName;Mass;Time;Intensity
	///	Data sample:
	///		AX;11.11;1254;150.21
	///		L2;12.21;1254;2010.012
	/// Remark:
	///		The cup name depends on the active cup configuration from the instruemnt.
	///		To determine a intensity on a counter cup, please activate this cup, because
	///		in default set the counter cups are deactivate.
	/// </summary>
	/// <param name="cupToRead">
	///		The cup which intensities are looking for.
	///		When this parameter are empty or null, then the whole spectrum are displays in the output.
	/// </param>
	/// <param name="mass">
	///		The mass on which the scan are run.
	///		Usable scan masses depends on instrument settings, default between :
	///			0.0 - 260.0
	///	</param>
	/// <param name="integrationTime">
	///		The integration time for the scan, unit is milliseconds.
	///		Usable scan integration times are:
	///			65.536 ms, 131.072 ms, 262.144 ms, 524.288 ms, 1048.576 ms, 2097.152 ms, 
	///			4194.304 ms, 8388.608 ms, 16777.216 ms, 33554.432 ms, 67108.864 ms
	///	</param>
	/// <param name="settlingTime">
	///		The settling time for the scan.
	///	</param>
	/// <returns><c>True</c> if the scan was successfull; otherwise <c>false</c>.</returns>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	private static List<string> Scan(string cupConfigurationName, string subCupConfigurationName, bool enableAllCounterCups, string cupToRead, double mass, double integrationTime, int settlingTime)
	{
		if (!ActivateCupConfiguration(cupConfigurationName, subCupConfigurationName, enableAllCounterCups))
		{
			return null;
		}
		return Scan(cupToRead, mass, integrationTime, settlingTime);
	}
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// This function runs a single scan.
	///	Readable output from this function is a list of string with following format:
	///		CupName;Mass;Time;Intensity
	///	Data sample:
	///		AX;11.11;1254;150.21
	///		L2;12.21;1254;2010.012
	/// Remark:
	///		The cup name depends on the active cup configuration from the instruemnt.
	///		To determine a intensity on a counter cup, please activate this cup, because
	///		in default set the counter cups are deactivate.
	/// </summary>
	/// <param name="cupConfigurationName">
	///		The cup configuation name which would be used for this single scan.
	///	</param>
	/// <param name="subCupConfigurationName">
	///		The sub cup configuation name which would be used for this single scan.
	///	</param>
	/// <param name="cupToRead">
	///		The cup which intensities are looking for.
	///		When this parameter are empty or null, then the whole spectrum are displays in the output.
	/// </param>
	/// <param name="mass">
	///		The mass on which the scan are run.
	///		Usable scan masses depends on instrument settings, default between :
	///			0.0 - 260.0
	///	</param>
	/// <param name="integrationTime">
	///		The integration time for the scan, unit is milliseconds.
	///		Usable scan integration times are:
	///			65.536 ms, 131.072 ms, 262.144 ms, 524.288 ms, 1048.576 ms, 2097.152 ms, 
	///			4194.304 ms, 8388.608 ms, 16777.216 ms, 33554.432 ms, 67108.864 ms
	///	</param>
	/// <param name="settlingTime">
	///		The settling time for the scan.
	///	</param>
	/// <returns><c>True</c> if the scan was successfull; otherwise <c>false</c>.</returns>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	private static List<string> Scan(string cupToRead, double mass, double integrationTime, int settlingTime)
	{
		return Sweep(null, mass, mass, 1.0, integrationTime, settlingTime);
	}
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// This function runs a sweep scan on a specific cup / sub cup configuration.
	/// Usable scan integration times are:
	///		65.536 ms, 131.072 ms, 262.144 ms, 524.288 ms, 1048.576 ms, 2097.152 ms, 
	///		4194.304 ms, 8388.608 ms, 16777.216 ms, 33554.432 ms, 67108.864 ms
	/// Usable scan masses depends on instrument settings, default between :
	///		0.0 - 260.0
	///	Readable output from this function is a list of string with following format:
	///		CupName;Mass;Time;Intensity
	///	Data sample:
	///		AX;11.11;1254;150.21
	///		L2;12.21;1254;2010.012
	/// Remark:
	///		The cup name depends on the active cup configuration from the instruemnt.
	///		To determine a intensity on a counter cup, please activate this cup, because
	///		in default set the counter cups are deactivate.
	/// </summary>
	/// <param name="cupConfigurationName">
	///		The cup configuation name which would be used for this sweep scan.
	///	</param>
	/// <param name="subCupConfigurationName">
	///		The sub cup configuation name which would be used for this sweep scan.
	///	</param>
	/// <param name="cupToRead">
	///		The cup which intensities are looking for.
	///		When this parameter is empty or null, then the whole spectrum is displayed in the log window.
	///	</param>
	/// <param name="startMass">
	///		This is the mass where the scan should be starts.
	///	</param>
	/// <param name="stopMass">
	///		This is the mass where the scan should be ends.
	///	</param>
	/// <param name="stepMass">
	///		This is the step resolution for the sweep.
	///	</param>
	/// <param name="integrationTime">
	///		The integration time for the scan, unit are in milliseconds.
	///		Usable scan integration times are:
	///			65.536 ms, 131.072 ms, 262.144 ms, 524.288 ms, 1048.576 ms, 2097.152 ms, 
	///			4194.304 ms, 8388.608 ms, 16777.216 ms, 33554.432 ms, 67108.864 ms
	///	</param>
	/// <param name="settlingTime">
	///		The settling time for the scan, unit are in milliseconds.
	///	</param>
	/// <returns><c>True</c> if the scan was successfull; otherwise <c>false</c>.</returns>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	private static List<string> Sweep(string cupConfigurationName, string subCupConfigurationName, bool enableAllCounterCups, string cupToRead, double startMass, double stopMass, double stepMass, double integrationTime, int settlingTime)
	{
		if (!ActivateCupConfiguration(cupConfigurationName, subCupConfigurationName, enableAllCounterCups))
		{
			return null;
		}
		return Sweep(cupToRead, startMass, stopMass, stepMass, integrationTime, settlingTime);
	}
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// This function runs a sweep scan.
	/// Usable scan integration times are:
	///		65.536 ms, 131.072 ms, 262.144 ms, 524.288 ms, 1048.576 ms, 2097.152 ms, 
	///		4194.304 ms, 8388.608 ms, 16777.216 ms, 33554.432 ms, 67108.864 ms
	/// Usable scan masses depends on instrument settings, default between :
	///		0.0 - 260.0
	///	Readable output from this function is a list of string with following format:
	///		CupName;Mass;Time;Intensity
	///	Data sample:
	///		AX;11.11;1254;150.21
	///		L2;12.21;1254;2010.012
	/// Remark:
	///		The cup name depends on the active cup configuration from the instruemnt.
	///		To determine a intensity on a counter cup, please activate this cup, because
	///		in default set the counter cups are deactivate.
	/// </summary>
	/// <param name="cupToRead">
	///		The cup which intensities are looking for.
	///		When this parameter are empty or null, then the whole spectrum are displays in the output.
	///	</param>
	/// <param name="startMass">
	///		This is the mass where the scan should be starts.
	///	</param>
	/// <param name="stopMass">
	///		This is the mass where the scan should be ends.
	///	</param>
	/// <param name="stepMass">
	///		This is the step resolution for the sweep.
	///	</param>
	/// <param name="integrationTime">
	///		The integration time for the scan, unit are in milliseconds.
	///		Usable scan integration times are:
	///			65.536 ms, 131.072 ms, 262.144 ms, 524.288 ms, 1048.576 ms, 2097.152 ms, 
	///			4194.304 ms, 8388.608 ms, 16777.216 ms, 33554.432 ms, 67108.864 ms
	///	</param>
	/// <param name="settlingTime">
	///		The settling time for the scan, unit are in milliseconds.
	///	</param>
	/// <returns><c>True</c> if the scan was successfull; otherwise <c>false</c>.</returns>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	private static List<string> Sweep(string cupToRead, double startMass, double stopMass, double stepMass, double integrationTime, int settlingTime)
	{
		List<string> singleResult = null;
		List<string> sweepResult = new List<string>();
		for (double actMass = startMass; actMass <= stopMass; actMass += stepMass)
		{
			Logger.Log(LogLevel.Info, String.Format("Start scan on mass: {0} [u].", actMass));
			singleResult = Instrument.ScanTransitionController.RunSingleScan(actMass, integrationTime, settlingTime);

			if (singleResult != null)
			{
				sweepResult.AddRange(singleResult.ToArray());
			}
			else
			{
				Logger.Log(LogLevel.Error, "No scan data avalaible.");
				break;
			}
		}
		return sweepResult;
	}
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// Prepare the instrument for scans.
	/// </summary>
	/// <returns><c>True</c> if the scan enviroment successfull prepared; otherwise <c>false</c>.</returns>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	private static bool PrepareScanEnviroment()
	{
		m_restoreMeasurementInfo = Instrument.MeasurementInfo;
		return Instrument.ScanTransitionController.InitializeScriptScan(m_restoreMeasurementInfo);
	}
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// Restore the instrument to his old state.
	/// </summary>
	/// <returns><c>True</c> if the scan enviroment successfull restored; otherwise <c>false</c>.</returns>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	private static bool RestoreScanEnviroment()
	{
		if (Instrument != null && m_restoreMeasurementInfo != null)
		{
			if (!Instrument.ScanTransitionController.StartMonitoring(m_restoreMeasurementInfo))
			{
				Logger.Log(LogLevel.UserError, "Could not restart the previous monitor scan.");
				return false;
			}
		}
		m_restoreMeasurementInfo = null;
		return true;
	}
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// Get all cup configurations names from the system.
	/// </summary>
	/// <returns>A list of cup configuration names.</returns>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	private static List<string> GetCupConfigurations()
	{
		List<string> result = new List<string>();
		foreach(var item in Instrument.CupConfigurationDataList)
		{
			result.Add(item.Name);
		}
		return result;
	}
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// Get all sub cup configurations names from a cup cupconfiguration.
	/// </summary>
	/// <param name="cupConfigurationName"></param>
	/// <returns>A list of sub cup configuration names.</returns>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	private static List<string> GetSubCupConfigurations(string cupConfigurationName)
	{
		IRMSBaseCupConfigurationData cupData = Instrument.CupConfigurationDataList.FindCupConfigurationByName(cupConfigurationName);
		if(cupData == null)
		{
			Logger.Log(LogLevel.UserError, String.Format("Could not find cup configuration \'{0}\'.", cupConfigurationName));
			return null;
		}

		List<string> result = new List<string>();
		foreach(var item in cupData.SubCupConfigurationList)
		{
			result.Add(item.Name);
		}
		return result;
	}
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// Activate a cup configuration and sub cup configuration.
	/// </summary>
	/// <param name="cupConfigurationName">The cup configuration name.</param>
	/// <param name="subCupConfigurationName">The sub cup configuration name.</param>
	/// <param name="mass">A nullable mass value. If has a value then use the mass for the monitor scan; otherwise use the master cup mass for the monitor scan.</param>
	/// <returns><c>True</c> if successfull; otherwise <c>false</c>.</returns>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	private static bool ActivateCupConfiguration(string cupConfigurationName, string subCupConfigurationName, bool enableAllCounterCups)
	{
		IRMSBaseCupConfigurationData cupData = Instrument.CupConfigurationDataList.FindCupConfigurationByName(cupConfigurationName);
		if (cupData == null)
		{
			Logger.Log(LogLevel.UserError, String.Format("Could not find cup configuration \'{0}\'.", cupConfigurationName));
			return false;
		}
		IRMSBaseSubCupConfigurationData subCupData = cupData.SubCupConfigurationList.FindSubCupConfigurationByName(subCupConfigurationName);
		if (subCupData == null)
		{
			Logger.Log(LogLevel.UserError, String.Format("Could not find sub cup configuration \'{0}\' in cup configuration.", subCupConfigurationName, cupConfigurationName));
			return false;
		}
		Instrument.CupConfigurationDataList.SetActiveItem(cupData.Identifier, subCupData.Identifier, Instrument.CupSettingDataList, null);
		Instrument.SetHardwareParameters(cupData, subCupData);
		bool success = Instrument.RequestCupConfigurationChange(Instrument.CupConfigurationDataList);
		if (!success)
		{
			Logger.Log(LogLevel.UserError, "Could not request a cup configuration change.");
			return false;
		}

		ActivateAllCounterCups(enableAllCounterCups);
		return true;
	}
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// Runs a monitor scan with specified cup configuration name and sub cup configuration name.
	/// </summary>
	/// <param name="cupConfigurationName"></param>
	/// <param name="subCupConfigurationName"></param>
	/// <returns><c>True</c> if start successfull; otherwise <c>false</c></returns>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	public static bool RunMonitorScan(string cupConfigurationName, string subCupConfigurationName, bool enableAllCounterCups)
	{
		if (!ActivateCupConfiguration(cupConfigurationName, subCupConfigurationName, enableAllCounterCups))
		{
			return false;
		}
		return RunMonitorScan(null);
	}
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// Runs a monitor scan with specified cup configuration name and sub cup configuration name 
	/// and jump to a mass.
	/// </summary>
	/// <param name="cupConfigurationName"></param>
	/// <param name="subCupConfigurationName"></param>
	/// <param name="mass"></param>
	/// <returns><c>True</c> if start successfull; otherwise <c>false</c></returns>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	public static bool RunMonitorScan(string cupConfigurationName, string subCupConfigurationName, double mass, bool enableAllCounterCups)
	{
		if (!ActivateCupConfiguration(cupConfigurationName, subCupConfigurationName, enableAllCounterCups))
		{
			return false;
		}
		return RunMonitorScan(mass);
	}
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// Runs a monitor scan with specified mass.
	/// </summary>
	/// <param name="mass"></param>
	/// <returns><c>True</c> if start successfull; otherwise <c>false</c></returns>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	public static bool RunMonitorScan(double? mass)
	{
		IRMSBaseCupConfigurationData cupData = Instrument.CupConfigurationDataList.GetActiveCupConfiguration();
		IRMSBaseMeasurementInfo newMeasurementInfo = 
			new IRMSBaseMeasurementInfo(
				Instrument.MeasurementInfo.ScanType,
				Instrument.MeasurementInfo.IntegrationTime,
				Instrument.MeasurementInfo.SettlingTime,
				(mass.HasValue) ? mass.Value : cupData.CollectorItemList.GetMasterCollectorItem().Mass.Value,
				cupData.CollectorItemList,
				cupData.MassCalibration
				);
		Instrument.ScanTransitionController.StartMonitoring(newMeasurementInfo);
		return true;
	}
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// Get all tune setting names from the system.
	/// </summary>
	/// <returns>A list of tune setting names.</returns>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	private static List<string> GetTunesettingNames()
	{
		// Tunesettings is a protected member from the core.
		List<string> result = new List<string>();
		TuneSettingsManager tuneSettingsManager = new TuneSettingsManager(Instrument.Id);
		tuneSettingsManager.EntryType = typeof(TuneSettings);
		result.AddRange(tuneSettingsManager.GetEntries());
		return result;
	}
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// Filter and display only a specific cup intensity.
	/// </summary>
	/// <param name="cupName"></param>
	/// <param name="resultList"></param>
	/// <returns>a double? value if success full; otherwise null.</returns>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	private static double? ReadIntensity(string cupName, List<string> resultList)
	{
		foreach (string result in resultList)
		{
			string[] singleValues = result.Split(';');
			if (singleValues.Length == 4 && singleValues[0] == cupName)
			{
				double resultValue;
				if (Double.TryParse(singleValues[3], out resultValue))
				{
					Logger.Log(LogLevel.Debug, "Parse : " + resultValue);
					return resultValue;
				}
				else
				{
					Logger.Log(LogLevel.Error, "Can't parse intensity for cup: " + cupName);
				}
			}
		}
		return null;
	}
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// Filter and display specific cup intensities.
	/// </summary>
	/// <param name="cupName"></param>
	/// <param name="resultList"></param>
	/// <returns>A List of double value if success full</returns>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	private static List<double> ReadIntensities(string cupName, List<string> resultList)
	{
		List<double> result = new List<double>();

		foreach (string resultString in resultList)
		{
			string[] singleValues = resultString.Split(';');
			if (singleValues.Length == 4 && singleValues[0] == cupName)
			{
				double resultValue;
				if (Double.TryParse(singleValues[3], out resultValue))
				{
					result.Add(resultValue);
				}
				else
				{
					Logger.Log(LogLevel.Error, "Can't parse intensity for cup: " + cupName);
				}
			}
		}
		return result;
	}
	
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// Activate or deactivate counter cups.
	/// </summary>
	/// <param name="activate">If <c>true</c> then activate all counter; otherwise deactivate the counter cups.</param>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	private static void ActivateAllCounterCups(bool activate)
	{
		IRMSBaseCupConfigurationData activeCupData = Instrument.CupConfigurationDataList.GetActiveCupConfiguration();
		foreach(IRMSBaseCollectorItem col in activeCupData.CollectorItemList)
		{
			if ((col.CollectorType == IRMSBaseCollectorType.CounterCup) && (col.Mass.HasValue == true))
			{
			    col.Active = activate;
			}
		}
	}
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// This function disconnect the core events.
	/// </summary>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	private static void InitializeIncludeScript()
	{
		PrepareScanEnviroment();
	}
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// This function disconnect the core events.
	/// </summary>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	private static void DisposeIncludeScript()
	{
		RestoreScanEnviroment();
	}
