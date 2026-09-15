"""Bounded remainder admission and capture control; synthetic results are not host PASS."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from axiom_validation import no_hook_native_observation as n
from axiom_validation import no_hook_clarification as b
from axiom_validation import no_hook_discovery as discovery
from tests import test_no_hook_empty_discovery_window as empty_window
from tests.test_no_hook_clarification import text_stream
from tests.test_no_hook_native_observation import stream

from tests.historical_fixture import ROOT

class TraceableDiscoveryHistoryTests(unittest.TestCase):
    def test_new_runtime_keeps_recorded_remainder_protocol_and_closed_window(self):
        recorded = n._accepted_remainder_protocol(ROOT)
        current = n._protocol(ROOT)
        self.assertNotEqual(recorded['protocolDigest'], current['protocolDigest'])
        self.assertEqual(recorded['assessmentRevision'], current['assessmentRevision'])
        self.assertEqual(recorded['acceptedRemainder'], current['acceptedRemainder'])
        self.assertEqual(recorded['nativeEmptyDiscovery'], current['nativeEmptyDiscovery'])
        binding = n._fixed_result_binding(ROOT, accepted_remainder=True)
        self.assertEqual(binding['sha256'], n.ACCEPTED_REMAINDER_RESULT_SHA256)
        data = (ROOT / binding['path']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), binding['sha256'])
        result = json.loads(data)
        self.assertEqual(result['protocolDigest'], recorded['protocolDigest'])
        self.assertEqual(result['cumulativeAttemptCount'], 122)
        self.assertEqual([c['status'] for c in result['caseResults']],
                         ['PASS', 'PASS', 'FAIL', 'NOT-RUN', 'NOT-RUN', 'NOT-RUN'])
        with patch.object(n, '_revision_four_auth_source',
                          side_effect=AssertionError('recorded window reached authentication')):
            with self.assertRaisesRegex(n.NativeObservationError, 'already recorded'):
                n.prepare_fixed_acceptance(ROOT, ROOT / 'never-create-a-run',
                    ROOT / 'never-read-private-state', ROOT / 'never-copy-a-package',
                    authorize_install=True, authorize_copy=True, accepted_remainder=True)

class AcceptedRemainderTests(unittest.TestCase):
    def setUp(self):
        self.support = empty_window.EmptyDiscoveryWindowTests()
        self.support.setUp()
        self.addCleanup(self.support.doCleanups)
        # These tests do not change repository history. Validate each immutable
        # predecessor chain once per test, then copy that result for the many
        # scope/capture checks. Real admission and prior-byte checks still run;
        # no cache is installed in production or shared between tests.
        original = n._fixed_attempt_history
        histories = {}
        def fixed_history(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            if key not in histories:
                histories[key] = original(*args, **kwargs)
            return copy.deepcopy(histories[key])
        self.enterContext(patch.object(n, '_fixed_attempt_history', side_effect=fixed_history))

    def prepared(self):
        return self.support.prepared(accepted_remainder=True)

    def routing(self, fail_at=None):
        run, runner, calls, queried = self.prepared()
        def invoke(argv, **kw):
            if 'exec' not in argv or fail_at is None or int(Path(kw['cwd']).parent.name[5:]) != fail_at:
                return runner(argv, **kw)
            capture = runner(argv, **{**kw, 'line_callback': None})
            final = Path(argv[argv.index('--output-last-message')+1])
            answer = json.loads(final.read_bytes())
            answer['usingAxiomFrontDoorObserved'] = not answer['usingAxiomFrontDoorObserved']
            final.write_text(json.dumps(answer));raw = stream(answer)
            for line in raw.splitlines():kw['line_callback'](line)
            return {**capture, 'stdout':raw}
        result = n.run_native_observation(ROOT, run, authorize_model_calls=True,
            reuse_test_auth=True, assessment_batch=True, accepted_remainder=True, process_runner=invoke)
        return run,result,runner,calls,queried

    def test_six_registered_scopes_no_a11_and_one_query_each(self):
        run,_,calls,queries=self.prepared()
        self.assertEqual(calls,[])
        self.assertEqual([x['ordinal'] for x in n._state(ROOT,run,accepted_remainder=True)[1]['cases']], [10,12,13,14,15,16])
        self.assertEqual(len(queries),6)
        self.assertTrue(all(not n._case_paths(run,i)['case'].exists() for i in [*range(1,10),11]))
        self.assertEqual([i for i in [10,12,13,14,15,16] if (n._case_paths(run,i)['home']/n.AUTH_FILE_NAME).exists()], [10])
        self.assertEqual(n.remainder_attempt_history(ROOT)['attempts'],119)
        with self.assertRaises(n.NativeObservationError):
            n._copy_test_auth(run,10,10,create=False)
        with self.assertRaises(n.NativeObservationError):
            n._copy_test_auth(run,10,10,create=True,source_root=run)
        with self.assertRaises(n.NativeObservationError):
            n._copy_test_auth(run,10,10,create=True,source_root=run/'case-10'/'..')

    def test_any_routing_semantic_failure_closes_every_later_slot_and_handoff(self):
        run,result,runner,calls,_=self.routing(fail_at=12)
        self.assertEqual(calls,[10,12])
        self.assertEqual([c['status'] for c in result['caseResults']],['PASS','FAIL']+['NOT-RUN']*4)
        self.assertEqual(result['cumulativeAttemptCount'],121)
        self.assertEqual(n.validate_native_result(result,ROOT),[])
        self.assertFalse((n._case_paths(run,13)['home']/n.AUTH_FILE_NAME).exists())
        with patch.object(b,'_login',side_effect=AssertionError('handoff after failure')):
            with self.assertRaises(n.NativeObservationError):
                b.prepare(ROOT,run.parent/n.ACCEPTED_REMAINDER['clarificationRunName'],run,
                    bundle_root=run.parent/'bundle',authorized=True,accepted_remainder=True,runner=runner)
        with self.assertRaises(n.NativeObservationError):
            n.run_native_observation(ROOT,run,authorize_model_calls=True,reuse_test_auth=True,
                assessment_batch=True,accepted_remainder=True,process_runner=runner)

    def reply_batch(self, verdict='PASS'):
        run,result,runner,calls,queries=self.routing()
        self.assertEqual(calls,[10,12,13,14,15,16])
        self.assertFalse(result['hostClaim'])
        target=run.parent/n.ACCEPTED_REMAINDER['clarificationRunName']
        with patch.object(discovery,'query_once',side_effect=self.support.query):
            b.prepare(ROOT,target,run,bundle_root=run.parent/'bundle',authorized=True,accepted_remainder=True,runner=runner)
        started=[];reviewed=[]
        message='Synthetic complete public reply for transport checks.'
        def invoke(argv,**kw):
            if 'exec' not in argv:return runner(argv,**kw)
            ordinal=int(Path(kw['cwd']).parent.name[5:]);started.append(ordinal)
            self.assertNotIn('--output-schema',argv)
            kw['started_callback']();raw=text_stream((message,))
            for line in raw.splitlines():kw['line_callback'](line)
            Path(argv[argv.index('--output-last-message')+1]).write_text(message)
            return {'returncode':0,'stdout':raw,'stderr':b'',
                'diagnostics':{**n._diagnostics(),'inputFullyDelivered':True}}
        def review(record):
            reviewed.append(record['ordinal'])
            self.assertEqual(record['replies']['messages'],[message])
            self.assertEqual(started,reviewed)
            if record['ordinal']<14:self.assertFalse((n._case_paths(target,record['ordinal']+1)['home']/n.AUTH_FILE_NAME).exists())
            return {'verdict':verdict,'reason':'Synthetic operator control verdict; not a host behavior claim.'}
        doc=b.run(ROOT,target,authorized=True,accepted_remainder=True,semantic_review=review,runner=invoke)
        return target,doc,started,reviewed,invoke

    def test_reply_semantic_failure_keeps_full_capture_and_stops_before_next_auth(self):
        run,doc,started,reviewed,invoke=self.reply_batch('FAIL')
        self.assertEqual(started, [12]);self.assertEqual(reviewed,[12])
        self.assertEqual([c['status'] for c in doc['caseResults']],['CAPTURED','NOT-RUN','NOT-RUN'])
        self.assertEqual(doc['cumulativeAttemptCount'],126)
        self.assertEqual(doc['operatorSemanticReviews'][0]['verdict'],'FAIL')
        self.assertFalse((n._case_paths(run,13)['home']/n.AUTH_FILE_NAME).exists())
        with self.assertRaises(n.NativeObservationError):
            b.run(ROOT,run,authorized=True,accepted_remainder=True,semantic_review=lambda _: {},runner=invoke)

    def test_full_synthetic_nine_preserves_separate_semantic_review_and_caps(self):
        _,doc,started,reviewed,_=self.reply_batch()
        self.assertEqual(started, [12,13,14]);self.assertEqual(reviewed,started)
        self.assertEqual(doc['cumulativeAttemptCount'],128)
        self.assertEqual(doc['cumulativeCliLaunchCount'],128)
        self.assertEqual(doc['runMode'],'simulated')
        self.assertEqual(doc['semanticAssessment'],'separate-review-required')
        self.assertTrue(all(c['status']=='CAPTURED' for c in doc['caseResults']))
        for rec,assessment in zip(doc['caseResults'],doc['operatorSemanticReviews']):
            self.assertEqual(assessment['caseResultSha256'],b.digest(b._bytes(rec)))

    def test_query_error_stops_before_model_and_authentication(self):
        with self.assertRaises(discovery.DiscoveryQueryError):
            self.support.prepared(accepted_remainder=True,query_error=True)
        run=self.support.parent/n.ACCEPTED_REMAINDER['routingRunName']
        self.assertFalse((n._case_paths(run,10)['home']/n.AUTH_FILE_NAME).exists())
        self.assertFalse((run/'batch-started.json').exists())

    def test_uniform_inputs_retain_the_previous_assessment_semantics(self):
        old=n._remainder_prior_protocol(ROOT);current=n._protocol(ROOT)
        for key in ['modelResponseSchema','promptEnvelope','fixtureMatrix']:
            self.assertEqual(old['inputs'][key],current['inputs'][key])
        for ordinal,case in enumerate(n.legacy.load_golden_cases(ROOT),1):
            def material(p):return n.materialize_native_case_contract(root=ROOT,materialization_seed=bytes(32),ordinal=ordinal,
                protocol_digest=p['protocolDigest'],model_schema=n._input(ROOT,p,'modelResponseSchema'),
                prompt_envelope=n._input(ROOT,p,'promptEnvelope'),request=case['request'])
            before,after=material(old),material(current)
            self.assertEqual(after.prompt_bytes,before.prompt_bytes.replace(before.token.encode(),after.token.encode()))
            self.assertEqual(after.schema_bytes,before.schema_bytes.replace(before.token.encode(),after.token.encode()))
            self.assertNotIn(b'accepted deviation',after.prompt_bytes)

    def test_accepted_old_score_and_stopped_windows_remain_unchanged(self):
        binding=n._fixed_result_binding(ROOT,outcome_semantics=True);raw=(ROOT/binding['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),n.REMAINDER_PRIOR)
        result=json.loads(raw);self.assertEqual(result['status'],'FAIL')
        self.assertEqual(result['caseResults'][0]['observed']['discoveryOutcome'],'no-route')
        self.assertEqual(n.validate_native_result(result,ROOT),[])
        for flags in [{},{'revision_four':True},{'host_context':True},{'empty_discovery':True},{'outcome_semantics':True}]:
            with patch.object(n,'_revision_four_auth_source',side_effect=AssertionError('old auth')):
                with self.assertRaises(n.NativeObservationError):
                    n.prepare_fixed_acceptance(ROOT,self.support.parent/'never',self.support.parent/'old',self.support.parent/'bundle',authorize_install=True,authorize_copy=True,**flags)
