"""Read-only, credential-free cloud transport diagnostics (Python 3.10+)."""
import argparse
import datetime
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import urlsplit


def summarize_logs(directory, pid=None):
    groups = {}
    for path in sorted(Path(directory).glob('*.log')):
        match = re.search(r'-(\d+)-t0-', path.name)
        if not match or (pid is not None and int(match[1]) != pid):
            continue
        process = match[1]
        with path.open(encoding='utf-8', errors='replace') as stream:
            for line in stream:
                if 'app_server_connection.state_changed' not in line:
                    continue
                if not re.search(r'\bhostId=durable(?:\s|$)', line):
                    continue
                stamp = re.search(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)', line)
                state = re.search(r'\bnext=(connected|connecting|disconnected|error)\b', line)
                initialized = re.search(r'\binitialized=(true|false)\b', line)
                if not stamp or not state or not initialized:
                    continue
                try:
                    moment = datetime.datetime.fromisoformat(stamp[0].replace('Z', '+00:00'))
                except ValueError:
                    continue
                record = {'timestamp': moment.isoformat(), 'state': state[1],
                          'initialized': initialized[1] == 'true'}
                groups.setdefault(process, []).append((moment, record))
    result = {}
    for process, events in groups.items():
        events.sort(key=lambda item: item[0])
        result[process] = {'transition_count': len(events),
                          'ever_initialized': any(e[1]['initialized'] for e in events),
                          'latest_observed': events[-1][1]}
    return {'processes': result, 'note': 'Historical observations only; verify a current native request.'}


def validate_probe(url, proxy, target_ip=None):
    target = urlsplit(url)
    if (target.scheme != 'https' or not target.hostname or target.username is not None
            or target.password is not None or target.query or target.fragment
            or target.path not in ('', '/') or target.port not in (None, 443)
            or not re.fullmatch(r'[A-Za-z0-9.-]+', target.hostname)):
        raise ValueError('Target must be an HTTPS hostname with root path, no credentials, query or fragment, port 443.')
    local = urlsplit(proxy)
    try:
        loopback = local.hostname == 'localhost' or ipaddress.ip_address(local.hostname).is_loopback
    except ValueError:
        loopback = False
    if (local.scheme not in ('http', 'socks5h') or not loopback or not local.port
            or local.username is not None or local.password is not None
            or local.path not in ('', '/') or local.query or local.fragment):
        raise ValueError('Proxy must be HTTP or SOCKS5H on loopback with an explicit port and no credentials.')
    if target_ip:
        address = ipaddress.ip_address(target_ip)
        if address.version != 4 or not address.is_global:
            raise ValueError('Target override must be a freshly verified public IPv4 address.')
    return target.hostname


def probe(url, proxy, target_ip=None, timeout=10):
    hostname = validate_probe(url, proxy, target_ip)
    if not 1 <= timeout <= 30:
        raise ValueError('Timeout must be between 1 and 30 seconds.')
    curl = shutil.which('curl.exe') or shutil.which('curl')
    if not curl:
        raise ValueError('curl is required for network probes.')
    results = {}
    for route in ('direct', 'proxy'):
        args = [curl, '--disable', '--silent', '--show-error', '--head', '--output', os.devnull,
                '--max-time', str(timeout), '--write-out',
                '%{http_code}\n%{remote_ip}\n%{time_connect}\n%{time_appconnect}\n']
        args += ['--noproxy', '*'] if route == 'direct' else ['--proxy', proxy, '--noproxy', '']
        if target_ip:
            args += ['--connect-to', f'{hostname}:443:{target_ip}:443']
        args += ['--url', url]
        try:
            run = subprocess.run(args, capture_output=True, text=True, timeout=timeout + 3)
            fields = run.stdout.splitlines()
            code = int(fields[0]) if fields and re.fullmatch(r'\d{3}', fields[0]) else 0
            try:
                peer = str(ipaddress.ip_address(fields[1]))
            except (ValueError, IndexError):
                peer = None
            results[route] = {'curl_exit_code': run.returncode, 'http_code': code, 'peer_ip': peer,
                              'verified_http_response': run.returncode == 0 and code > 0}
        except subprocess.TimeoutExpired:
            results[route] = {'timed_out': True, 'verified_http_response': False}
    return {'hostname': hostname, 'routes': results,
            'note': 'HTTP reachability does not establish authenticated WebSocket or task success.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    logs = commands.add_parser('logs')
    logs.add_argument('--directory', type=Path, required=True)
    logs.add_argument('--pid', type=int)
    network = commands.add_parser('probe')
    network.add_argument('--url', required=True)
    network.add_argument('--proxy', required=True)
    network.add_argument('--target-ip')
    network.add_argument('--timeout', type=int, default=10)
    args = parser.parse_args()
    try:
        if args.command == 'logs':
            if not args.directory.is_dir():
                parser.error('Log directory does not exist.')
            result = summarize_logs(args.directory, args.pid)
        else:
            result = probe(args.url, args.proxy, args.target_ip, args.timeout)
    except ValueError as error:
        parser.error(str(error))
    except OSError:
        parser.error('Could not read the selected files or execute curl; check local permissions.')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
