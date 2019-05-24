from stravalib.client import Client
from datetime import datetime, timedelta
import pytz
import os

def runPoll(event, context):
    access_token = os.environ.get('strava_access_token', '')
    segments = [('GD-1', 20515464),
                ('GD-2', 20515384),
                ('GD-3', 20515676),
                ('GD-4', 20515238),
                ('GD-5', 20515175)]
    x = XduroResultBuilder(access_token)
    rawResults = x.get_results_for(segments)
    json = convertResultsToJson(rawResults, segments)
    toS3(html)

def toS3(body):
    import boto3
    s3 = boto3.resource('s3')
    s3.Object('bikerid.es', 'racingCollective/duro/glen/19-test.json').put(Body=body)

class XduroResultBuilder(object):

    def __init__(self, access_token):
        self.client = Client()
        self.client.access_token = access_token
        self.club = 238976
        #self.timeFrame = 'this_month'
        self.min_results = 2

    def get_results_for(self, segments):
        results_by_segment = self.pull_results_from_strava(segments)
        results_by_rider = self.pivot_results(results_by_segment)
        worst_results = self.get_worst_results(segments, results_by_rider)
        all_results = self.compile_results(results_by_rider, worst_results)
        return all_results

    def compile_results(self, results_by_rider, worst_results):
        all_results = []
        for rider, results in results_by_rider.items():
            results = {id: (results[id], True) if id in results else (worst_results[id], False) for id in worst_results}
            total_time = timedelta(0)
            get_all_results = True
            for t, r in results.values():
                total_time += t
                get_all_results = get_all_results & r
            results['rider'] = rider
            results['total'] = (total_time,get_all_results)
            all_results.append( results )
        all_results.sort(key=lambda r: r['total'])
        return all_results

    def get_worst_results(self, segments, results_by_rider):
        worst_results = {seg: timedelta() for _, seg in segments}
        for rider, results in results_by_rider.items():
            for seg, result in results.items():
                if result > worst_results[seg]:
                    worst_results[seg] = result
        return worst_results

    def pivot_results(self, results_by_segment):
        results_by_rider = {}
        for id, segment in results_by_segment.items():
            for athlete, elapsed_time in segment.items():
                if athlete not in results_by_rider:
                    results_by_rider[athlete] = {}
                results_by_rider[athlete][id] = elapsed_time
        results_by_rider = {rider: results for rider, results in results_by_rider.items() if len(results) >= self.min_results }
        return results_by_rider

    def pull_results_from_strava(self, segments):
        results_by_segment = {}
        for _, segment in segments:
            efforts = self.client.get_segment_leaderboard(segment, timeframe=self.timeFrame, club_id=self.club, top_results_limit=50)
            results_by_segment[segment] = {e.athlete_name: e.elapsed_time for e in efforts}
        return results_by_segment


def convertResultsToJson( results, segments ):
    from collections import OrderedDict
    import json
    allRes = []
    for rdr in results:
        rdrRes = OrderedDict()
        rdrRes['Rider'] = rdr['rider']
        for segName, segId in segments:
            rdrRes[segName] = str(rdr[segId][0])
        rdrRes['Total'] = str(rdr['total'][0])
        allRes.append(rdrRes)
    return json.dumps({'data': allRes }, indent=2)
