import json
import re
import subprocess
from argparse import ArgumentParser

import requests

IP_PATTERN = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')


def get_parser():
    parser = ArgumentParser(description="Trace Autonomous Systems")
    parser.add_argument("target", type=str, help="Целевой хост")
    parser.add_argument("-hops", default=52, type=int, help="Максимальное значение TTL")
    parser.add_argument("-timeout", default=5, type=int, help="Таймаут ответа в секундах")
    return parser


def get_ip_info(ip):
    info = json.loads(requests.get("http://ipinfo.io/{0}/json".format(ip)).content)

    if "bogon" in info and info["bogon"]:
        return "\t bogon"

    msg = f"\t {info['country']} {info['region']} {info['city']}"
    if "org" in info and info["org"] != "":
        msg += " Organisation: {}".format(info["org"])
    if "loc" in info and info["loc"] != "":
        msg += " Location: {}".format(info["loc"])
    return msg


def get_trace(ip: str, max_hops: int, timeout: int):
    trace = subprocess.Popen(['tracert', '-d', '-w', str(timeout), '-h', str(max_hops), ip], stdout=subprocess.PIPE)
    skipped_lines = 0

    for line in iter(trace.stdout.readline, b''):
        if skipped_lines < 3:
            skipped_lines += 1
            continue

        ip = re.search(IP_PATTERN, line.decode('866'))
        if ip is not None:
            yield ip.group(0)


def trace_as(ip: str, max_hops: int, timeout: int):
    for ttl, ip in enumerate(get_trace(ip, max_hops, timeout), start=1):
        yield (f"{ttl} "
               f'{ip:<{20}}'
               f"{get_ip_info(ip)}")


def main():
    args = get_parser().parse_args()

    for message in trace_as(args.target, args.hops, args.timeout):
        print(message)


if __name__ == '__main__':
    main()
