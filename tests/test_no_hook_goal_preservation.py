"""Offline fixed B-first admission tests; synthetic replies are not host evidence."""
import copy
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from axiom_validation import no_hook_native_observation as n
from axiom_validation import no_hook_clarification as b
from axiom_validation import no_hook_discovery as discovery
from tests import test_no_hook_empty_discovery_window as support
from tests.test_no_hook_native_observation import stream
from tests.test_no_hook_clarification import text_stream

from tests.historical_fixture import ROOT


class GoalPreservationTests(unittest.TestCase):
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

    def capture(self, failure=None, query_failure=False):
        run, runner, _, queries = self.support.prepared(goal_preservation=True)
        state = n._state(ROOT, run, goal_preservation=True)[1]
        self.assertEqual([x['ordinal'] for x in state['cases']], [12, 3])
        self.assertFalse((n._case_paths(run,12)['home']/n.AUTH_FILE_NAME).exists())
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
            message = 'Synthetic complete reply for offline capture-control testing.'
            raw = text_stream((message,))
            for line in raw.splitlines():
                kw['line_callback'](line)
            Path(argv[argv.index('--output-last-message')+1]).write_text(message)
            return {'returncode':0,'stdout':raw,'stderr':b'',
                    'diagnostics':{**n._diagnostics(),'inputFullyDelivered':True}}
        def review(record):
            label = ('B' if record['status']=='CAPTURED' else 'A')+str(record['ordinal'])
            self.assertEqual(order[-1],label);reviewed.append(label)
            return {'verdict':'FAIL' if label==failure else 'PASS',
                    'reason':'Synthetic whole-capture control review; not a real behavior conclusion.'}
        def query(*args,**kwargs):
            if query_failure:
                raise discovery.DiscoveryQueryError('synthetic query failure')
            return self.support.query(*args,**kwargs)
        with patch.object(discovery,'query_once',side_effect=query), \
             patch.object(n,'_revision_four_auth_source',return_value=state):
            result = n.run_native_observation(ROOT,run,authorize_model_calls=True,reuse_test_auth=True,
                assessment_batch=True,goal_preservation=True,process_runner=invoke,semantic_review=review)
        self.assertEqual(n.validate_native_result(result,ROOT),[])
        self.assertFalse(result['hostClaim'])
        extra=result['goalPreservation']
        self.assertEqual(extra['attemptCount'],len(order));self.assertEqual(extra['cliLaunchCount'],len(order))
        self.assertEqual(result['cumulativeAttemptCount'],129+len(order))
        self.assertEqual(extra['cumulativeCliLaunchCount'],129+len(order))
        with self.assertRaises(n.NativeObservationError):
            n.run_native_observation(ROOT,run,authorize_model_calls=True,reuse_test_auth=True,
                assessment_batch=True,goal_preservation=True,process_runner=invoke,semantic_review=review)
        return run,result,order,reviewed,queries

    def test_complete_fixed_order_and_no_extra_scopes(self):
        run,result,order,reviewed,queries=self.capture()
        self.assertEqual(order,['B12','A12','A3','B14']);self.assertEqual(reviewed,order)
        self.assertEqual(len(queries),4)
        self.assertEqual(result['attemptCount'],2)
        self.assertEqual(result['goalPreservation']['status'],'INCOMPLETE')
        for i in set(range(1,17))-{12,3}:
            self.assertFalse(n._case_paths(run,i)['case'].exists())
        bad=copy.deepcopy(result);bad['goalPreservation']['clarificationResults'][0]['review']['verdict']='FAIL'
        self.assertTrue(n.validate_native_result(bad,ROOT))
        bad=copy.deepcopy(result);bad['goalPreservation']['clarificationResults'][0]['capture']['replies']['messages'][0]='Changed'
        self.assertTrue(n.validate_native_result(bad,ROOT))

    def test_b12_failure_stops_before_any_routing_authentication(self):
        run,result,order,_,_=self.capture('B12')
        self.assertEqual(order,['B12'])
        self.assertEqual([x['status'] for x in result['caseResults']],['NOT-RUN','NOT-RUN'])
        for ordinal in (12,3):
            self.assertFalse((n._case_paths(run,ordinal)['home']/n.AUTH_FILE_NAME).exists())
        self.assertFalse((run.parent/(n.GOAL_PRESERVATION['clarificationRunName']+'-stage-14')).exists())

    def test_a12_failure_stops_a3_and_b14(self):
        _,_,order,_,_=self.capture('A12');self.assertEqual(order,['B12','A12'])

    def test_a3_failure_stops_b14(self):
        run,_,order,_,_=self.capture('A3');self.assertEqual(order,['B12','A12','A3'])
        self.assertFalse((run.parent/(n.GOAL_PRESERVATION['clarificationRunName']+'-stage-14')).exists())

    def test_first_reply_query_failure_consumes_no_model_and_stops(self):
        run,result,order,_,_=self.capture(query_failure=True)
        self.assertEqual(order,[])
        self.assertEqual(result['goalPreservation']['clarificationResults'][0]['status'],'INCOMPLETE')
        self.assertFalse((n._case_paths(run,12)['home']/n.AUTH_FILE_NAME).exists())

    def test_old_history_closed_and_measurement_inputs_unchanged(self):
        self.assertEqual(n.goal_attempt_history(ROOT)['attempts'],129)
        old=n._traceable_protocol(ROOT);now=n._protocol(ROOT)
        for key in ('assessmentRevision','hostEnvironmentContext','nativeEmptyDiscovery'):
            self.assertEqual(old[key],now[key])
        for key in ('modelResponseSchema','promptEnvelope','fixtureMatrix','goldenSet'):
            self.assertEqual(old['inputs'][key],now['inputs'][key])
        with patch.object(n,'_revision_four_auth_source',side_effect=AssertionError('closed source reached')):
            for flags in ({},{'revision_four':True},{'host_context':True},{'empty_discovery':True},
                          {'outcome_semantics':True},{'accepted_remainder':True},{'traceable_confirmation':True}):
                with self.assertRaises(n.NativeObservationError):
                    n.prepare_fixed_acceptance(ROOT,self.support.parent/'never',self.support.parent/'old',
                        self.support.parent/'bundle',authorize_install=True,authorize_copy=True,**flags)

    def test_query_preparation_failure_creates_no_attempt_or_auth_handoff(self):
        with self.assertRaises(discovery.DiscoveryQueryError):
            self.support.prepared(goal_preservation=True,query_error=True)
        run=self.support.parent/n.GOAL_PRESERVATION['routingRunName']
        self.assertFalse((run/'batch-started.json').exists())
        self.assertFalse((n._case_paths(run,12)['home']/n.AUTH_FILE_NAME).exists())
