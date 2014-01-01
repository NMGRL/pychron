// RegisterSystemAssembly: System.dll
// RegisterSystemAssembly: System.XML.dll
// RegisterAssembly: SpectrumLibrary.dll
// ------------------------------------------------------------------------------------------------------------------------------------------
using System.Collections.Generic;
using System.ComponentModel;
using System.Text;
using Thermo.Imhotep.SpectrumLibrary;
using Thermo.Imhotep.Util;
//-------------------------------------------------------------------------------------------------------------------------------------------------------------
public class SampleFunctionScript
{
	public static IRMSBaseCore Instrument;
	public static IRMSBaseMeasurementInfo m_restoreMeasurementInfo;

	//InsertScript: Scripts\Noble Gas\SampleFunctionIncludeScript.cs		

	public static void Main()
	{
		Instrument = ArgusMC;
		m_restoreMeasurementInfo = ArgusMC.MeasurementInfo;

		InitializeIncludeScript();

		//RunGetCupConfigurationInfosExample();
		//RunGetTuneSettingNamesExample();
		//RunGetSetMagnetPositionExample();
		//RunGetSetHVExample();
		//RunSetTuneSettingsExample();
		//RunGetSetAllDetectorParametersExample();
		//RunIONGaugeOnOffExample();
		//RunSetMassExample();

		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		// Scan example section, please only enable one function in these section.
		// If the boolean parameter in the follwing functions are set to true then all counter cups in measurements are activated; otherwise deactivated.		
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		//RunMonitorScanWithCupConfigurationExample(true);
		//RunMonitorScanWithCupConfigurationAndMassExample(true);
		//RunSweepScanWithCupConfigurationExample(true);
		//RunSweepScanUseSelectedCupConfigurationExample(true);
		//RunSingleScanWithCupConfigurationExample(true);
		//RunSingleScanUseSelectedCupConfigurationExample(true);
	
		//RunChangeIntegrationTimeForMonitorScanExample();
	}
	
	private static void RunGetCupConfigurationInfosExample()
	{
		List<string> cupConfigurationNames = GetCupConfigurations();
		List<string> subCupConfigurationNames = null;
		if (cupConfigurationNames == null)
		{
			return;
		}
		foreach (string cupConfigurationName in cupConfigurationNames)
		{
			subCupConfigurationNames = GetSubCupConfigurations(cupConfigurationName);
			if (subCupConfigurationNames == null)
			{
				return;
			}
			foreach (string subCupConfigurationName in subCupConfigurationNames)
			{
				Logger.Log(LogLevel.UserInfo, String.Format("Cup Configuration / Sub Cup Configuration '{0}' / '{1}'  .", cupConfigurationName, subCupConfigurationName));
			}
		}
	}

	private static void RunMonitorScanWithCupConfigurationExample(bool activateCounterCups)
	{
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		// Runs the monitor scan with the master cup mass from the specified cup configuration and activate or deactivate the counter cups.
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		RunMonitorScan("Argon MC L1", "Full", activateCounterCups);
	}
	
	private static void RunMonitorScanWithCupConfigurationAndMassExample(bool activateCounterCups)
	{
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		// Runs the monitor scan with a specific mass and the currently activated cup configuration and activate or deactivate the counter cups.
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		RunMonitorScan("Argon MC L1", "Full", 20.0, activateCounterCups);
	}

	private static void RunSweepScanWithCupConfigurationExample(bool activateCounterCups)
	{
		List<string> result = Sweep("Argon MC L1", "Full", activateCounterCups, null, 20.0, 20.6, 0.1, 1048, 100);
		if (result == null)
		{
			Logger.Log(LogLevel.UserError, "Could not request sweep data.");
		}
		else
		{
			foreach (string data in result)
			{
				Logger.Log(LogLevel.UserInfo, data);
			}
		}
		RestoreScanEnviroment();
	}
	
	private static void RunSweepScanUseSelectedCupConfigurationExample(bool activateCounterCups)
	{
		ActivateAllCounterCups(activateCounterCups);
		
		List<string> result = Sweep(null, 5.0, 6.0, 0.1, 524.2, 100);
		if (result == null)
		{
			Logger.Log(LogLevel.UserError, "Could not request sweep data.");
		}
		else
		{
			foreach (string data in result)
			{
				Logger.Log(LogLevel.UserInfo, data);
			}
		}
		RestoreScanEnviroment();
	}
	
	private static void RunSingleScanWithCupConfigurationExample(bool activateCounterCups)
	{
		List<string> result = Scan("Argon MC L1", "Full", activateCounterCups, null, 11.11, 2097, 100);
		if (result == null)
		{
			Logger.Log(LogLevel.UserError, "Could not request sweep data.");
		}
		else
		{
			foreach (string data in result)
			{
				Logger.Log(LogLevel.UserInfo, data);
			}
		}
		RestoreScanEnviroment();
	}
	
	private static void RunSingleScanUseSelectedCupConfigurationExample(bool activateCounterCups)
	{
		ActivateAllCounterCups(activateCounterCups);	
		
		List<string> result = Scan(null, 40.24, 4194, 100);
		if (result == null)
		{
			Logger.Log(LogLevel.UserError, "Could not request sweep data.");
		}
		else
		{
			foreach (string data in result)
			{
				Logger.Log(LogLevel.UserInfo, data);
			}
		}
		RestoreScanEnviroment();
	}

	private static void RunGetTuneSettingNamesExample()
	{
		List<string> tuneSettingsNames = GetTunesettingNames();
		Logger.Log(LogLevel.UserInfo, String.Format("Numbers of tune settings: '{0}'.", tuneSettingsNames.Count));
		foreach (string tuneSettingName in tuneSettingsNames)
		{
			Logger.Log(LogLevel.UserInfo, String.Format("Tunesetting '{0}'.", tuneSettingName));
		}
	}
	
	private static void RunGetSetMagnetPositionExample()
	{
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		//1. Get/Set Magnet Position
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		double value = 0.0;
		if (GetParameter("Field Set", out value))
		{
			Logger.Log(LogLevel.UserInfo, String.Format("Parameter: 'Field Set' Value: '{0}'", value));
		}
		SetParameter("Field Set", value);
	}
	
	private static void RunGetSetHVExample()
	{
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		//2. Get/Set HV
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		double value = 0.0;
		if (GetParameter("Acceleration Reference Set", out value))
		{
			Logger.Log(LogLevel.UserInfo, String.Format("Parameter: 'Acceleration Reference Set' Value: '{0}'", value));
		}
		SetParameter("Acceleration Reference Set", value);
	}

	private static void RunSetTuneSettingsExample()
	{
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		//6. Get/Set all source parameters (Tune sets)
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		SetTuneSetting("Test Tunesetting For script");
	}

	private static void RunGetSetAllDetectorParametersExample()
	{
		double value = 0.0;	
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		//7. Get/Set all detector parameters (CDD gain, steering etc)
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		if (GetParameter("Deflection CDD Set", out value))
		{
			Logger.Log(LogLevel.UserInfo, String.Format("Parameter: 'Deflection CDD Set' Value: '{0}'", value));
		}
		SetParameter("Deflection CDD Set", value);

		if (GetParameter("Deflection H2 Set", out value))
		{
			Logger.Log(LogLevel.UserInfo, String.Format("Parameter: 'Deflection H2 Set' Value: '{0}'", value));
		}
		SetParameter("Deflection H2 Set", value);

		if (GetParameter("Deflection H1 Set", out value))
		{
			Logger.Log(LogLevel.UserInfo, String.Format("Parameter: 'Deflection H1 Set' Value: '{0}'", value));
		}
		SetParameter("Deflection H1 Set", value);

		if (GetParameter("Deflection AX Set", out value))
		{
			Logger.Log(LogLevel.UserInfo, String.Format("Parameter: 'Deflection AX Set' Value: '{0}'", value));
		}
		SetParameter("Deflection AX Set", value);

		if (GetParameter("Deflection L1 Set", out value))
		{
			Logger.Log(LogLevel.UserInfo, String.Format("Parameter: 'Deflection L1 Set' Value: '{0}'", value));
		}
		SetParameter("Deflection L1 Set", value);

		if (GetParameter("Deflection L2 Set", out value))
		{
			Logger.Log(LogLevel.UserInfo, String.Format("Parameter: 'Deflection L2 Set' Value: '{0}'", value));
		}
		SetParameter("Deflection L2 Set", value);

		if (GetParameter("CDD Supply Set", out value))
		{
			Logger.Log(LogLevel.UserInfo, String.Format("Parameter: 'CDD Supply Set' Value: '{0}'", value));
		}
		SetParameter("CDD Supply Set", value);
	}

	private static void RunIONGaugeOnOffExample()
	{
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------	
		//9. Turn Ion Gauge On/Off
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		//Ion gauge off
		SetParameter("Ion Gauge MS enable / disable Set", 0);
		//Ion gauge on
		SetParameter("Ion Gauge MS enable / disable Set", 1);
	}

	private static void RunChangeIntegrationTimeForMonitorScanExample()
	{
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		//8. Get/Set integration time
		//a. For monitor scan
		//	 Applicable integration times (ms) 
		//	 65.536, 131.072, 262.144, 524.288, 1048.576, 2097.152, 4194.304, 8388.608, 16777.216, 33554.432, 67108.864
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		ChangeIntegrationTimeForMonitorScan(4194.304);
	}

	private static void RunSetMassExample()
	{
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		//Set Mass
		//-------------------------------------------------------------------------------------------------------------------------------------------------------------
		RunMonitorScan(7.34);
	}

	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	/// <summary>
	/// The script changes his state to terminate.
	/// </summary>
	///-------------------------------------------------------------------------------------------------------------------------------------------------------------
	public static void Dispose()
	{
		DisposeIncludeScript();
	}
}
