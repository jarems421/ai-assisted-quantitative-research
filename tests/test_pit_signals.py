from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import random
import unittest

from src.research.pit_signals import (insider_score, institutional_score, decision_for_session,
                                      assert_pit, quarter_pair, resolve_identity)
from src.research.custom_signals import export_dataset, publish_new


def event(**changes):
    return dict(dict(eventId="leg1", ownerCik="owner1", security_id="stable1", versionAccession="original",
                     firstAvailableAt="2015-01-02T01:00:00Z", availableAt="2015-01-02T01:00:00Z",
                     supersededAt=None, coverageUnverifiedAt=None, rowKind="nonderiv", transactionCode="P",
                     acquiredDisposed="A", shares=10), **changes)


def filing(manager, quarter, **changes):
    return dict(dict(manager_cik=manager, quarter=quarter, availableAt="2015-05-15T01:00:00Z",
                     accession=manager+quarter, kind="ORIGINAL", holdings={"stable1": 10}, complete=True,
                     identity_certified=True), **changes)


class PITSignalTests(unittest.TestCase):
    def test_joint_owners_duplicate_legs_and_people(self):
        t=decision_for_session(date(2015,1,5))
        rows=[event(),event(),event(ownerCik="owner2"),event(eventId="leg2")]
        score=insider_score(rows,"stable1",t,30,coverage_certified=True)
        self.assertEqual((score["value"],score["qualifying_transaction_count"]),(2,2))
        assert_pit(score,t)

    def test_future_amendment_does_not_rewrite_old_view(self):
        t=decision_for_session(date(2015,1,5));after=decision_for_session(date(2015,1,8))
        old=event(supersededAt="2015-01-06T01:00:00Z")
        amendment=event(versionAccession="amended",availableAt="2015-01-06T01:00:00Z",transactionCode="S")
        self.assertEqual(insider_score([event()],"stable1",t,30,coverage_certified=True),insider_score([old,amendment],"stable1",t,30,coverage_certified=True))
        self.assertEqual(insider_score([old,amendment],"stable1",after,30,coverage_certified=True)["value"],0)

    def test_correction_does_not_restart_window(self):
        row=event(firstAvailableAt="2014-10-01T01:00:00Z",availableAt="2015-01-03T01:00:00Z")
        self.assertEqual(insider_score([row],"stable1",decision_for_session(date(2015,1,5)),90,coverage_certified=True)["value"],0)

    def test_missing_feed_and_ambiguous_active_versions(self):
        t=decision_for_session(date(2015,1,5))
        self.assertIsNone(insider_score([],"stable1",t,30,coverage_certified=False)["value"])
        self.assertIsNone(insider_score([event(),event(shares=20)],"stable1",t,30,coverage_certified=True)["value"])

    def test_after_cutoff_and_weekend_publication(self):
        friday=decision_for_session(date(2015,1,9));monday=decision_for_session(date(2015,1,12))
        after=event(availableAt="2015-01-09T03:00:00Z",firstAvailableAt="2015-01-09T03:00:00Z")
        weekend=event(eventId="weekend",ownerCik="weekend",availableAt="2015-01-10T17:00:00Z",firstAvailableAt="2015-01-10T17:00:00Z")
        self.assertEqual(insider_score([after,weekend],"stable1",friday,30,coverage_certified=True)["value"],0)
        self.assertEqual(insider_score([after,weekend],"stable1",monday,30,coverage_certified=True)["value"],2)

    def test_pit_prefix_invariance_many_future_appends(self):
        rng=random.Random(2002)
        for n in range(100):
            t=decision_for_session(date(2015,1,5)+timedelta(days=n))
            base=[event()];future=[event(eventId=str(k),ownerCik=str(k),availableAt=(t+timedelta(hours=rng.randint(1,500))).isoformat()) for k in range(5)]
            self.assertEqual(insider_score(base,"stable1",t,90,coverage_certified=True),insider_score(base+future,"stable1",t,90,coverage_certified=True))

    def test_security_rename_uses_effective_stable_identity(self):
        segments=[dict(ticker="OLD",security_id="s1",start="2014-01-01",end="2015-01-05"),dict(ticker="NEW",security_id="s1",start="2015-01-06",end="2020-12-31")]
        t=datetime(2015,1,7,tzinfo=timezone.utc)
        self.assertEqual(resolve_identity("NEW",t,segments),"s1")
        self.assertIsNone(resolve_identity("OLD",t,segments))
        self.assertIsNone(resolve_identity("NEW",t,segments+[dict(segments[1],security_id="ambiguous")]))

    def test_matched_cohort_and_manager_disappearance(self):
        t=decision_for_session(date(2015,6,5));prior,current=quarter_pair(t)
        rows=[filing("a",prior),filing("a",current,holdings={}),filing("b",prior),filing("b",current),filing("gone",prior)]
        score=institutional_score(rows,"stable1",t,source_certified=True,minimum_managers=2,minimum_coverage=.6)
        self.assertEqual(score["value"],-1);self.assertEqual(score["matched_manager_count"],2)
        self.assertIn("gone",score["excluded_managers"])
        self.assertIsNone(institutional_score(rows,"stable1",t,source_certified=True)["value"])

    def test_late_institutional_amendment_and_missing_not_zero(self):
        t=decision_for_session(date(2015,6,5));prior,current=quarter_pair(t)
        rows=[filing("a",prior),filing("a",current)]
        future=filing("a",current,kind="RESTATEMENT",holdings={},availableAt="2015-06-10T01:00:00Z",accession="later")
        kw=dict(source_certified=True,minimum_managers=1,minimum_coverage=1)
        self.assertEqual(institutional_score(rows,"stable1",t,**kw),institutional_score(rows+[future],"stable1",t,**kw))
        self.assertIsNone(institutional_score([rows[0]],"stable1",t,**kw)["value"])

    def test_quarter_buffer_holiday_and_dst_cutoff(self):
        self.assertEqual(decision_for_session(date(2016,3,14)).utcoffset(),timedelta(hours=-4))
        self.assertEqual(decision_for_session(date(2015,2,17)).hour,21)
        self.assertEqual(quarter_pair(decision_for_session(date(2015,5,31)))[1],"2014-12-31")
        self.assertEqual(quarter_pair(decision_for_session(date(2015,6,2)))[1],"2015-03-31")


class CustomExportTests(unittest.TestCase):
    def make(self,path):
        row=insider_score([event()],"stable1",decision_for_session(date(2015,1,5)),30,coverage_certified=True)
        row.update(ticker="OLD",security_id="stable1",identity_certified=True,decision_timestamp=decision_for_session(date(2015,1,5)).isoformat())
        return export_dataset(path,version="v001",name="audit",rows=[row],source_hashes={"source":"abc"},methodology={"version":1},git_sha="abc123",generated_at="2026-10-11T00:00:00Z",diagnostic_only=True)

    def test_deterministic_points_immutable_version(self):
        with TemporaryDirectory() as tmp:
            a,b=Path(tmp)/"a",Path(tmp)/"b";self.make(a);self.make(b)
            self.assertEqual((a/"points.json").read_bytes(),(b/"points.json").read_bytes())
            with self.assertRaises(ValueError):self.make(a)

    def test_unauthorized_tampered_or_production_publication_rejected(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"data";self.make(p)
            with self.assertRaises(ValueError):publish_new(None,p)
            data=json.loads((p/"manifest.json").read_text());data["diagnostic_only"]=False;(p/"manifest.json").write_text(json.dumps(data))
            with self.assertRaises(ValueError):publish_new(None,p,authorize=True)
            data["diagnostic_only"]=True;(p/"manifest.json").write_text(json.dumps(data));(p/"points.json").write_text("[]")
            with self.assertRaises(ValueError):publish_new(None,p,authorize=True)
