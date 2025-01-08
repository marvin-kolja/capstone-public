import uuid
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from core.device.i_device import IDevice
from core.device.i_services import IServices
from core.exceptions.i_device import DeviceNotReadyForDvt
from core.subprocesses.xcodebuild_command import IOSDestination
from core.subprocesses.xctrace_command import Instrument
from core.test_session.metrics import Metric
from core.test_session.plan import StepTestCase
from core.test_session.session import Session
from core.test_session.session_state import ExecutionStepState
from core.test_session.session_step_hasher import hash_session_execution_step
from core.test_session.xctestrun import XcTestTarget
from tests.conftest import fake_udid
from tests.unit.conftest import i_device_mocked_lockdown
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
        AND: It should call the step states `set_running` and `set_completed` methods the correct number of times
        """
        mock_execution_plan.execution_steps = [mock_execution_step for i in range(100)]

        session = Session(
            execution_plan=mock_execution_plan,
            session_id=MagicMock(),
            device=MagicMock(),
            output_dir=MagicMock(),
        )

        mock_execution_step_state = MagicMock(spec=ExecutionStepState)

        with patch.object(
            session._session_state,
            "next_execution_step",
            return_value=mock_execution_step_state,
        ) as mock_next_step, patch.object(
            session, "_run_execution_step"
        ) as mock_run_execution_step:
            await session._run_execution_plan()

            assert mock_next_step.call_count == 100
            assert mock_run_execution_step.await_count == 100
            assert mock_execution_step_state.set_running.call_count == 100
            assert mock_execution_step_state.set_completed.call_count == 100

    @pytest.mark.parametrize("end_on_failure", [True, False])
    @pytest.mark.asyncio
    async def test_run_execution_plan_failure(
        self,
        mock_execution_plan,
        mock_execution_step,
        end_on_failure,
    ):
        """
        GIVEN: A test session

        WHEN: Running the execution plan and an exception occurs

        THEN: The session should set the step state to failed
        AND: If the test plan is set to end on failure, it should break the loop
        """
        mock_execution_plan.execution_steps = [mock_execution_step, mock_execution_step]
        # Two steps to ensure the loop breaks after the first failure

        mock_execution_plan.test_plan.end_on_failure = end_on_failure

        session = Session(
            execution_plan=mock_execution_plan,
            session_id=MagicMock(),
            device=MagicMock(),
            output_dir=MagicMock(),
        )

        mock_execution_step_state = MagicMock(spec=ExecutionStepState)

        with patch.object(
            session._session_state,
            "next_execution_step",
            return_value=mock_execution_step_state,
        ) as mock_next_step, patch.object(
            session, "_run_execution_step"
        ) as mock_run_execution_step:
            mock_run_execution_step.side_effect = Exception

            await session._run_execution_plan()

            if end_on_failure:
                assert mock_run_execution_step.await_count == 1
                assert mock_execution_step_state.set_failed.call_count == 1
                assert mock_next_step.call_count == 1
            else:
                assert mock_run_execution_step.await_count == 2
                assert mock_execution_step_state.set_failed.call_count == 2
                assert mock_next_step.call_count == 2

    @pytest.mark.parametrize(
        "recording_start_strategy",
        ["launch", "attach"],
    )
    @pytest.mark.parametrize(
        "reinstall_app",
        [True, False],
    )
    @pytest.mark.parametrize(
        "app_bundle_id, ui_app_bundle_id",
        [
            ("com.example.app", None),
            ("com.example.app", "com.example.ui_test_app"),
        ],
    )
    @pytest.mark.parametrize(
        "apps_installed",
        [
            True,
            False,
        ],
    )
    @pytest.mark.asyncio
    async def test_run_execution_step(
        self,
        mock_execution_plan,
        mock_execution_step,
        mock_i_device,
        fake_udid,
        recording_start_strategy,
        reinstall_app,
        app_bundle_id,
        ui_app_bundle_id,
        apps_installed,
    ):
        """
        GIVEN: A test session

        WHEN: Running an execution step

        THEN: It should uninstall the app if it is already installed and the reinstall_app flag is set
        AND: It should install the app if it is not already installed
        AND: It should record the metrics using the correct strategy (launch or attach) and parameters
        AND: It should run the test cases using the correct parameters

        TODO: In the future the method should be split into smaller methods so this test can be a lot less messy
        """
        output_dir = "/tmp/output"
        session_id = uuid.uuid4()
        app_bundle_ids = (
            [app_bundle_id, ui_app_bundle_id] if ui_app_bundle_id else [app_bundle_id]
        )

        session = Session(
            execution_plan=mock_execution_plan,
            session_id=session_id,
            device=mock_i_device,
            output_dir=output_dir,
        )

        mock_i_device.lockdown_service = MagicMock(udid=fake_udid)

        mock_test_target = MagicMock(
            spec=XcTestTarget,
            app_path="/tmp/example.app",
            ui_test_app_path="/tmp/ui_test_example.app" if ui_app_bundle_id else None,
        )

        mock_execution_plan.info_plists = {
            "/tmp/example.app": MagicMock(CFBundleIdentifier=app_bundle_id),
        }
        if ui_app_bundle_id:
            mock_execution_plan.info_plists["/tmp/ui_test_example.app"] = MagicMock(
                CFBundleIdentifier=ui_app_bundle_id
            )

        mock_test_case = MagicMock(
            spec=StepTestCase, xctest_id="TestTarget/TestClass/testMethod"
        )

        mock_execution_step.plan_repetition = 0
        mock_execution_step.step_repetition = 0
        mock_execution_step.recording_start_strategy = recording_start_strategy
        mock_execution_step.reinstall_app = reinstall_app
        mock_execution_step.metrics = [Metric.cpu]
        mock_execution_step.instruments = [Instrument.activity_monitor]
        mock_execution_step.test_cases = [mock_test_case]
        mock_execution_step.xctest_ids = [mock_test_case.xctest_id]
        mock_execution_step.test_target = mock_test_target
        mock_execution_step.xctestrun_config = (
            mock_execution_plan.test_plan.xctestrun_config
        )

        with patch.object(
            session, "_i_services", MagicMock(spec=IServices)
        ) as mock_i_services, patch(
            "core.test_session.session.Xctest.run_test"
        ) as mock_run_test, patch(
            "core.test_session.session.Xctrace.record_launch"
        ) as mock_record_launch, patch(
            "core.test_session.session.Xctrace.record_attach"
        ) as mock_record_attach:
            mock_i_services.list_installed_apps.return_value = (
                app_bundle_ids if apps_installed else []
            )
            mock_i_services.wait_for_app_pid.return_value = 1234
            await session._run_execution_step(mock_execution_step)
            mock_i_services.list_installed_apps.assert_called_once()

            if not apps_installed or reinstall_app:
                assert mock_i_services.install_app.call_count == len(app_bundle_ids)
            else:
                assert mock_i_services.install_app.call_count == 0

            if apps_installed and reinstall_app:
                assert mock_i_services.uninstall_app.call_count == len(app_bundle_ids)
            else:
                assert mock_i_services.uninstall_app.call_count == 0

            if mock_execution_step.recording_start_strategy == "launch":
                mock_record_launch.assert_called_once_with(
                    trace_path=f"{output_dir}/{hash_session_execution_step(session_id, mock_execution_step)}.trace",
                    instruments=[Instrument.activity_monitor],
                    app_to_launch=app_bundle_id,
                    append_trace=False,
                    device=fake_udid,
                )
            else:
                mock_record_attach.assert_called_once_with(
                    trace_path=f"{output_dir}/{hash_session_execution_step(session_id, mock_execution_step)}.trace",
                    instruments=[Instrument.activity_monitor],
                    pid=1234,
                    append_trace=False,
                    device=fake_udid,
                )

            mock_run_test.assert_called_once_with(
                xcresult_path=f"{output_dir}/{hash_session_execution_step(session_id, mock_execution_step)}.xcresult",
                test_configuration=mock_execution_plan.test_plan.xctestrun_config.test_configuration,
                xctestrun_path=mock_execution_plan.test_plan.xctestrun_config.path,
                only_testing=[mock_test_case.xctest_id],
                destination=IOSDestination(id=fake_udid),
            )
