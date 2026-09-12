"""Offline query/admission regressions, never a host-observation PASS."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from axiom_validation import no_hook_native_observation as native
from axiom_validation import no_hook_clarification as replies
from axiom_validation import no_hook_discovery as discovery
from tests import test_no_hook_native_observation as support

ROOT = Path(__file__).resolve().parents[1]


class EmptyDiscoveryWindowTests(unittest.TestCase):
    def setUp(self):
        self.helper = support.NativeObservationTests()
        self.helper.setUp()
        self.addCleanup(self.helper.doCleanups)
        self.parent = self.helper.parent

    def prepared(self):
        # As in the existing fixed-window fixtures, only the synthetic reader
        # sees an unconsumed registration. The checked-in actual result and
        # production admission remain closed and are tested separately below.
        actual_read = native._read
        def synthetic_registration(path, *args, **kwargs):
            data = actual_read(path, *args, **kwargs)
            if path in (ROOT / native.HISTORY_RELATIVE, ROOT / replies.HISTORY):
                history = json.loads(data)
                history['nativeEmptyDiscoveryAcceptance']['results'] = []
                return native._bytes(history)
            return data
        for module in (native, replies):
            registration = patch.object(module, '_read', side_effect=synthetic_registration)
            registration.start()
            self.addCleanup(registration.stop)
        prior, runner, calls = self.helper._prepared_runner()
        old = json.loads((prior / native.STATE_NAME).read_bytes())
        previous = self.parent / native.HOST_CONTEXT_ACCEPTANCE['routingRunName']
        paths = native._case_paths(previous, 10)
        paths['workspace'].mkdir(parents=True)
        paths['home'].mkdir()
        auth = paths['home'] / native.AUTH_FILE_NAME
        auth.write_bytes(b'PUBLIC-SYNTHETIC-NORMAL-SOURCE')
        auth.chmod(0o600)
        meta = auth.stat()
        native._exclusive(native._auth_owner(previous, 10), native._bytes({
            'ordinal': 10, 'device': meta.st_dev, 'inode': meta.st_ino}))
        queried = []
        def query(paths, executable, marketplace, installed, definition):
            # Only the native RPC is simulated. Scope, preparation, input
            # materialization, auth ownership and result validators are real.
            scope = discovery.query_scope(paths, executable, marketplace, installed, definition)
            self.assertFalse((paths['home'] / native.AUTH_FILE_NAME).exists())
            queried.append(paths['workspace'])
            skills = ([{'name': 'synthetic-public-helper', 'description': 'Test metadata.',
                       'path': str(paths['discovery'] / 'helper/SKILL.md'),
                       'scope': 'user', 'enabled': True}] if paths['discovery'].exists() else [])
            receipt = {'status': 'verified', 'queryStarts': 1, 'scope': scope,
                       'returnCode': 0, 'threadStarts': 0, 'turnStarts': 0, 'forceReload': True,
                       'response': {'id': 2, 'result': {'data': [{
                           'cwd': str(paths['workspace']), 'skills': skills, 'errors': []}]}}}
            native._exclusive(paths['case'] / 'discovery-query.json', native._bytes(receipt))
            return receipt
        self.query = query
        run = self.parent / native.EMPTY_DISCOVERY_ACCEPTANCE['routingRunName']
        with patch.object(native, '_revision_four_auth_source', return_value=old), \
             patch.object(discovery, 'query_once', side_effect=query):
            native.prepare_fixed_acceptance(ROOT, run, previous, self.parent/'bundle',
                authorize_install=True, authorize_copy=True, empty_discovery=True, runner=runner)
        return run, runner, calls, queried

    def test_only_six_routing_states_are_prepared_and_history_stays_closed(self):
        run, _, calls, queried = self.prepared()
        state = native._state(ROOT, run, empty_discovery=True)[1]
        self.assertEqual([x['ordinal'] for x in state['cases']], list(range(11,17)))
        self.assertEqual(len(queried), 6)
        self.assertEqual(calls, [])
        self.assertTrue(all(not native._case_paths(run, i)['case'].exists() for i in range(1,11)))
        self.assertEqual(native.empty_discovery_attempt_history(ROOT)['attempts'], 117)
        self.assertFalse(native._case_paths(run, 11)['discovery'].exists())
        self.assertFalse(native._case_paths(run, 11)['package'].exists())
        self.assertEqual([i for i in range(11,17) if
                         (native._case_paths(run,i)['home']/native.AUTH_FILE_NAME).exists()], [11])
        with patch.object(native.subprocess, 'Popen', side_effect=AssertionError('real client')):
            for flags in ({}, {'revision_four': True}, {'host_context': True}):
                with self.assertRaises(native.NativeObservationError):
                    native.prepare_fixed_acceptance(ROOT, self.parent/'never', self.parent/'old',
                        self.parent/'bundle', authorize_install=True, authorize_copy=True, **flags)

    def run_window(self, *, mismatch=False):
        run, runner, calls, _ = self.prepared()
        def invoke(argv, **kwargs):
            if 'exec' not in argv:
                return runner(argv, **kwargs)
            capture = runner(argv, **{**kwargs, 'line_callback': None})
            if mismatch:
                events = [json.loads(x) for x in capture['stdout'].splitlines()]
                message = next(e['item'] for e in events if e.get('item',{}).get('type')=='agent_message')
                answer = json.loads(message['text'])
                answer['usingAxiomFrontDoorObserved'] = not answer['usingAxiomFrontDoorObserved']
                message['text'] = json.dumps(answer)
                Path(argv[argv.index('--output-last-message')+1]).write_text(message['text'])
                capture['stdout'] = b''.join(support.event(e) for e in events)
            for line in capture['stdout'].splitlines():
                kwargs['line_callback'](line)
            return capture
        result = native.run_native_observation(ROOT, run, authorize_model_calls=True,
            assessment_batch=True, reuse_test_auth=True, empty_discovery=True, process_runner=invoke)
        return run, result, calls, runner

    def test_a11_semantic_failure_stops_remaining_cases_and_reply_handoff(self):
        run, result, calls, runner = self.run_window(mismatch=True)
        self.assertEqual(calls, [11])
        self.assertEqual(result['cumulativeAttemptCount'], 118)
        self.assertEqual([x['status'] for x in result['caseResults']], ['FAIL']+['NOT-RUN']*5)
        self.assertEqual(native.validate_native_result(result, ROOT), [])
        self.assertFalse((native._case_paths(run,12)['home']/native.AUTH_FILE_NAME).exists())
        target = self.parent / native.EMPTY_DISCOVERY_ACCEPTANCE['clarificationRunName']
        with patch.object(replies, '_login', side_effect=AssertionError('later handoff')):
            with self.assertRaises(native.NativeObservationError):
                replies.prepare(ROOT, target, run, bundle_root=self.parent/'bundle',
                    authorized=True, empty_discovery=True, runner=runner)
        self.assertFalse(target.exists())

    def test_six_case_completion_never_claims_a_new_sixteen_case_host_pass(self):
        run, result, calls, runner = self.run_window()
        self.assertEqual(calls, list(range(11,17)))
        self.assertEqual(result['cumulativeAttemptCount'], 123)
        self.assertEqual([x['status'] for x in result['caseResults']], ['PASS']*6)
        self.assertEqual(result['runMode'], 'simulated')
        self.assertFalse(result['hostClaim'])
        self.assertEqual(native.validate_native_result(result, ROOT), [])
        self.assertEqual(native.completed_fixed_routing(ROOT, run, simulated=True, empty_discovery=True)[1]['attempts'],123)
        changed = copy.deepcopy(result)
        changed['caseResults'][0]['nativeDiscovery']['skillCount'] = 8
        self.assertTrue(native.validate_native_result(changed, ROOT))
        with self.assertRaises(native.NativeObservationError):
            native.run_native_observation(ROOT, run, authorize_model_calls=True,
                assessment_batch=True, reuse_test_auth=True, empty_discovery=True, process_runner=runner)

    def test_scope_drift_stops_before_model_or_authentication_handoff(self):
        run, runner, calls, _ = self.prepared()
        (native._case_paths(run,11)['home']/'environments.toml').write_text('PUBLIC SYNTHETIC DRIFT')
        result = native.run_native_observation(ROOT, run, authorize_model_calls=True,
            assessment_batch=True, reuse_test_auth=True, empty_discovery=True, process_runner=runner)
        self.assertEqual(calls, [])
        self.assertEqual(result['attemptCount'],0)
        self.assertEqual(result['cumulativeAttemptCount'],117)
        self.assertEqual([x['status'] for x in result['caseResults']], ['INCOMPLETE']+['NOT-RUN']*5)

    def test_recorded_actual_failure_keeps_the_window_closed_before_auth_or_client(self):
        binding = native._fixed_result_binding(ROOT, empty_discovery=True)
        self.assertIsNotNone(binding)
        data = (ROOT / binding['path']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), binding['sha256'])
        result = json.loads(data)
        self.assertEqual(native.validate_native_result(result, ROOT), [])
        self.assertEqual(result['cumulativeAttemptCount'], 118)
        self.assertEqual([x['status'] for x in result['caseResults']], ['FAIL']+['NOT-RUN']*5)
        with patch.object(native.subprocess, 'Popen', side_effect=AssertionError('client started')), \
             patch.object(native, '_revision_four_auth_source', side_effect=AssertionError('auth handoff')):
            with self.assertRaisesRegex(native.NativeObservationError, 'already recorded'):
                native.prepare_fixed_acceptance(ROOT, self.parent/'never', self.parent/'old',
                    self.parent/'bundle', authorize_install=True, authorize_copy=True, empty_discovery=True)
