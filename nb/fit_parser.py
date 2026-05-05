import fitparse
import csv
import os

# Define the name of your FIT file
fit_filename = '2025-08-11-13-06-50.fit'

# Define the names for your output CSV files
record_csv_filename = 'record_data.csv'
accel_csv_filename = 'accelerometer_data.csv'
gyro_csv_filename = 'gyroscope_data.csv'

def write_to_csv(filename, data_list, headers):
    """Writes a list of dictionaries to a CSV file using explicit headers."""
    if not data_list:
        print(f"No data to write for {filename}")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data_list)
    print(f"Successfully created {filename}")


def parse_fit_file(filepath):
    """Parses a FIT file and extracts record, accelerometer, and gyroscope data."""
    if not os.path.exists(filepath):
        print(f"Error: File not found at {filepath}")
        return

    fitfile = fitparse.FitFile(filepath)

    record_data = []
    accelerometer_data = []
    gyroscope_data = []
    
    # Define the final, correct headers for our CSVs
    record_headers = set(['timestamp'])
    accel_headers = ['timestamp', 'sample_index', 'accel_x', 'accel_y', 'accel_z']
    gyro_headers = ['timestamp', 'sample_index', 'gyro_x', 'gyro_y', 'gyro_z']

    print("Starting final data extraction...")

    for message in fitfile.get_messages(['record', 'accelerometer_data', 'gyroscope_data']):
        
        if message.name == 'record':
            record = message.get_values()
            record_data.append(record)
            record_headers.update(record.keys())

        elif message.name == 'accelerometer_data':
            message_values = message.get_values()
            
            # **FIX 1: Use the correct field names found by the inspector**
            x_key, y_key, z_key = 'calibrated_accel_x', 'calibrated_accel_y', 'calibrated_accel_z'
            
            x_values = message_values.get(x_key)
            
            # **FIX 2: Check for both list and tuple data types**
            if isinstance(x_values, (list, tuple)):
                y_values = message_values.get(y_key)
                z_values = message_values.get(z_key)
                for i in range(len(x_values)):
                    accelerometer_data.append({
                        'timestamp': message_values.get('timestamp'),
                        'sample_index': i,
                        'accel_x': x_values[i],
                        'accel_y': y_values[i],
                        'accel_z': z_values[i],
                    })

        elif message.name == 'gyroscope_data':
            message_values = message.get_values()
            
            # **FIX 1: Use the correct field names**
            x_key, y_key, z_key = 'calibrated_gyro_x', 'calibrated_gyro_y', 'calibrated_gyro_z'

            x_values = message_values.get(x_key)
            
            # **FIX 2: Check for both list and tuple**
            if isinstance(x_values, (list, tuple)):
                y_values = message_values.get(y_key)
                z_values = message_values.get(z_key)
                for i in range(len(x_values)):
                     gyroscope_data.append({
                        'timestamp': message_values.get('timestamp'),
                        'sample_index': i,
                        'gyro_x': x_values[i],
                        'gyro_y': y_values[i],
                        'gyro_z': z_values[i],
                    })

    print("Finished processing messages.")

    write_to_csv(record_csv_filename, record_data, sorted(list(record_headers)))
    write_to_csv(accel_csv_filename, accelerometer_data, accel_headers)
    write_to_csv(gyro_csv_filename, gyroscope_data, gyro_headers)

# Run the final parser
parse_fit_file(fit_filename)