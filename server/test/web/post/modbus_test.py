import pytest
import queue
from unittest.mock import Mock, patch
from server.web.handler.post.modbus import Handler
from server.tasks.modbusWriteTask import ModbusWriteTask, log
from server.web.handler.requestData import RequestData
from server.blackboard import BlackBoard


# Test that doPost parses commands into tasks correctly 
def test_do_post():
    inverter = Mock()
    bb = BlackBoard()
    bb.inverters.add(inverter)

    handler = Handler()

    post_data = {
        'commands': [
            {
                'type': 'write',
                'startingAddress': '10',
                'values': ['0', '1', '2']
            },
            {
                'type': 'pause',
                'duration': '2000',
            }
        ]
    }

    
    tasks = queue.Queue()
    rd = RequestData(bb, {}, {}, post_data, tasks)
    response_code, response_body = handler.doPost(rd)
    
    assert tasks.qsize() == 1
    task = tasks.get_nowait()
    assert isinstance(task, ModbusWriteTask)
    assert isinstance(task.commands[0], ModbusWriteTask.WriteCommand)
    assert isinstance(task.commands[1], ModbusWriteTask.PauseCommand)

# Test error handling for missing 'commands' field
def test_missing_commands():
    handler = Handler()
    rd = RequestData(BlackBoard(), {}, {}, {}, queue.Queue())
    response_code, response_body = handler.doPost(rd)
    assert response_code == 400
# Test error handling for Missing inverter field
def test_missing_inverter():
    handler = Handler()
    rd = RequestData(BlackBoard(), {}, {}, {'commands': []}, queue.Queue())
    response_code, response_body = handler.doPost(rd)
    assert response_code == 400

# Test that malformed command objects are handled and an error is returned
def test_malformed_commands():
    handler = Handler()

    

    def requestData(data):
        bb = BlackBoard()
        bb.inverters.add(Mock())
        return RequestData(bb, {}, {}, data, queue.Queue())

    # Command without required 'type' field
    post_data_no_type = {'commands': [{}]}
    response_code, response_body = handler.doPost(requestData(post_data_no_type))
    assert response_code == 500

    # Unrecognized command type
    post_data_bad_type = {'commands': [{'type': 'not_a_real_command_type'}]}
    response_code, response_body = handler.doPost(requestData(post_data_bad_type))
    assert response_code == 500

    # Write command without 'startingAddress'
    post_data_no_start = {'commands': [{'type': 'write', 'values': ['0', '1', '2']}]}
    response_code, response_body = handler.doPost(requestData(post_data_no_start))
    assert response_code == 500

    # Write command without 'values' field
    post_data_no_values = {'commands': [{'type': 'write', 'startingAddress': '10'}]}
    response_code, response_body = handler.doPost(requestData(post_data_no_values))
    assert response_code == 500

    # Pause command without 'duration' field
    post_data_no_duration = {'commands': [{'type': 'pause'}]}
    response_code, response_body = handler.doPost(requestData(post_data_no_duration))
    assert response_code == 500