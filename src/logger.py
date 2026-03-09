import json
import csv
import time
import os

class ArtisanLogger:
    def __init__(self, output_dir='.'):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def save_csv(self, time_data, et_data, bt_data, filename_prefix="roast"):
        """Saves raw data to a CSV file."""
        if not time_data:
            return None

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"{filename_prefix}_{timestamp}.csv")
        
        try:
            with open(filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Time(s)', 'ET(°C)', 'BT(°C)'])
                for t, et, bt in zip(time_data, et_data, bt_data):
                    writer.writerow([round(t, 2), et, bt])
            return filename
        except Exception as e:
            print(f"Error saving CSV: {e}")
            return None

    def save_alog(self, time_data, et_data, bt_data, title="Artisan-Lite Roast"):
        """
        Saves data to an Artisan-compatible .alog (JSON) file.
        Note: The actual Artisan .alog format is complex and contains many 
        configuration settings and events. This is a minimal structural recreation
        to allow importing curves into the main Desktop app.
        """
        if not time_data:
            return None

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"roast_{timestamp}.alog")

        # Convert simple list format to Artisan's internal curve arrays
        # Artisan generally uses floating point arrays for time (T-axis) and values (Y-axis)
        
        alog_data = {
            "title": title,
            "roaster": "Custom Modbus Gateway (Artisan-Lite)",
            "time1": time_data,
            "temp1": bt_data, # Convention: temp1 is often BT
            "time2": time_data,
            "temp2": et_data, # Convention: temp2 is often ET
            "events": [],     # Empty for now (Charge, Drop, etc. can be added later)
            "phases": {},
            "computed": {}
        }

        try:
            with open(filename, 'w') as file:
                json.dump(alog_data, file, indent=2)
            return filename
        except Exception as e:
            print(f"Error saving ALOG: {e}")
            return None
