from unittest.mock import patch

from trunk.events.tasks import dispatch_event_task


@patch("trunk.events.tasks.event_dispatcher")
def test_dispatch_event_task(mock_dispatcher):
    event_type = "TEST_EVENT"
    payload = {"data": 123}

    dispatch_event_task(event_type, payload)

    mock_dispatcher.dispatch_sync.assert_called_once_with(event_type, payload)
