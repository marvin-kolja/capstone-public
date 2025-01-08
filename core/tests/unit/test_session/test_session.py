import uuid
from unittest.mock import MagicMock, patch

import pytest

from core.device.i_device import IDevice
from core.exceptions.i_device import DeviceNotReadyForDvt
from core.test_session.session import Session
from core.test_session.session_state import ExecutionStepState
from tests.unit.test_session.conftest import mock_execution_plan


@pytest.fixture
def mock_i_device():
    return MagicMock(
        spec=IDevice,
        paired=True,
        developer_mode_enabled=True,
        product_version="18.0",
        ddi_mounted=True,
    )


class TestSession:
    def test_init(self, mock_execution_plan):
        """
        GIVEN: A device, execution plan, output dir, and session id

        WHEN: Initializing a test session

        THEN: All instance arguments should be initialized correctly
        """
        session_id_mock = MagicMock(spec=uuid.UUID)
        mock_device = MagicMock(spec=IDevice)
        mock_output_dir = MagicMock(spec=str)

        session = Session(
            execution_plan=mock_execution_plan,
            session_id=session_id_mock,
            device=mock_device,
            output_dir=mock_output_dir,
        )

        assert session._execution_plan == mock_execution_plan
        assert session._session_id == session_id_mock
        assert session._device == mock_device
        assert session._output_dir == mock_output_dir
        assert session._i_services._IServices__device == mock_device
        assert (
            session._session_state._SessionState__execution_plan == mock_execution_plan
        )
        assert session._session_state._SessionState__session_id == session_id_mock

    @pytest.mark.asyncio
    async def test_run(self):
        """
        GIVEN: A test session

        WHEN: Running the test session

        THEN: The session should prepare and run the execution plan
        """
        session = Session(
            execution_plan=MagicMock(),
            session_id=MagicMock(),
            device=MagicMock(),
            output_dir=MagicMock(),
        )

        with patch.object(session, "_prepare") as mock_prepare, patch.object(
            session, "_run_execution_plan"
        ) as mock_run_execution_plan:
            await session.run()

            mock_prepare.assert_awaited_once()
            mock_run_execution_plan.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_prepare(
        self, mock_i_device, mock_execution_plan, mock_execution_step
    ):
        """
        GIVEN: A test session

        WHEN: Preparing the test session

        THEN: The device should be checked if ready for use with dvt
        AND: It should not raise any exceptions as execution plan is valid
        """
        mock_execution_plan.execution_steps = [mock_execution_step]

        session = Session(
            execution_plan=mock_execution_plan,
            session_id=MagicMock(),
            device=mock_i_device,
            output_dir=MagicMock(),
        )

        with patch.object(
            mock_i_device, "check_dvt_ready"
        ) as mock_check_device_readiness:
            await session._prepare()

            mock_check_device_readiness.assert_called_once()

    @pytest.mark.asyncio
    async def test_prepare_device_not_ready(
        self,
        mock_i_device,
        mock_execution_plan,
        mock_execution_step,
    ):
        """
        GIVEN: A test session
        AND: A device that is not ready for use with dvt

        WHEN: Preparing the test session

        THEN: It should raise a DeviceNotReadyForDvt exception
        """
        mock_i_device.check_dvt_ready.side_effect = DeviceNotReadyForDvt

        mock_execution_plan.execution_steps = [mock_execution_step]

        session = Session(
            execution_plan=mock_execution_plan,
            session_id=MagicMock(),
            device=mock_i_device,
            output_dir=MagicMock(),
        )

        with pytest.raises(DeviceNotReadyForDvt):
            await session._prepare()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("steps", [None, []])
    async def test_prepare_invalid_execution_plan(
        self,
        mock_i_device,
        mock_execution_plan,
        steps,
    ):
        """
        GIVEN: A test session
        AND: An invalid execution plan

        WHEN: Preparing the test session

        THEN: It should raise a ValueError
        """
        mock_execution_plan.execution_steps = steps

        session = Session(
            execution_plan=mock_execution_plan,
            session_id=MagicMock(),
            device=mock_i_device,
            output_dir=MagicMock(),
        )

        with pytest.raises(ValueError):
            await session._prepare()

    @pytest.mark.asyncio
    async def test_run_execution_plan(
        self,
        mock_execution_plan,
        mock_execution_step,
    ):
        """
        GIVEN: A test session

        WHEN: Running the execution plan

        THEN: It should call the sessions `next_execution_step` method the correct number of times
        """
        mock_execution_plan.execution_steps = [mock_execution_step for i in range(100)]

        session = Session(
            execution_plan=mock_execution_plan,
            session_id=MagicMock(),
            device=MagicMock(),
            output_dir=MagicMock(),
        )

        with patch.object(
            session._session_state, "next_execution_step"
        ) as mock_next_step, patch.object(
            session, "_run_execution_step"
        ) as mock_run_execution_step:
            await session._run_execution_plan()
            mock_next_step.assert_called()
            assert mock_next_step.call_count == 100
            assert mock_run_execution_step.await_count == 100
