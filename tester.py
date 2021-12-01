from pythonping import ping
import pprint
from influxdb import InfluxDBClient
import argparse

# Upload to InfluxDB
def upload_data(host, port, user, password, dbname, data):
    print('Uploading this data:\n')
    pprint.pprint(data)
    print('{}@{}:{}/{}'.format(user, host, port, dbname))
    client = InfluxDBClient(host, port, user, password, dbname, ssl=True, verify_ssl=False)
    return client.write_points(data)


def get_results(destinations):
    results = {}
    for ip in destinations:
        results[ip] = ping(ip, count=1)
    return results


def transform_points(ip_results, device, ssid, device_area):
    points = []
    for ip, results in ip_results.items():
        for result in results:
            points.append(
                {
                    'measurement': 'ping',
                    'tags': {
                        'ip': ip,
                        'success': result.success,
                        'error_message': result.error_message,
                        'device': device,
                        'ssid': ssid,
                        'device_area': device_area,
                    },
                    'fields': {
                        'time_elapsed_ms': float(result.time_elapsed_ms)
                    }
                }
            )

    return points

parser = argparse.ArgumentParser()
parser.add_argument('--influxdb_host')
parser.add_argument('--influxdb_port', type=int, default=8086)
parser.add_argument('--influxdb_user')
parser.add_argument('--influxdb_password')
parser.add_argument('--influxdb_database')
parser.add_argument('--device')  # every device should be unique
parser.add_argument('--ssid')  # every device should be unique
parser.add_argument('--device_area')  # up to anyone how to define this
parser.add_argument('destinations', nargs='+')
args = parser.parse_args()

upload_data(
    args.influxdb_host, args.influxdb_port, args.influxdb_user, args.influxdb_password, args.influxdb_database,
    transform_points(get_results(args.destinations), args.device, args.ssid, args.device_area))

# Must haves
# TODO: Cache if upload to Grafana fails
# TODO: Gather connected SSID automatically

# Nice to haves
# TODO: Add SpeedTest integration, maybe this: https://github.com/sivel/speedtest-cli
# TODO: Add traceroute integration, maybe this: https://github.com/hardikvasa/webb
