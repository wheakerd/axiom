"""Uniform measurement/input checks and simulated one-case admission, not host PASS."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from axiom_validation import no_hook_native_observation as native
from axiom_validation import no_hook_discovery as discovery
from axiom_validation import no_hook_clarification as replies
from tests import test_no_hook_empty_discovery_window as window_support
from tests import test_no_hook_native_observation as support

ROOT = Path(__file__).resolve().parents[1]


class OutcomeSemanticsTests(unittest.TestCase):
    def setUp(self):
        self.window = window_support.EmptyDiscoveryWindowTests()
        self.window.setUp()
        self.addCleanup(self.window.doCleanups)

    def test_all_inputs_change_only_uniform_definition_and_bound_identities(self):
        old = native._outcome_prior_protocol(ROOT)
        current = native._protocol(ROOT)
        schema = native._input(ROOT, current, 'modelResponseSchema')
        envelope = native._input(ROOT, current, 'promptEnvelope')
        old_schema = native._input(ROOT, old, 'modelResponseSchema')
        old_envelope = native._input(ROOT, old, 'promptEnvelope')
        definition = schema['properties']['discoveryOutcome']['description']
        old_definition = old_schema['properties']['discoveryOutcome']['description']
        self.assertEqual(envelope['assessmentRevision'], 5)
        self.assertEqual(old_envelope['assessmentRevision'], 4)
        self.assertEqual(envelope['fixedInstructions'].count(definition), 1)
        schema_without_change = copy.deepcopy(schema)
        schema_without_change['properties']['discoveryOutcome']['description'] = old_definition
        self.assertEqual(schema_without_change, old_schema)
        self.assertEqual(schema['properties']['discoveryOutcome']['enum'],
                         ['selected', 'clarification', 'no-route', 'unavailable'])
        for ordinal, case in enumerate(native.legacy.load_golden_cases(ROOT), 1):
            with self.subTest(ordinal=ordinal):
                def material(p, s, e):
                    return native.materialize_native_case_contract(root=ROOT,
                        materialization_seed=bytes(32), ordinal=ordinal,
                        protocol_digest=p['protocolDigest'], model_schema=s,
                        prompt_envelope=e, request=case['request'])
                before, after = material(old, old_schema, old_envelope), material(current, schema, envelope)
                self.assertNotEqual(before.prompt_bytes, after.prompt_bytes)
                self.assertEqual(after.prompt_bytes.count(definition.encode()), 1)
                expected = before.prompt_bytes.replace(old_definition.encode(), definition.encode())
                expected = expected.replace(old['inputs']['modelResponseSchema']['sha256'].encode(),
                                            current['inputs']['modelResponseSchema']['sha256'].encode())
                expected = expected.replace(before.token.encode(), after.token.encode())
                self.assertEqual(after.prompt_bytes, expected)
                self.assertEqual(after.schema_bytes,
                                 before.schema_bytes.replace(before.token.encode(), after.token.encode()))
                self.assertTrue(after.prompt_bytes.endswith(('User request:\n'+case['request']+'\n').encode()))
                for forbidden in (case['id'], 'expectedOutcome', 'expectedRoutes', 'caseClass', 'discoveryAvailable'):
                    self.assertNotIn(forbidden.encode(), after.prompt_bytes)
                # RPC facts stay facts; the compatibility fragment supplies no
                # selected outcome, and an error is never converted to success.
                relayed = discovery.relay_empty_discovery(after, {'skills': [], 'errors': []})
                prefix = relayed.prompt_bytes.partition(b'\nUser request:\n')[0]
                fragment = prefix[prefix.index(b'\nNative skills/list query result'):]
                self.assertNotIn(b'unavailable', fragment)
                self.assertNotIn(b'no-route', fragment)
                self.assertIn(b'{"skills":[],"errors":[]}', fragment)
                self.assertIs(discovery.relay_empty_discovery(after,
                    {'skills': [{'name': 'synthetic-other-workflow'}], 'errors': []}), after)
                with self.assertRaises(discovery.DiscoveryQueryError):
                    discovery.relay_empty_discovery(after, {'skills': [], 'errors': ['synthetic error']})

    def test_definition_drift_cannot_be_delivered(self):
        p = native._protocol(ROOT)
        schema = native._input(ROOT, p, 'modelResponseSchema')
        e = native._input(ROOT, p, 'promptEnvelope')
        rule = schema['properties']['discoveryOutcome']['description']
        for change in ('missing', 'duplicate', 'different'):
            with self.subTest(change=change):
                altered = copy.deepcopy(e)
                altered['fixedInstructions'].remove(rule)
                altered['fixedInstructions'] += [rule]*2 if change == 'duplicate' else [rule+' Changed.'] if change == 'different' else []
                with self.assertRaisesRegex(native.NativeObservationError, 'field definitions'):
                    native.materialize_native_case_contract(root=ROOT,
                        materialization_seed=bytes(32), ordinal=1,
                        protocol_digest=p['protocolDigest'], model_schema=schema,
                        prompt_envelope=altered, request='Compare a local planning workflow with a note-taking workflow.')

    def test_one_state_one_query_and_no_old_window_or_reply_admission(self):
        run, _, calls, queried = self.window.prepared(outcome_semantics=True)
        state = native._state(ROOT, run, outcome_semantics=True)[1]
        self.assertEqual([x['ordinal'] for x in state['cases']], [11])
        self.assertEqual(len(queried), 1)
        self.assertEqual(calls, [])
        self.assertEqual(native.outcome_attempt_history(ROOT)['attempts'], 118)
        self.assertFalse(native._case_paths(run, 11)['discovery'].exists())
        self.assertFalse(native._case_paths(run, 11)['package'].exists())
        self.assertTrue(all(not native._case_paths(run, i)['case'].exists() for i in range(1,17) if i != 11))
        self.assertEqual(native.OUTCOME_ACCEPTANCE['clarificationOrdinals'], [])
        self.assertIsNone(native.OUTCOME_ACCEPTANCE['clarificationRunName'])
        for flags in ({}, {'revision_four': True}, {'host_context': True}, {'empty_discovery': True}):
            with self.subTest(flags=flags), patch.object(native, '_revision_four_auth_source', side_effect=AssertionError('old auth')):
                with self.assertRaises(native.NativeObservationError):
                    native.prepare_fixed_acceptance(ROOT, run.parent/'never', run.parent/'old',
                        run.parent/'bundle', authorize_install=True, authorize_copy=True, **flags)

    def run_once(self, *, semantic_failure=False):
        run, runner, calls, _ = self.window.prepared(outcome_semantics=True)
        def invoke(argv, **kwargs):
            if 'exec' not in argv:
                return runner(argv, **kwargs)
            capture = runner(argv, **{**kwargs, 'line_callback': None})
            if semantic_failure:
                events = [json.loads(x) for x in capture['stdout'].splitlines()]
                message = next(e['item'] for e in events if e.get('item', {}).get('type') == 'agent_message')
                answer = json.loads(message['text'])
                answer['discoveryOutcome'] = 'no-route'
                message['text'] = json.dumps(answer)
                Path(argv[argv.index('--output-last-message')+1]).write_text(message['text'])
                capture['stdout'] = b''.join(support.event(e) for e in events)
            for line in capture['stdout'].splitlines():
                kwargs['line_callback'](line)
            return capture
        result = native.run_native_observation(ROOT, run, authorize_model_calls=True,
            assessment_batch=True, reuse_test_auth=True, outcome_semantics=True, process_runner=invoke)
        return run, result, calls, runner

    def test_simulated_pass_is_one_attempt_and_never_full_host_pass(self):
        run, result, calls, runner = self.run_once()
        self.assertEqual(calls, [11])
        self.assertEqual([x['status'] for x in result['caseResults']], ['PASS'])
        self.assertEqual(result['cumulativeAttemptCount'], 119)
        self.assertFalse(result['hostClaim'])
        self.assertEqual(native.validate_native_result(result, ROOT), [])
        with self.assertRaises(native.NativeObservationError):
            native.run_native_observation(ROOT, run, authorize_model_calls=True,
                assessment_batch=True, reuse_test_auth=True, outcome_semantics=True, process_runner=runner)

    def test_no_route_failure_is_retained_without_postprocessing_or_retry(self):
        run, result, calls, runner = self.run_once(semantic_failure=True)
        self.assertEqual(calls, [11])
        self.assertEqual([x['status'] for x in result['caseResults']], ['FAIL'])
        self.assertEqual(result['caseResults'][0]['observed']['discoveryOutcome'], 'no-route')
        self.assertEqual(result['cumulativeAttemptCount'], 119)
        self.assertEqual(native.validate_native_result(result, ROOT), [])
        with self.assertRaises(native.NativeObservationError):
            native.run_native_observation(ROOT, run, authorize_model_calls=True,
                assessment_batch=True, reuse_test_auth=True, outcome_semantics=True, process_runner=runner)

    def test_query_failure_prevents_auth_copy_and_model_start(self):
        with patch.object(native, '_copy_test_auth', side_effect=AssertionError('auth copy')):
            with self.assertRaisesRegex(discovery.DiscoveryQueryError, 'synthetic incomplete'):
                self.window.prepared(outcome_semantics=True, query_error=True)
        run = self.window.parent/native.OUTCOME_ACCEPTANCE['routingRunName']
        self.assertFalse((run/'attempt-11.json').exists())
        self.assertFalse((native._case_paths(run,11)['home']/native.AUTH_FILE_NAME).exists())

    def test_old_normalized_failure_keeps_its_old_inputs_and_score(self):
        binding = native._fixed_result_binding(ROOT, empty_discovery=True)
        data = (ROOT/binding['path']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), native.OUTCOME_PRIOR)
        old = json.loads(data)
        self.assertEqual(native.validate_native_result(old, ROOT), [])
        self.assertEqual(old['cumulativeAttemptCount'], 118)
        self.assertEqual(old['caseResults'][0]['status'], 'FAIL')
        self.assertEqual(old['caseResults'][0]['observed']['discoveryOutcome'], 'no-route')
        self.assertNotEqual(old['protocolDigest'], native._protocol(ROOT)['protocolDigest'])
