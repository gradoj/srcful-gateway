# Docker Compose Version of the Gateway

This currently publishes a web-server at port 80 (if running through docker-compose, alt 5000 if running in local mode). It currently

* Simulates reading the frequency at 10Hz (goal)
* Harvests energy and asks the api for a name at 0.1 Hz (goal)
* Checks for web-requests at 1Hz (goal) to be reasonably responsive

## Development

In general strive for defining parameter types and return types.

### Testing
We use the pytest testing framework for automated testing (https://docs.pytest.org/en/7.2.x/getting-started.html#get-started).

Test modules are placed under `/test` and mirror the structure of the main project. Tests are executed by running:  
`pytest`

Integration in VSCode can be achieved by installing *Python Test Explorer for Visual Studio Code* add the following to your `./vscode/launch.json` configuration to enable *debugging* of tests.

```
{
  "name": "Debug test",
  "type": "python",
  "request": "attach",
  "console": "externalTerminal",
  "justMyCode": false,
  "stopOnEntry": true,
  "envFile": "${workspaceFolder}/.env.test",
  "purpose": [
    "debug-test"
  ]
}
```

### /server
The crypto stuff is partially mocked and does not require the libs to be installed as this does not seem to work well in a windows based container environment (even though the container itself runs linux...). This should handle iteself gracefully in the code.

Not all functions in the crypto lib have been fixed so pay attention to possible errors you get.

To start a local dev version of the gw you can simply do:  
`docker-commpose -f docker-compose-no_crypt.yml up`

or you can run the main module with python directly from the parent directory of `server` (this can be a good idea for debugging).:  
`python -m server.__main__`  

We need to run this as a module as there are dependencies between some packages/modules and they need a common root package (server).

### /modbus_slave
This is the directory that contains simulation servers of all inverters. This is started with docker-compose-no_crypt or you can start it locally using pythion (this seems painfully slow on windows for some reason). Alternativealy you run the docker container (create it with `docker-compose build` first):

`docker run -p 502:502 sourcefulgateway_inverter`

Don't forget to change the inverter host to `localhost` in `app.py`

## Deployment
Deploy using `balena push` - this will use the normal `docker-compose.yml`

## Design
The current design is task bases with a priority queue. The idea is that a task is scheduled to happen at a certain time. This allows for fine grained control and adjustment of task times/delays etc. The downside is that tasks cannot be blocking so IO operations typically need threading. Though this is rater easy to do and there are also some helper classes for common tasks that require threading.

On top of the task-engine we can put a state machine so that it becomes easier to know what tasks are high prio in different contexts.