from typing import Callable

def inverterForm():
  return """
  <h1>Inverter Form</h1>

    <form id="inverter-form">
        <label for="ip">Inverter IP:</label>
        <input type="text" id="ip" name="ip"><br><br>

        <label for="port">Inverter Port:</label>
        <input type="text" id="port" name="port"><br><br>

        <label for="type">Inverter Type:</label>
        <input type="text" id="type" name="type"><br><br>

        <button type="submit">Submit</button>
    </form>

    <script>
        const form = document.querySelector('#inverter-form');

        form.addEventListener('submit', async (event) => {
            event.preventDefault();

            const formData = new FormData(form);
            const data = {
                ip: formData.get('ip'),
                port: formData.get('port'),
                type: formData.get('type')
            };

            const response = await fetch('/api/inverter', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                console.log('Inverter data submitted successfully!');
            } else {
                console.error('Failed to submit inverter data:', response.status);
            }
        });
    </script>"""

class Handler:

  def doGet(self, stats: dict, timeMSFunc:Callable, chipInfoFunc:Callable):
    freqReads = stats['freqReads'] if 'freqReads' in stats else 0
    energyHarvested = stats['harvest'] if 'harvest' in stats else 0
    energyTransported = 0
    if 'harvestTransports' in stats:
      energyTransported = stats['harvestTransports']
    startTime = stats['startTime']

 
    ret = "<html><head><title>Srcful Energy Gateway</title></head>"
    ret += "<body>"
    ret += "<h1>Srcful Energy Gateway</h1>"
    ret += f"<h2>{stats['name']}</h2>"

    ret += f"<p>chipInfo: {chipInfoFunc()}</p>"

    elapsedTime = timeMSFunc() - startTime

    # convert elapsedTime to days, hours, minutes, seconds in a tuple
    days, remainder = divmod(elapsedTime // 1000, 60*60*24)
    hours, remainder = divmod(remainder, 60*60)
    minutes, seconds = divmod(remainder, 60)

    # output the gateway current uptime in days, hours, minutes, seconds
    ret += f"<p>Uptime (days, hours, minutes, seconds): {(days, hours, minutes, seconds)}</p>"

    ret += inverterForm()

    ret += f"<p>freqReads: {freqReads} in {elapsedTime} ms<br/>"
    ret += f"average freqReads: {freqReads / elapsedTime * 1000} per second</p>"

    ret += f"last freq: {stats['lastFreq'] if 'lastFreq' in stats else 0} Hz</p>"

    ret += f"<p>energyHarvested: {energyHarvested} in {elapsedTime} ms</br>"
    ret += f"average energyHarvested: {energyHarvested / elapsedTime * 1000} per second</p>"

    ret += f"<p>energyTransported: {energyTransported} in {elapsedTime} ms</br>"
    ret += f"average energyTransported: {energyTransported / elapsedTime * 1000} per second</p>"
    
    ret += f"ALL: {stats}</p>"

    ret += "</body></html>"

    return ret
