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


# Expecting a dict of name : ips
def get_results_dict(destinations):
    results = {}
    for name, ip in destinations.items():
        results[(name, ip)] = ping(ip, count=1)
    return results


def get_results(destinations):
    results = {}
    for ip in destinations:
        results[ip] = ping(ip, count=1)
    return results


def transform_points(ip_results):
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
parser.add_argument('destinations', nargs='+')
args = parser.parse_args()

upload_data(
    args.influxdb_host, args.influxdb_port, args.influxdb_user, args.influxdb_password, args.influxdb_database,
    transform_points(get_results(args.destinations)))

# test_uploading(args.influxdb_host, args.influxdb_port, args.influxdb_user, args.influxdb_password, args.influxdb_database)
# test_parsing()
# test_reading()

# TODO: Cache if upload to Grafana fails

# Nice to haves
# TODO: Include names with IP addresses
# TODO: Add SpeedTest integration, maybe this: https://github.com/sivel/speedtest-cli
# TODO: Add traceroute integration, maybe this: https://github.com/hardikvasa/webb
