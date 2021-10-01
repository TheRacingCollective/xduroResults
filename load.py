from datetime import datetime, timedelta
import json


class XduroResultBuilder(object):

    def __init__(self, segments, event):
        self.segments = zip(range(1, len(segments)+1), segments)
        self.results = {s: '' for s in segments}
        self.load_segment_results()
        self.min_results = 2
        self.event = event

    def load_segment_results(self):
        for segment_id in self.results:
            try:
                with open('{}.csv'.format(segment_id), 'r') as f:
                    segment_results = f.read()
                    self.results[segment_id] = segment_results
            except IOError:
                pass

    def store_segment_results(self, segment_id, segment_results):
        self.results[segment_id] = segment_results
        with open('{}.csv'.format(segment_id), 'w') as f:
            f.write(segment_results)

    def get_results(self):
        name_by_id, results_by_segment = self._read_results()
        results_by_rider = self._pivot_results(results_by_segment)
        signed_up = get_signups(self.event)
        results_by_rider = self._drop_not_signed_up(results_by_rider, signed_up, name_by_id)
        worst_results = self._get_worst_results(results_by_rider)
        all_results = self._compile_results(results_by_rider, worst_results, name_by_id)
        required_padding = self._get_required_padding(all_results)
        all_results_json = self._convert_results_to_json(all_results, required_padding)
        return all_results_json

    def _get_required_padding(self, all_results):
        padding = {}
        for _, segment_id in self.segments + [(None, 'total')]:
            max_delta = max([rdr.get(segment_id, (0,))[0] for rdr in all_results] or [timedelta(1)])
            max_hours = (max_delta.days * 24) + (max_delta.seconds / 3600)
            padding[segment_id] = (max_hours // 10 + 1)
        return padding

    def _read_results(self):
        results_by_segment = {}
        id2name = {}
        for _, segment in self.segments:
            seg_res = {}
            for a in self.results[segment].splitlines():
                a_split = a.split(',')
                seg_time_raw = a_split[0]
                if len(seg_time_raw.split(':')) == 2:
                    seg_time_raw = '0:'+seg_time_raw
                if 's' in seg_time_raw:
                    seg_time = datetime.strptime(seg_time_raw, '%Ss') - datetime(1900, 1, 1)
                else:
                    seg_time = datetime.strptime(seg_time_raw, '%H:%M:%S') - datetime(1900, 1, 1)
                rider_id = a_split[1].strip()
                name = a_split[2].strip()
                id2name[rider_id] = name
                seg_res[rider_id] = seg_time
            results_by_segment[segment] = seg_res
        return id2name, results_by_segment

    def _pivot_results(self, results_by_segment):
        results_by_rider = {}
        for rider_id, segment in results_by_segment.items():
            for athlete, elapsed_time in segment.items():
                if athlete not in results_by_rider:
                    results_by_rider[athlete] = {}
                results_by_rider[athlete][rider_id] = elapsed_time
        results_by_rider = {rider: results for rider, results in results_by_rider.items() if len(results) >= self.min_results}
        return results_by_rider

    @staticmethod
    def _drop_not_signed_up(results_by_rider, signed_up, name_by_id):
        not_signed_up = [name_by_id[rider] for rider in results_by_rider.keys() if rider not in signed_up]
        if not_signed_up:
            print('Not signed up: %s' % ', '.join(not_signed_up))
        return {rider: results for rider, results in results_by_rider.items() if rider in signed_up}

    @staticmethod
    def _compile_results(results_by_rider, worst_results, name_by_id):
        all_results = []
        for rider, results in results_by_rider.items():
            results = {rider_id: (results[rider_id], True) if rider_id in results else (worst_results[rider_id], False) for rider_id in worst_results}
            total_time = timedelta(0)
            get_all_results = True
            for t, r in results.values():
                total_time += t
                get_all_results = get_all_results & r
            results['rider'] = name_by_id[rider]
            results['total'] = (total_time, get_all_results)
            all_results.append(results)
        all_results.sort(key=lambda res: res['rider'])
        return all_results

    def _get_worst_results(self, results_by_rider):
        worst_results = {seg: timedelta() for _, seg in self.segments}
        for rider, results in results_by_rider.items():
            for seg, result in results.items():
                if result > worst_results[seg]:
                    worst_results[seg] = result
        return worst_results

    def _convert_results_to_json(self, results, required_padding):
        from collections import OrderedDict
        all_res = []
        for rdr in results:
            rider_results = OrderedDict()
            rider_results['R'] = rdr['rider']
            for segName, segId in self.segments:
                rider_results[segName] = format_timedelta(rdr[segId][0] if rdr[segId][1] else '', required_padding[segId])
                if rider_results[segName] == '0:00:00':
                    rider_results[segName] = ''
            rider_results['T'] = format_timedelta(rdr['total'][0], required_padding['total'])
            all_res.append(rider_results)
        return json.dumps({'data': all_res}, indent=2)


def get_signups(ride_name):
    import pandas as pd
    responses = pd.read_csv('responses.csv')
    responses = responses[responses['Which reliability trails are you planning on riding?'].str.contains(ride_name)]
    if 'duro' in ride_name.lower():
        responses = responses[~responses['Strava profile URL'].isna()]
        signup_ids = list(responses['Strava profile URL'].apply(lambda x: x.split('/')[-1].strip()))
    elif 'trans' in ride_name.lower():
        responses = responses[~responses['Twitter handle'].isna()]
        signup_ids = list(responses['Twitter handle'].apply(lambda x: x[1:].strip()))
    else:
        raise ValueError('New ride type')
    return signup_ids


def format_timedelta(td, padding=2):
    from datetime import timedelta
    if not isinstance(td, timedelta):
        return td
    if td.days > 30:
        return 'DNF'
    hours = (td.days * 24) + (td.seconds / 3600)
    minutes = (td.seconds % 3600) / 60
    seconds = td.seconds % 60
    return ('{:0' + str(padding) + 'd}H {:02d}M {:02d}S').format(hours, minutes, seconds)


def to_s3(path, body):
    import boto3
    s3 = boto3.resource('s3')
    s3.Object('bikerid.es', path).put(Body=body, ContentType='application/json')


if __name__ == "__main__":
    run_manual_poll()
