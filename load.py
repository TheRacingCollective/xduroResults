from stravalib.client import Client
from datetime import datetime, timedelta
import pytz
import os

def runPoll(event, context):
    access_token = os.environ.get('strava_access_token', '')
    s = [('XDP-1', 15800992),
         ('XDP-2', 15801621),
         ('XDP-3', 15801674),
         ('XDP-4', 15801749),
         ('XDP-5', 15801763)]
    x = XduroResultBuilder(access_token)
    r = ResultsPrinter()
    html = r.format_html(s, x.get_results_for(s))
    toS3(html)

def toS3(html):
    import boto3
    s3 = boto3.resource('s3')
    s3.Object('bikerid.es', 'xduro/index.html').put(Body=html, ContentType='text/html')

class XduroResultBuilder(object):

    def __init__(self, access_token):
        self.client = Client()
        self.client.access_token = access_token
        self.club = 238976
        self.timeFrame = 'this_month'
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
            efforts = self.client.get_segment_leaderboard(segment, timeframe=self.timeFrame, club_id=self.club)
            results_by_segment[segment] = {e.athlete_name: e.elapsed_time for e in efforts}
        return results_by_segment


class ResultsPrinter(object):

    header = '''<html>
      <head>
        <title>XDURO Results</title>
        <meta charset="UTF-8">
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css" integrity="sha384-WskhaSGFgHYWDcbwN70/dfYBj47jz9qbsMId/iRN3ewGhXQFZCSftd1LZCfmhktB" crossorigin="anonymous">
      </head>
      <body>
        <table class="table table-striped">
          <thead>
            <tr>
              <th scope="col">Rider</th>
    '''

    mid = '''          <th scope="col">Total</th>
            </tr>
          </thead>
          <tbody>
    '''

    footer = '''      </tbody>
        </table>
        <i>Classement provisoire, &agrave; {}</i>
        <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/js/bootstrap.min.js" integrity="sha384-smHYKdLADwkXOn1EmN1qk/HfnUcbVRZyYmZ4qpPea6sjB/pTJ0euyQp0Mk8ck+5T" crossorigin="anonymous"></script>
      </body>
    </html>'''

    def format_html(self, segments, results):
        html = self.header
        for name, segId in segments:
            html += '          <th scope="col"><a href="https://www.strava.com/segments/{}">{}</a></th>\n'.format(segId,name)
        html += self.mid
        for result in results:
            html += '        <tr>\n          <th scope=\'row\'>{}</th>\n'.format(result['rider'])
            for name, segId in segments:
                format_string = '          <td>{}</td>\n' if result[segId][1] else '          <td><i>{}</i></td>\n'
                html += format_string.format(result[segId][0])
            format_string = '          <td>{}</td>\n' if result['total'][1] else '          <td><i>{}</i></td>\n'
            html += format_string.format(result['total'][0])
        update_time = '{:%H:%M}'.format(datetime.utcnow().replace(tzinfo=pytz.timezone('Europe/London')))
        html += self.footer.format(update_time)
        return html
