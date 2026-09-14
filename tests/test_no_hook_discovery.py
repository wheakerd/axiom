"""No-model checks for native discovery response facts and compatibility relay."""

from dataclasses import dataclass
import copy
from pathlib import Path
import unittest

from axiom_validation.no_hook_discovery import (
    DiscoveryExchange, DiscoveryQueryError, checked_discovery_entry, relay_empty_discovery,
)


@dataclass(frozen=True)
class Material:
    prompt_bytes: bytes = b"Original assessment.\nUser request:\nExplain the project.\n"
    prompt_sha256: str = "unchanged"


class NativeDiscoveryRelayTests(unittest.TestCase):
    def response(self):
        return {"id": 2, "result": {"data": [
            {"cwd": "/synthetic/project", "skills": [], "errors": []}]}}

    def check(self, response):
        return checked_discovery_entry(response, cwd=Path("/synthetic/project"), request_id=2)

    def test_documented_unauthenticated_notification_is_not_a_query_response(self):
        exchange = DiscoveryExchange(Path('/synthetic/project'), Path('/synthetic/home'))
        requests = exchange.receive({'id': 1, 'result': {'codexHome': '/synthetic/home'}})
        self.assertEqual([r['method'] for r in requests], ['initialized', 'skills/list'])
        self.assertEqual(requests[1]['params'], {'cwds': ['/synthetic/project'], 'forceReload': True})
        self.assertEqual(exchange.receive({'method': 'account/updated', 'emittedAtMs': 0, 'params': {
            'authMode': None, 'planType': None}}), [])
        self.assertIsNone(exchange.entry)
        exchange.receive(self.response())
        self.assertEqual(exchange.entry['skills'], [])
        self.assertEqual(exchange.unauthenticated_notifications, 1)

    def test_scope_drift_config_warnings_and_unexpected_authority_stop(self):
        for event in ({'method': 'skills/changed', 'params': {}},
                      {'method': 'configWarning', 'params': {'summary': 'invalid config'}},
                      {'method': 'account/updated', 'params': {'authMode': 'chatgpt', 'planType': None}},
                      {'id': 3, 'method': 'thread/start', 'params': {}}):
            exchange = DiscoveryExchange(Path('/synthetic/project'), Path('/synthetic/home'))
            exchange.receive({'id': 1, 'result': {'codexHome': '/synthetic/home'}})
            with self.subTest(event=event), self.assertRaises(DiscoveryQueryError):
                exchange.receive(event)
            self.assertIsNone(exchange.entry)

    def test_initial_remote_status_only_accepts_disabled_local_state(self):
        for status in ("disabled", "connecting", "connected", "errored"):
            exchange = DiscoveryExchange(Path('/synthetic/project'), Path('/synthetic/home'))
            exchange.receive({'id': 1, 'result': {'codexHome': '/synthetic/home'}})
            event = {'method': 'remoteControl/status/changed', 'emittedAtMs': 0, 'params': {
                'status': status, 'serverName': 'synthetic', 'installationId': 'synthetic',
                'environmentId': None}}
            if status == 'disabled':
                self.assertEqual(exchange.receive(event), [])
                self.assertEqual(exchange.disabled_remote_notifications, 1)
                event['params']['environmentId'] = 'unexpected-enrollment'
            with self.assertRaises(DiscoveryQueryError):
                exchange.receive(event)
            self.assertIsNone(exchange.entry)

    def test_notification_envelope_is_required_and_does_not_accept_a_request(self):
        exchange = DiscoveryExchange(Path('/synthetic/project'), Path('/synthetic/home'))
        exchange.receive({'id': 1, 'result': {'codexHome': '/synthetic/home'}})
        base = {'method': 'account/updated', 'params': {'authMode': None, 'planType': None}}
        for fields in ({}, {'emittedAtMs': True}, {'emittedAtMs': -1},
                       {'emittedAtMs': 0, 'id': 5}, {'emittedAtMs': 2**63}):
            with self.assertRaises(DiscoveryQueryError):
                exchange.receive({**base, **fields})

    def test_native_empty_facts_are_explicitly_compatibility_delivered(self):
        original = Material()
        material = relay_empty_discovery(original, self.check(self.response()))
        self.assertIn(b'{"skills":[],"errors":[]}', material.prompt_bytes)
        self.assertIn(b"relayed by the compatibility layer", material.prompt_bytes)
        self.assertEqual(material.prompt_bytes.partition(b"\nUser request:\n")[2],
                         original.prompt_bytes.partition(b"\nUser request:\n")[2])
        for forbidden in (b"unavailable", b"selectedRoutes", b"caseId", b"pluginState",
                          b"/synthetic/project", b"SKILL.md"):
            self.assertNotIn(forbidden, material.prompt_bytes)

    def test_nonempty_including_disabled_entries_preserves_input_object(self):
        for enabled in (True, False):
            with self.subTest(enabled=enabled):
                response = self.response()
                response["result"]["data"][0]["skills"] = [{
                    "name": "arbitrary-tool", "description": "Public helper.",
                    "path": "/synthetic/skills/arbitrary-tool/SKILL.md",
                    "scope": "user", "enabled": enabled}]
                material = Material()
                self.assertIs(relay_empty_discovery(material, self.check(response)), material)

    def test_errors_in_empty_or_nonempty_catalogs_stop(self):
        for skills in ([], [{"name": "arbitrary-tool"}]):
            response = self.response()
            response["result"]["data"][0].update(
                skills=skills, errors=[{"path": "/synthetic/project", "message": "load failed"}])
            with self.subTest(skills=skills), self.assertRaises(DiscoveryQueryError):
                self.check(response)

    def test_missing_fields_mismatched_scope_and_invalid_shapes_stop(self):
        original = self.response()
        variants = [{"id": 2, "error": {"code": -1}}, {"id": 1, "result": original["result"]},
                    {"id": True, "result": original["result"]}, {"id": 2, "result": {}},
                    {"id": 2, "result": {"data": []}}]
        for field in ("cwd", "skills", "errors"):
            response = copy.deepcopy(original)
            del response["result"]["data"][0][field]
            variants.append(response)
        for field, value in (("cwd", "/another/project"), ("skills", {}),
                             ("errors", None), ("skills", [None])):
            response = copy.deepcopy(original)
            response["result"]["data"][0][field] = value
            variants.append(response)
        response = copy.deepcopy(original)
        response["result"]["data"].append(copy.deepcopy(response["result"]["data"][0]))
        variants.append(response)
        for response in variants:
            with self.subTest(response=response), self.assertRaises(DiscoveryQueryError):
                self.check(response)


if __name__ == "__main__":
    unittest.main()

class NativeDiscoveryProcessTests(unittest.TestCase):
    def exercise(self, mode):
        import tempfile
        from unittest.mock import MagicMock, patch
        from axiom_validation import no_hook_native_observation as native
        from axiom_validation import no_hook_discovery as discovery
        with tempfile.TemporaryDirectory(prefix='axiom-query-offline-') as folder:
            base=Path(folder)
            paths={k:base/k for k in ('case','home','workspace')}
            for path in paths.values(): path.mkdir()
            scope={'cwd':str(paths['workspace']),'overrides':[], 'environment':{}}
            process=MagicMock()
            process.poll.return_value=0
            process.returncode=0
            key=MagicMock(); key.fileobj=process.stdout
            selector=MagicMock();selector.select.return_value=[(key,1)]
            initialization={'id':1,'result':{'codexHome':str(paths['home'])}}
            reply={'id':2,'result':{'data':[{'cwd':str(paths['workspace']),'skills':[], 'errors':[]}]}}
            import json
            content=b''.join((json.dumps(x)+'\n').encode() for x in (initialization,reply))
            if mode=='late-warning':
                content+=(json.dumps({'method':'configWarning','params':{},'emittedAtMs':0})+'\n').encode()
            scopes=[scope,scope] if mode!='scope-drift' else [scope,{**scope,'cwd':'/changed'}]
            times=iter([0,30]) if mode=='timeout' else None
            with patch.object(discovery,'query_scope',side_effect=scopes), \
                 patch.object(native.legacy,'freeze_executable'), patch.object(native.legacy,'recheck_executable'), \
                 patch('subprocess.Popen',return_value=process) as started, \
                 patch('selectors.DefaultSelector',return_value=selector), \
                 patch('os.read',side_effect=[content,b'']), \
                 patch.object(native,'_close_process'), \
                 patch('time.monotonic',side_effect=(lambda: next(times)) if times else lambda:0):
                if mode=='success':
                    receipt=discovery.query_once(paths,Path('/synthetic/binary'),base,False,{})
                    self.assertEqual(receipt['response'],reply)
                    sent=b''.join(c.args[0] for c in process.stdin.write.call_args_list)
                    methods=[json.loads(x)['method'] for x in sent.splitlines()]
                    self.assertEqual(methods,['initialize','initialized','skills/list'])
                    self.assertEqual((receipt['threadStarts'],receipt['turnStarts']),(0,0))
                else:
                    with self.assertRaises(discovery.DiscoveryQueryError):
                        discovery.query_once(paths,Path('/synthetic/binary'),base,False,{})
                    receipt=json.loads((paths['case']/'discovery-query.json').read_bytes())
                    self.assertEqual(receipt['status'],'failed')
                    self.assertIsNone(receipt['response'])
                self.assertEqual(started.call_count,1)
            # The once-only marker is checked before creating another client.
            with patch.object(discovery,'query_scope',return_value=scope), \
                 patch.object(native.legacy,'freeze_executable'), \
                 patch('subprocess.Popen',side_effect=AssertionError('query retried')):
                with self.assertRaises(FileExistsError):
                    discovery.query_once(paths,Path('/synthetic/binary'),base,False,{})

    def test_complete_native_exchange_is_query_only(self):self.exercise('success')
    def test_timeout_is_not_empty_and_cannot_be_requeried(self):self.exercise('timeout')
    def test_late_warning_is_not_lost_after_skills_response(self):self.exercise('late-warning')
    def test_changed_scope_is_not_empty_success(self):self.exercise('scope-drift')
