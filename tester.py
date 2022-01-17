from pythonping import ping
import pprint
from influxdb import InfluxDBClient
import argparse
import os

# Upload to InfluxDB
def upload_data(host, port, user, password, dbname, data, lame_duck=False):
    print('Uploading this data:\n')
    pprint.pprint(data)
    print('{}@{}:{}/{}'.format(user, host, port, dbname))
    client = InfluxDBClient(host, port, user, password, dbname, ssl=True, verify_ssl=False)
    if not lame_duck:
        return client.write_points(data)
    else:
        print('Lame duck mode NOT SENDING DATA')
    return None


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
parser.add_argument('--device', help='Every device should be unique')
parser.add_argument('--ssid', default=None, help='If none will try to discover it using "iwgetid"')
parser.add_argument('--device_area', help='Up to anyone how to define this, represents grouping "above" device')
parser.add_argument('--add_dns_destination', type=bool, default=False,
                    help='adds the local DNS as a ping destination (usually ends up being the gateway)')
parser.add_argument('--lame_duck', type=bool, default=False,
                    help='Do not actually post the results to influxDB')
parser.add_argument('destinations', nargs='+')
args = parser.parse_args()

if args.add_dns_destination:
    import dns.resolver  # doing this here for backwards compatibility if not installed
    args.destinations.append(dns.resolver.Resolver().nameservers[0])


if args.ssid is None:
    # Linux / Raspberry Pi
    ssid = os.popen("iwgetid -r").read()
    if len(ssid) > 0:
        args.ssid = ssid
    else:
        # Try Mac / OSX
        ssid = os.popen("/System/Library/PrivateFrameworks/Apple80211.framework/Resources/airport -I  | awk -F' SSID: '  '/ SSID: / {print $2}'").read().strip()
        if len(ssid) > 0:
            args.ssid = ssid

upload_data(
    args.influxdb_host, args.influxdb_port, args.influxdb_user, args.influxdb_password, args.influxdb_database,
    transform_points(get_results(args.destinations), args.device, args.ssid, args.device_area),
    args.lame_duck)

# Must haves
# TODO: Cache if upload to Grafana fails

# Nice to haves
# TODO: Gather visible SSIDs automatically
# TODO: Add SpeedTest integration, maybe this: https://github.com/sivel/speedtest-cli
# TODO: Add traceroute integration, maybe this: https://github.com/hardikvasa/webb
