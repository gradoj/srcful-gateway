import server.tasks.harvest as harvest
from unittest.mock import Mock, patch
import pytest

from server.blackboard import BlackBoard


def test_create_harvest():
    t = harvest.Harvest(0, BlackBoard(), None)
    assert t is not None


def test_create_harvest_transport():
    t = harvest.HarvestTransport(0, BlackBoard(), {}, "huawei")
    assert t is not None


def test_inverter_terminated():
    mock_inverter = Mock()
    mock_inverter.is_terminated.return_value = False

    t = harvest.Harvest(0, BlackBoard(), mock_inverter)
    t.execute(17)

    t.backoff_time = t.max_backoff_time
    t.inverter.read_harvest_data.side_effect = Exception("mocked exception")
    t.execute(17)

    assert mock_inverter.close.call_count == 1
    assert mock_inverter.open.call_count == 0

    t.inverter.is_open.return_value = False

    t.execute(17)

    assert mock_inverter.close.call_count == 1
    assert mock_inverter.open.call_count == 1


def test_execute_harvest():
    mock_inverter = Mock()
    registers = {"1": "1717"}
    mock_inverter.read_harvest_data.return_value = registers
    mock_inverter.is_terminated.return_value = False

    t = harvest.Harvest(0, BlackBoard(), mock_inverter)
    ret = t.execute(17)
    assert ret is t
    assert t.barn[17] == registers
    assert len(t.barn) == 1
    assert t.time == 17 + 1000


def test_execute_arvest_x10():
    # in this test we check that we get the desired behavior when we execute a harvest task 10 times
    # the first 9 times we should get the same task back
    # the 10th time we should get a list of 2 tasks back
    mock_inverter = Mock()
    registers = [{"1": 1717 + x} for x in range(10)]
    t = harvest.Harvest(0, BlackBoard(), mock_inverter)
    mock_inverter.is_terminated.return_value = False

    for i in range(9):
        mock_inverter.read_harvest_data.return_value = registers[i]
        ret = t.execute(i)
        assert ret is t
        assert t.barn[i] == registers[i]
        assert len(t.barn) == i + 1

    mock_inverter.read_harvest_data.return_value = registers[9]
    ret = t.execute(17)
    assert len(t.barn) == 0
    assert ret is not t
    assert len(ret) == 2
    assert ret[0] is t
    assert ret[1] is not t
    assert ret[1].barn == {
        0: registers[0],
        1: registers[1],
        2: registers[2],
        3: registers[3],
        4: registers[4],
        5: registers[5],
        6: registers[6],
        7: registers[7],
        8: registers[8],
        17: registers[9],
    }


def test_adaptive_backoff():
    mock_inverter = Mock()
    mock_inverter.is_terminated.return_value = False

    t = harvest.Harvest(0, BlackBoard(), mock_inverter)
    t.execute(17)

    assert t.backoff_time == 1000

    # Mock one failed poll -> We back off by 2 seconds instead of 1
    t.inverter.read_harvest_data.side_effect = Exception("mocked exception")
    t.execute(17)

    assert t.backoff_time == 2000

    # Save the initial minbackoff_time to compare with the actual minbackoff_time later on
    backoff_time = t.backoff_time

    # Number of times we want to reach max backoff time, could be anything
    num_of_lost_connections = 900

    # Now we fail until we reach max backoff time
    for _i in range(num_of_lost_connections):
        t.execute(17)
        backoff_time *= 2

        if backoff_time > 256000:
            backoff_time = 256000

        assert t.backoff_time == backoff_time
        assert t.backoff_time <= 256000


def test_adaptive_poll():
    mock_inverter = Mock()
    mock_inverter.is_terminated.return_value = False

    t = harvest.Harvest(0, BlackBoard(), mock_inverter)
    t.execute(17)

    assert t.backoff_time == 1000

    t.inverter.read_harvest_data.side_effect = Exception("mocked exception")
    t.backoff_time = t.max_backoff_time
    t.execute(17)

    assert t.backoff_time == 256000

    t.inverter.read_harvest_data.side_effect = None
    t.execute(17)

    assert t.backoff_time == 230400.0


def test_execute_harvest_no_transport():
    mock_inverter = Mock()
    mock_inverter.is_terminated.return_value = False
    registers = [{"1": 1717 + x} for x in range(10)]
    t = harvest.Harvest(0, {}, mock_inverter)

    for i in range(len(registers)):
        mock_inverter.read_harvest_data.return_value = registers[i]
        t.execute(i)

    # we should now have issued a transport and the barn should be empty
    assert t.transport is not None
    assert len(t.barn) == 0

    # we now continue to harvest but these should not be transported as the transport task is not executed
    for i in range(len(registers)):
        mock_inverter.read_harvest_data.return_value = registers[i]
        t.execute(i + 100)

    assert len(t.barn) == 10

    # finally we fake that the barn has been transported and we should get a new transport task
    # note that we only transport every 10th harvest
    t.transport.reply = "all done"
    for i in range(len(registers)):
        mock_inverter.read_harvest_data.return_value = registers[i]
        ret = t.execute(i + 200)
    assert len(t.barn) == 0
    assert ret is not t
    assert len(ret) == 2
    assert ret[0] is t
    assert ret[1] is not t


def test_execute_harvest_incremental_backoff_increasing():
    mock_inverter = Mock()
    mock_inverter.read_harvest_data.side_effect = Exception("mocked exception")
    mock_inverter.is_terminated.return_value = False
    t = harvest.Harvest(0, {}, mock_inverter)

    while t.backoff_time < t.max_backoff_time:
        old_time = t.backoff_time
        ret = t.execute(17)
        assert ret is t
        assert ret.backoff_time > old_time
        assert ret.time == 17 + ret.backoff_time

    assert ret.backoff_time == t.max_backoff_time


def test_execute_harvest_incremental_backoff_reset():
    mock_inverter = Mock()
    mock_inverter.read_harvest_data.side_effect = Exception("mocked exception")
    mock_inverter.is_terminated.return_value = False
    t = harvest.Harvest(0, {}, mock_inverter)

    while t.backoff_time < t.max_backoff_time:
        ret = t.execute(17)

    mock_inverter.read_harvest_data.side_effect = None
    mock_inverter.read_harvest_data.return_value = {"1": 1717}
    ret = t.execute(17)
    assert ret is t
    assert ret.time == 17 + ret.backoff_time


def test_execute_harvest_incremental_backoff_reconnect_on_max():
    mock_inverter = Mock()
    mock_inverter.read_harvest_data.side_effect = Exception("mocked exception")
    mock_inverter.is_terminated.return_value = False
    t = harvest.Harvest(0, {}, mock_inverter)

    while t.backoff_time < t.max_backoff_time:
        ret = t.execute(17)

        # assert that the inverter has not been closed and opened again
        assert mock_inverter.close.call_count == 0
    assert mock_inverter.open.call_count == 0

    ret = t.execute(17)
    assert ret is t

    t.inverter.is_open.return_value = False

    t.execute(17)

    # assert that inverter has been closed and opened again
    assert mock_inverter.close.call_count == 1
    assert mock_inverter.open.call_count == 1


@pytest.fixture
def mock_init_chip():
    pass


@pytest.fixture
def mock_build_jwt(data, inverter_type):
    pass


@pytest.fixture
def mock_release():
    pass


@patch("server.crypto.crypto.init_chip")
@patch("server.crypto.crypto.build_jwt")
@patch("server.crypto.crypto.release")
def test_data_harvest_transport_jwt(mock_release, mock_build_jwt, mock_init_chip):
    barn = {"test": "test"}
    inverter_type = "test"
    mock_build_jwt.return_value = {str(barn), inverter_type}

    instance = harvest.HarvestTransport(0, {}, barn, inverter_type)
    instance._data()

    mock_init_chip.assert_called_once()
    mock_build_jwt.assert_called_once_with(instance.barn, instance.inverter_type)
    mock_release.assert_called_once()


def test_on_200():
    # just make the call for now
    response = Mock()

    instance = harvest.HarvestTransport(0, {}, {}, "huawei")
    instance._on_200(response)


def test_on_error():
    # just make the call for now
    response = Mock()
    instance = harvest.HarvestTransport(0, {}, {}, "huawei")
    instance._on_error(response)
