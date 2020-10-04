from datetime import datetime, timedelta


def runPoll(event, context):
    segments = [('1', 25750409),
                ('2', 25750487),
                ('3', 25750527),
                ('4', 25750586),
                ('5', 25750610)]
    x = XduroResultBuilder()
    rawResults = x.get_results_for(segments)
    json = convertResultsToJson(rawResults, segments)
    with open('20.json', 'w') as f:
        f.write(json)

class XduroResultBuilder(object):

    def __init__(self):
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
            results['total'] = (total_time, get_all_results)
            all_results.append(results)
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
        results_by_rider = {rider: results for rider, results in results_by_rider.items() if
                            len(results) >= self.min_results}
        return results_by_rider

    def pull_results_from_strava(self, segments):
        cannedData = {
            25750409: '''Rank 	Name 	Date 	Speed 	HR 	Power 	VAM 	Time
	Brett Daughtrey 	3 Oct 2020 	12.3km/h 	- 	245W 	844.6 	7:54
2 	Dean Kirkham (Real Fitness Race Team) 	3 Oct 2020 	10.8km/h 	- 	193W 	742.7 	8:59
3 	Stevan Brown 	3 Oct 2020 	9.7km/h 	176bpm 	254W 	668.3 	9:59
4 	Sam Newham 	3 Oct 2020 	9.4km/h 	159bpm 	284W 	647.8 	10:18
5 	Chris Slack 	3 Oct 2020 	9.2km/h 	- 	192W 	634.4 	10:31
6 	Liam Garrison 	3 Oct 2020 	9.0km/h 	- 	225W 	616.8 	10:49
7 	jade field 	3 Oct 2020 	8.9km/h 	- 	- 	614.0 	10:52
8 	John Baston 	3 Oct 2020 	7.7km/h 	- 	47W 	526.7 	12:40
9 	Toby Willis 	3 Oct 2020 	7.1km/h 	- 	132W 	488.2 	13:40
10 	Daniel Lane 	3 Oct 2020 	7.1km/h 	- 	230W 	487.6 	13:41''',
            25750487: '''Rank 	Name 	Date 	Speed 	HR 	Power 	VAM 	Time
	Brett Daughtrey 	3 Oct 2020 	8.7km/h 	- 	305W 	1,327.4 	5:07
2 	Toby Willis 	3 Oct 2020 	8.1km/h 	- 	271W 	1,234.9 	5:30
3 	Daniel Lane 	3 Oct 2020 	8.0km/h 	- 	294W 	1,223.8 	5:33
4 	Dean Kirkham (Real Fitness Race Team) 	3 Oct 2020 	7.3km/h 	- 	238W 	1,119.6 	6:04
5 	Sam Newham 	3 Oct 2020 	6.4km/h 	157bpm 	316W 	986.7 	6:53
6 	Stevan Brown 	3 Oct 2020 	6.3km/h 	177bpm 	290W 	972.6 	6:59
7 	jade field 	3 Oct 2020 	6.1km/h 	- 	- 	928.3 	7:19
8 	Liam Garrison 	3 Oct 2020 	5.4km/h 	- 	192W 	826.6 	8:13
9 	Chris Slack 	3 Oct 2020 	5.0km/h 	- 	186W 	770.4 	8:49''',
            25750527: '''Rank 	Name 	Date 	Speed 	HR 	Power 	Time
	John Baston 	3 Oct 2020 	10.4km/h 	- 	155W 	3:45
2 	Brett Daughtrey 	3 Oct 2020 	10.3km/h 	- 	270W 	3:47
3 	Daniel Lane 	3 Oct 2020 	9.9km/h 	- 	260W 	3:55
4 	Dean Kirkham (Real Fitness Race Team) 	3 Oct 2020 	9.7km/h 	- 	239W 	4:00
5 	Toby Willis 	3 Oct 2020 	9.7km/h 	- 	245W 	4:01
6 	Chris JOnes 	3 Oct 2020 	9.1km/h 	145bpm 	245W 	4:17
7 	Stevan Brown 	3 Oct 2020 	9.0km/h 	169bpm 	327W 	4:19
8 	jade field 	3 Oct 2020 	8.4km/h 	- 	- 	4:37
9 	Chris Slack 	3 Oct 2020 	5.7km/h 	- 	146W 	6:48''',
            25750586: '''Rank 	Name 	Date 	Speed 	HR 	Power 	Time
	Carl Hopps 	3 Oct 2020 	23.9km/h 	- 	140W 	7:35
2 	Brett Daughtrey 	3 Oct 2020 	21.2km/h 	- 	85W 	8:31
3 	John Baston 	3 Oct 2020 	20.3km/h 	- 	72W 	8:54
4 	Chris JOnes 	3 Oct 2020 	16.9km/h 	118bpm 	76W 	10:42
5 	Daniel Lane 	3 Oct 2020 	12.6km/h 	- 	80W 	14:20
6 	jade field 	3 Oct 2020 	11.4km/h 	- 	- 	15:51''',
            25750610: '''Rank 	Name 	Date 	Speed 	HR 	Power 	VAM 	Time
	Carl Hopps 	3 Oct 2020 	9.2km/h 	- 	228W 	739.8 	9:05
	Daniel Lane 	3 Oct 2020 	9.2km/h 	- 	226W 	739.8 	9:05
3 	John Baston 	3 Oct 2020 	7.7km/h 	- 	44W 	621.3 	10:49
4 	jade field 	3 Oct 2020 	7.0km/h 	- 	- 	559.2 	12:01''',
        }
        results_by_segment = {}
        for _, segment in segments:
            results_by_segment[segment] = {l.split('\t')[1].strip(): convertToTimeDelta(l.split('\t')[-1]) for l in
                                           cannedData[segment].splitlines()[1:]}
        return results_by_segment


def convertResultsToJson(results, segments):
    from collections import OrderedDict
    import json
    allRes = []
    for rdr in results:
        rdrRes = OrderedDict()
        rdrRes['Rider'] = rdr['rider']
        for segName, segId in segments:
            rdrRes[segName] = format_timedelta(rdr[segId][0] if rdr[segId][1] else '')
            if rdrRes[segName] == '0:00:00':
                rdrRes[segName] = ''
        rdrRes['Total'] = format_timedelta(rdr['total'][0])
        allRes.append(rdrRes)
    return json.dumps({'data': allRes}, indent=2)


def format_timedelta(td):
    from datetime import timedelta
    if not isinstance(td, timedelta):
        return td
    if td.days > 30:
        return 'DNF'
    minutes = td.seconds // 60
    seconds = td.seconds % 60
    return '{:02d}M {:02d}S'.format(minutes, seconds)


def convertToTimeDelta(s):
    m, s = s.split(':')
    return timedelta(minutes=int(m), seconds=int(s))
