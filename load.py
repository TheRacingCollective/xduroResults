from stravalib.client import Client
from datetime import timedelta
import boto3

header = '''<html>
    <head>
        <title>'Duro Results</title>
        <meta charset="UTF-8">
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css" integrity="sha384-WskhaSGFgHYWDcbwN70/dfYBj47jz9qbsMId/iRN3ewGhXQFZCSftd1LZCfmhktB" crossorigin="anonymous">
    </head>
    <body>
    <table class="table table-striped">
  <thead>
    <tr>
          <th scope="col">Rider</th>'''
mid = '''      <th scope="col">Total</th>
    </tr>
  </thead>
  <tbody>'''
footer = '''  </tbody>
</table>
        <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/js/bootstrap.min.js" integrity="sha384-smHYKdLADwkXOn1EmN1qk/HfnUcbVRZyYmZ4qpPea6sjB/pTJ0euyQp0Mk8ck+5T" crossorigin="anonymous"></script>
    </body>
</html>'''

def runPoll(event, context):
    client = Client()
    client.access_token = os.environ.get('strava_access_token', '')
    segments = [('XDS1',15888276), ('XDS2',15781529), ('XDS3',15781535), ('XDS4',15781545), ('XDS5',15781550)]
    riders = {}

    for club in [238976]:
        leaderboards = {}
        maxTimes = {}
        for _, segment in segments:
            leaderboards[segment] = client.get_segment_leaderboard(segment, timeframe='this_week', top_results_limit=50, club_id=club)
            maxTimes[segment] = timedelta(0)
        for segment, leaderBoard in leaderboards.items():
            for effort in leaderBoard.entries:
                if '2018-09-0' not in str(effort.start_date):
                    pass
                riderEfforts = riders.get( effort.athlete_name, {} )
                riderEfforts[ segment ] = effort.elapsed_time
                riders[ effort.athlete_name ] = riderEfforts
                if effort.elapsed_time > maxTimes[segment]:
                    maxTimes[segment] = effort.elapsed_time

    resultRows = {}
    for rider, results in riders.items():
        gotAllResults = True
        totalTime = timedelta(0)
        thisRow = '<tr><th scope=\'row\'>{}</th>'.format( rider )
        for _, segment in segments:
            result = results.get( segment, maxTimes[segment] )
            gotAllResults = gotAllResults and segment in results
            totalTime = ( totalTime + result )
            if segment in results:
                thisRow += '<td>{}</td>'.format(result)
            else:
                thisRow += '<td><i>{}</i></td>'.format(result)
        if gotAllResults:
            thisRow += '<td>{}</td></tr>'.format(totalTime)
        else:
            thisRow += '<td><i>{}</i></td></tr>'.format(totalTime)
        resultRows[ totalTime  ] = thisRow


    html = header
    for segment in segments:
        html += '<th scope="col"><a href="https://www.strava.com/segments/{}">{}</a></th>'.format(segment[1], segment[0])
    html += mid
    for result in sorted(resultRows.keys()):
        html += resultRows[result]
    html += footer

    s3 = boto3.resource('s3')
    s3.Object('bikerid.es', 'xduro/index.html').put(Body=html, ContentType='text/html')