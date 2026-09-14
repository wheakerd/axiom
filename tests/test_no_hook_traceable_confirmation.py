"""Offline eight-item admission/capture regression; never a host behavior PASS."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from axiom_validation import no_hook_native_observation as n
from axiom_validation import no_hook_clarification as b
from axiom_validation import no_hook_discovery as discovery
from tests import test_no_hook_empty_discovery_window as support
from tests.test_no_hook_native_observation import stream
from tests.test_no_hook_clarification import text_stream

ROOT = Path(__file__).resolve().parents[1]


class TraceableConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.support = support.EmptyDiscoveryWindowTests()
        self.support.setUp()
        self.addCleanup(self.support.doCleanups)
        original = n._fixed_attempt_history
        histories = {}
        def history(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            if key not in histories:
                histories[key] = original(*args, **kwargs)
            return copy.deepcopy(histories[key])
        self.enterContext(patch.object(n, '_fixed_attempt_history', side_effect=history))

    def capture(self, failure=None, public_failure=None, reply_query_failure=False):
        run, runner, _, queries = self.support.prepared(traceable_confirmation=True)
        self.assertEqual([x['ordinal'] for x in n._state(ROOT, run, traceable_confirmation=True)[1]['cases']], [13,6,14,15,16])
        order, reviewed = [], []
        def invoke(argv, **kw):
            if 'exec' not in argv:
                return runner(argv, **kw)
            ordinal = int(Path(kw['cwd']).parent.name[5:])
            routing = '--output-schema' in argv
            label = ('A' if routing else 'B') + str(ordinal)
            order.append(label)
            if routing:
                capture = runner(argv, **{**kw, 'line_callback': None})
                if label == failure:
                    final = Path(argv[argv.index('--output-last-message')+1])
                    response = json.loads(final.read_bytes())
                    response['usingAxiomFrontDoorObserved'] = not response['usingAxiomFrontDoorObserved']
                    final.write_text(json.dumps(response))
                    capture['stdout'] = stream(response)
                for line in capture['stdout'].splitlines():
                    kw['line_callback'](line)
                return capture
            kw['started_callback']()
            message = 'Synthetic complete reply retained for capture-control verification.'
            raw = text_stream((message,))
            for line in raw.splitlines():
                kw['line_callback'](line)
            Path(argv[argv.index('--output-last-message')+1]).write_text(message)
            return {'returncode':0, 'stdout':raw, 'stderr':b'',
                    'diagnostics':{**n._diagnostics(), 'inputFullyDelivered':True}}
        def review(record):
            label = ('B' if record['status'] == 'CAPTURED' else 'A') + str(record['ordinal'])
            self.assertEqual(order[-1], label)
            reviewed.append(label)
            return {'verdict':'FAIL' if label in (failure, public_failure) else 'PASS',
                    'reason':'Synthetic whole-message control review; no real host conclusion.'}
        def query(*args, **kwargs):
            if reply_query_failure:
                raise discovery.DiscoveryQueryError('synthetic reply query failed')
            return self.support.query(*args, **kwargs)
        with patch.object(discovery, 'query_once', side_effect=query):
            result = n.run_native_observation(ROOT, run, authorize_model_calls=True, reuse_test_auth=True,
                assessment_batch=True, traceable_confirmation=True, process_runner=invoke, semantic_review=review)
        self.assertEqual(n.validate_native_result(result, ROOT), [])
        self.assertFalse(result['hostClaim'])
        extra = result['traceableConfirmation']
        self.assertEqual(extra['attemptCount'], len(order))
        self.assertEqual(extra['cliLaunchCount'], len(order))
        self.assertEqual(result['cumulativeAttemptCount'], 122+len(order))
        self.assertEqual(extra['cumulativeCliLaunchCount'], 122+len(order))
        with self.assertRaises(n.NativeObservationError):
            n.run_native_observation(ROOT,run,authorize_model_calls=True,reuse_test_auth=True,
                assessment_batch=True,traceable_confirmation=True,process_runner=invoke,semantic_review=review)
        return run, result, order, reviewed, queries

    def test_full_fixed_order_counts_and_separate_reviews(self):
        run, result, order, reviewed, queries = self.capture()
        self.assertEqual(order, n.TRACEABLE_CONFIRMATION['order'])
        self.assertEqual(reviewed, order)
        self.assertEqual(len(queries), 8)
        self.assertEqual(result['attemptCount'], 5)  # Routing component, not whole window.
        self.assertEqual(result['cumulativeAttemptCount'], 130)
        self.assertEqual(result['traceableConfirmation']['status'], 'INCOMPLETE')  # Simulated.
        self.assertTrue(all(x['status']=='PASS' for x in result['traceableConfirmation']['clarificationResults']))
        for i in [*range(1,6),*range(7,13)]:
            self.assertFalse(n._case_paths(run,i)['case'].exists())
        changed=copy.deepcopy(result)
        changed['traceableConfirmation']['routingMessageReviews'][0]['verdict']='FAIL'
        self.assertTrue(n.validate_native_result(changed, ROOT))
        changed=copy.deepcopy(result)
        changed['traceableConfirmation']['clarificationResults'][0]['capture']['replies']['messages'][0]='Rewritten'
        self.assertTrue(n.validate_native_result(changed, ROOT))

    def test_a13_score_failure_stops_before_any_reply_or_handoff(self):
        run,result,order,reviewed,queries=self.capture('A13')
        self.assertEqual(order,['A13']);self.assertEqual(reviewed,[])
        self.assertEqual(len(queries),5)
        self.assertEqual(result['caseResults'][0]['status'],'FAIL')
        self.assertFalse((run.parent/(n.TRACEABLE_CONFIRMATION['clarificationRunName']+'-after-13')).exists())
        self.assertFalse((n._case_paths(run,6)['home']/n.AUTH_FILE_NAME).exists())

    def test_full_public_a13_review_stops_despite_passing_final_score(self):
        _,result,order,_,_=self.capture(public_failure='A13')
        self.assertEqual(order,['A13'])
        self.assertEqual(result['caseResults'][0]['status'],'PASS')
        self.assertEqual(result['traceableConfirmation']['routingMessageReviews'][0]['verdict'],'FAIL')

    def test_b13_failure_stops_before_a6(self):
        run,_,order,_,_=self.capture('B13')
        self.assertEqual(order,['A13','B13'])
        self.assertFalse((n._case_paths(run,6)['home']/n.AUTH_FILE_NAME).exists())

    def test_a6_failure_does_not_start_remaining_segment(self):
        _,_,order,_,_=self.capture('A6')
        self.assertEqual(order,['A13','B13','A6'])

    def test_b12_failure_does_not_handoff_to_b14(self):
        run,_,order,_,_=self.capture('B12')
        self.assertEqual(order,n.TRACEABLE_CONFIRMATION['order'][:-1])
        tail=run.parent/(n.TRACEABLE_CONFIRMATION['clarificationRunName']+'-after-16')
        self.assertFalse((n._case_paths(tail,14)['home']/n.AUTH_FILE_NAME).exists())

    def test_query_failure_does_not_consume_an_observation_or_copy_auth(self):
        with self.assertRaises(discovery.DiscoveryQueryError):
            self.support.prepared(traceable_confirmation=True,query_error=True)
        run=self.support.parent/n.TRACEABLE_CONFIRMATION['routingRunName']
        self.assertFalse((run/'batch-started.json').exists())
        self.assertFalse((n._case_paths(run,13)['home']/n.AUTH_FILE_NAME).exists())

    def test_reply_query_failure_closes_before_reply_model_or_next_a_handoff(self):
        run,result,order,_,_=self.capture(reply_query_failure=True)
        self.assertEqual(order,['A13'])
        entry=result['traceableConfirmation']['clarificationResults'][0]
        self.assertEqual(entry['status'],'INCOMPLETE')
        self.assertEqual(entry['attemptCount'],0)
        self.assertFalse((n._case_paths(run,6)['home']/n.AUTH_FILE_NAME).exists())

    def test_history_and_uniform_input_semantics_are_preserved(self):
        self.assertEqual(n.traceable_attempt_history(ROOT)['attempts'],122)
        baseline=json.loads(__import__('subprocess').check_output(['git','show',
            'HEAD:evals/no-hook-observation/codex-native-protocol-v2.json'],cwd=ROOT))
        current=n._protocol(ROOT)
        for key in ['assessmentRevision','hostEnvironmentContext','nativeEmptyDiscovery']:
            self.assertEqual(baseline[key],current[key])
        for key in ['modelResponseSchema','promptEnvelope','fixtureMatrix','goldenSet']:
            self.assertEqual(baseline['inputs'][key],current['inputs'][key])
        self.assertEqual(baseline['bundle'],current['bundle'])
        for flags in ({},{'revision_four':True},{'host_context':True},{'empty_discovery':True},
                      {'outcome_semantics':True},{'accepted_remainder':True}):
            with patch.object(n,'_revision_four_auth_source',side_effect=AssertionError('old source reached')):
                with self.assertRaises(n.NativeObservationError):
                    n.prepare_fixed_acceptance(ROOT,self.support.parent/'never',self.support.parent/'old',
                        self.support.parent/'bundle',authorize_install=True,authorize_copy=True,**flags)

class HistoricalAuthenticationPackageTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.package = Path(self.directory.name) / 'public-package'
        self.package.mkdir()
        self.result = json.loads((ROOT / 'evals/no-hook-observation/results' /
            ('codex-native-' + n.EMPTY_DISCOVERY_PRIOR + '.json')).read_bytes())
        evidence = json.loads((ROOT / 'evidence/profiles/openai-hook-independent-v1/bundle-revision-14.json').read_bytes())
        manifest = evidence['bundleManifest']
        for entry in manifest['runtimeFiles']:
            name = entry['path']
            data = (ROOT / n.TRACEABLE_DISCOVERY_ARCHIVE / 'traceable-git-submit-source.txt').read_bytes() if name == 'skills/traceable-git-submit/SKILL.md' else (ROOT / name).read_bytes()
            path = self.package / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data);path.chmod(0o644)
        for name, value in [('BUNDLE-MANIFEST.json', manifest),
                            ('.codex-plugin/plugin.json', manifest['derivedPluginManifest']['fields'])]:
            path = self.package / name;path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value, ensure_ascii=True, indent=2)+'\n');path.chmod(0o644)

    def test_original_inventory_is_accepted_without_rebinding_new_target_identity(self):
        old=n._auth_source_package_identity(ROOT,self.package,self.result)
        self.assertEqual(old,n._host_context_protocol(ROOT)['bundle']['packageSha256'])
        self.assertNotEqual(old,n._protocol(ROOT)['bundle']['packageSha256'])
        with self.assertRaises(n.NativeObservationError):
            n.package_identity(self.package)

    def test_unknown_source_file_is_rejected_before_any_snapshot_read(self):
        (self.package/'unknown').write_text('Public synthetic unregistered file.')
        with patch.object(n.legacy,'snapshot_tree',side_effect=AssertionError('unknown file must not be read')):
            with self.assertRaisesRegex(n.NativeObservationError,'unknown authentication-source package file'):
                n._auth_source_package_identity(ROOT,self.package,self.result)

    def test_hardlinked_manifest_is_rejected_before_its_content_is_read(self):
        import os
        manifest=self.package/'BUNDLE-MANIFEST.json'
        linked=Path(self.directory.name)/'public-hardlink'
        os.link(manifest,linked)
        original=n._read
        def guarded(path,*args,**kwargs):
            if path==manifest:
                raise AssertionError('hardlinked manifest must not be opened')
            return original(path,*args,**kwargs)
        with patch.object(n,'_read',side_effect=guarded):
            with self.assertRaisesRegex(n.NativeObservationError,'unknown authentication-source package file'):
                n._auth_source_package_identity(ROOT,self.package,self.result)

    def test_changed_registered_source_bytes_or_wrong_protocol_are_rejected(self):
        path=self.package/'skills/traceable-git-submit/SKILL.md'
        path.write_bytes(path.read_bytes()+b'\n')
        with self.assertRaisesRegex(n.NativeObservationError,'public package bytes changed'):
            n._auth_source_package_identity(ROOT,self.package,self.result)
        with self.assertRaisesRegex(n.NativeObservationError,'source protocol changed'):
            n._auth_source_package_identity(ROOT,self.package,{**self.result,'protocolDigest':n._protocol(ROOT)['protocolDigest']})


class TraceableCliExitTests(unittest.TestCase):
    def test_cli_uses_whole_window_status_even_when_all_routing_passed(self):
        import contextlib
        import io
        for status,code in [('FAIL',1),('INCOMPLETE',1),('PASS',0)]:
            with self.subTest(status=status), patch.object(n,'run_native_observation',
                    return_value={'status':'PASS','traceableConfirmation':{'status':status}}), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(n.main(['--run','--run-root','/synthetic-not-created',
                    '--traceable-confirmation','--review-public-messages-stdin'],root=ROOT),code)


if __name__ == '__main__':
    unittest.main()
