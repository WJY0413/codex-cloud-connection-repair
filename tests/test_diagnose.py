import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/codex-cloud-connection-repair/scripts/diagnose.py'
spec = importlib.util.spec_from_file_location('diagnose', SCRIPT)
diagnose = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnose)


class LogTests(unittest.TestCase):
    def test_rotation_pid_and_redaction(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def write(name, time, state, initialized):
                (root / name).write_text(f'{time} app_server_connection.state_changed hostId=durable next={state} initialized={initialized} connectionError=SECRET_TOKEN\n', encoding='utf-8')
            write('desktop-123-t0-9.log', '2026-09-30T07:30:00Z', 'connected', 'true')
            write('desktop-123-t0-1.log', '2026-09-30T08:30:00Z', 'disconnected', 'false')
            write('desktop-456-t0-0.log', '2026-09-30T09:30:00Z', 'connected', 'true')
            result = diagnose.summarize_logs(root, 123)
            self.assertEqual(set(result['processes']), {'123'})
            process = result['processes']['123']
            self.assertEqual(process['transition_count'], 2)
            self.assertTrue(process['ever_initialized'])
            self.assertEqual(process['latest_observed']['state'], 'disconnected')
            self.assertNotIn('SECRET', json.dumps(result))
            self.assertEqual(len(diagnose.summarize_logs(root)['processes']), 2)

    def test_empty(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(diagnose.summarize_logs(folder)['processes'], {})


class ProbeTests(unittest.TestCase):
    def test_validation(self):
        for url in ('http://example.com', 'https://user:secret@example.com',
                    'https://example.com/?token=secret', 'https://example.com/private', 'https://example.com:444/'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                diagnose.validate_probe(url, 'http://127.0.0.1:8888')
        for proxy in ('http://example.com:8080', 'http://user:secret@localhost:8080', 'http://localhost', 'file:///tmp/proxy'):
            with self.subTest(proxy=proxy), self.assertRaises((ValueError, TypeError)):
                diagnose.validate_probe('https://example.com', proxy)
        with self.assertRaises(ValueError):
            diagnose.validate_probe('https://example.com', 'http://localhost:8888', '127.0.0.1')

    @patch.object(diagnose.shutil, 'which', return_value='curl')
    @patch.object(diagnose.subprocess, 'run')
    def test_routes_preserve_tls_and_do_not_leak_stderr(self, run, which):
        run.return_value = subprocess.CompletedProcess([], 0, '403\n1.1.1.1\n0.1\n0.2\n', 'SECRET_TOKEN')
        result = diagnose.probe('https://example.com/', 'http://127.0.0.1:8888', '1.1.1.1')
        self.assertEqual(run.call_count, 2)
        direct, proxy = [call.args[0] for call in run.call_args_list]
        self.assertEqual(direct[1], '--disable')
        self.assertIn('*', direct)
        self.assertIn('--proxy', proxy)
        self.assertEqual(proxy[proxy.index('--noproxy') + 1], '')
        for args in (direct, proxy):
            self.assertIn('example.com:443:1.1.1.1:443', args)
            self.assertNotIn('--insecure', args)
        self.assertTrue(result['routes']['proxy']['verified_http_response'])
        self.assertNotIn('SECRET', json.dumps(result))

    @patch.object(diagnose.shutil, 'which', return_value='curl')
    @patch.object(diagnose.subprocess, 'run')
    def test_tls_failure_is_not_success(self, run, which):
        run.return_value = subprocess.CompletedProcess([], 60, '000\n\n0\n0\n', 'certificate error')
        self.assertFalse(diagnose.probe('https://example.com', 'socks5h://localhost:8888')['routes']['proxy']['verified_http_response'])


if __name__ == '__main__':
    unittest.main()
