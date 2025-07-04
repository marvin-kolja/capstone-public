"""
Test the whole process from building the app to parsing the test results (.trace, .xcresult).
"""

import contextlib
import os
import pathlib
import tempfile
import uuid

import pytest

from core.xc.app_builder import (
    AppBuilder,
    XcodeBuildArtefacts,
    XcodeTestBuildArtefacts,
)
from core.device.i_device_manager import IDeviceManager
from core.device.i_services import IServices
from core.xc.commands.xcodebuild_command import (
    IOSDestination,
    XcodebuildCommand,
)
from core.test_session.execution_plan import ExecutionPlan
from core.test_session.metrics import Metric
from core.test_session.plan import (
    SessionTestPlan,
    XctestrunConfig,
    PlanStep,
    StepTestCase,
)
from core.test_session.session import Session
from core.test_session.session_step_hasher import hash_session_execution_step
from core.xc.commands.xctrace_command import XctraceCommand
from core.xc.xcresult.xcresulttool import XcresultTool
from core.xc.xctest import Xctest
from core.xc.xc_project import XcProject
from core.xc.xctrace.xctrace_interface import Xctrace
from core.xc.xctrace.xml_parser import Schema


@pytest.fixture(scope="module", autouse=True)
def fix_xcodebuild_sudo_issue(build_output_dir, test_output_dir):
    """
    It seems when executing xcodebuild using sudo it is unable to it is unable to automatically sign applications during
    the build process. This workaround always uses the current user when executing xcodebuild in a subprocess.

    It also seems that xctrace may also have issues executing as sudo. This workaround also uses the current user when
    executing xctrace in a subprocess.

    This leads to another issue as then the process does not have access to the paths created by the sudo user. Thus, we
    also need to change the permission of:
    - `test_output_dir`
    - temporary dir for the test enumeration command
    """
    if os.geteuid() == 0:
        xcodebuild_command_parse = XcodebuildCommand.parse
        xctrace_command_parse = XctraceCommand.parse

        def create_new_parse(original_parse):
            def new_parse(self):
                parsed_command = original_parse(self)
                additional_args = ["sudo", "-u", os.getenv("SUDO_USER")]
                return additional_args + parsed_command

            return new_parse

        XcodebuildCommand.parse = create_new_parse(xcodebuild_command_parse)
        XctraceCommand.parse = create_new_parse(xctrace_command_parse)

        xctest__temporary_file_path = Xctest._temporary_file_path

        @contextlib.contextmanager
        def _temporary_file_path(suffix: str = ""):
            with xctest__temporary_file_path(suffix) as tmp_file:
                if os.geteuid() == 0:
                    tmp_file.parent.chmod(0o777)
                yield tmp_file

        Xctest._temporary_file_path = _temporary_file_path

        test_output_dir_path = test_output_dir
        for path in [test_output_dir_path]:
            if path.exists():
                # if the dir is created by sudo, the current user does not have access to it thus we need to change the
                # permissions
                if path.stat().st_uid == 0:
                    os.chmod(path, 0o777)
                if path.parent.stat().st_uid == 0:
                    os.chmod(path.parent, 0o777)

        yield

        XcodebuildCommand.parse = xcodebuild_command_parse
        XctraceCommand.parse = xctrace_command_parse
        Xctest._temporary_file_path = xctest__temporary_file_path
    else:
        yield


@pytest.fixture(scope="module")
def tmp_dir():
    with tempfile.TemporaryDirectory(delete=False) as tmp_dir:
        yield tmp_dir


@pytest.fixture(scope="module")
def build_output_dir():
    test_root = pathlib.Path(__file__).parent.parent
    build_path = test_root.joinpath("test_data/build_output_dir")
    if not build_path.exists():
        pytest.fail(f"Build output dir does not exist: {build_path}")
    return build_path.resolve().as_posix()


@pytest.fixture(scope="module")
def test_output_dir(tmp_dir):
    test_path = pathlib.Path(tmp_dir, "test_output_dir")
    test_path.mkdir()
    yield test_path


@pytest.fixture(scope="module")
def xc_project():
    path_to_example_app = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "../../../misc/example_apps/RP Swift/RP Swift.xcodeproj",
    )

    return XcProject(path_to_example_app)


@pytest.fixture(scope="module")
async def xc_project_details(xc_project):
    return await xc_project.list()


@pytest.fixture(scope="module")
async def xc_project_scheme(xc_project_details):
    if "RP Swift" not in xc_project_details.schemes:
        pytest.fail(
            f"Expected scheme 'RP Swift' in project, got: {xc_project_details.schemes}"
        )
    return "RP Swift"


@pytest.fixture(scope="module")
async def xc_project_configuration(xc_project_details):
    if "Release" not in xc_project_details.configurations:
        pytest.fail(
            f"Expected configuration 'Release' in project, got: {xc_project_details.configurations}"
        )
    return "Release"


@pytest.fixture(scope="module")
async def xc_project_test_plans(xc_project, xc_project_scheme):
    return await xc_project.xcode_test_plans(scheme=xc_project_scheme)


@pytest.fixture(scope="module")
async def xc_project_test_plan(xc_project_test_plans):
    return xc_project_test_plans[0]


@pytest.fixture(scope="module")
async def ios_device(device_udid, tunnel_server_subprocess):
    device_manager = IDeviceManager()
    device = device_manager.get_device(udid=device_udid)
    await device.establish_trusted_channel()
    return device


@pytest.fixture(scope="module")
def app_builder(xc_project):
    return AppBuilder(xc_project)


@pytest.fixture(scope="module")
def ios_destination(device_udid):
    return IOSDestination(id=device_udid)


@pytest.fixture(scope="module")
def build_app_artefacts(
    request,
    build_output_dir,
    xc_project_scheme,
    xc_project_configuration,
):
    if not AppBuilder.products_dir(build_output_dir).exists():
        return pytest.fail("Must have executed 'test_build' before this fixture.")
    return XcodeBuildArtefacts(
        scheme=xc_project_scheme,
        configuration=xc_project_configuration,
        build_dir=AppBuilder.build_dir(build_output_dir).as_posix(),
        products_dir=AppBuilder.products_dir(build_output_dir).as_posix(),
        iphoneos_dir=AppBuilder.iphoneos_dir(
            build_output_dir, xc_project_configuration
        ).as_posix(),
    )


@pytest.fixture(scope="module")
def build_app_for_testing_artefacts(
    request,
    build_output_dir,
    xc_project_scheme,
    xc_project_configuration,
    xc_project_test_plan,
):
    try:
        xctestrun_path = AppBuilder.xctestrun_file(
            build_output_dir, scheme=xc_project_scheme, test_plan=xc_project_test_plan
        )
    except FileNotFoundError:
        return pytest.fail("Must have executed 'test_build' before this fixture.")
    return XcodeTestBuildArtefacts(
        scheme=xc_project_scheme,
        configuration=xc_project_configuration,
        build_dir=AppBuilder.build_dir(build_output_dir).as_posix(),
        products_dir=AppBuilder.products_dir(build_output_dir).as_posix(),
        iphoneos_dir=AppBuilder.iphoneos_dir(
            build_output_dir, xc_project_configuration
        ).as_posix(),
        xctestrun_path=xctestrun_path.as_posix(),
        test_plan=xc_project_test_plan,
    )


@pytest.fixture(scope="module")
def xc_test_case():
    return "RP SwiftUITests/XUITest/testLottieAnimation"


@pytest.mark.real_device
@pytest.mark.asyncio
async def test_build(
    xc_project_details,
    app_builder,
    xc_project_scheme,
    xc_project_configuration,
    build_output_dir,
    ios_destination,
    xc_project_test_plan,
):
    build_for_testing_artefacts = await app_builder.build_for_testing(
        scheme=xc_project_scheme,
        test_plan=xc_project_test_plan,
        configuration=xc_project_configuration,
        output_dir=build_output_dir,
        destination=ios_destination,
        clean=True,
    )
    build_artefacts = await app_builder.build(
        scheme=xc_project_scheme,
        configuration=xc_project_configuration,
        output_dir=build_output_dir,
        destination=ios_destination,
    )

    assert build_artefacts.build_dir == build_for_testing_artefacts.build_dir
    assert build_artefacts.products_dir == build_for_testing_artefacts.products_dir
    assert build_artefacts.scheme == build_for_testing_artefacts.scheme
    assert build_artefacts.configuration == build_for_testing_artefacts.configuration
    assert build_artefacts.iphoneos_dir == build_for_testing_artefacts.iphoneos_dir

    assert pathlib.Path(build_artefacts.build_dir).exists()
    assert pathlib.Path(build_artefacts.products_dir).exists()
    assert pathlib.Path(build_artefacts.iphoneos_dir).exists()
    assert pathlib.Path(build_for_testing_artefacts.xctestrun_path).exists()


@pytest.mark.real_device
def test_parse_xctestrun(
    build_app_artefacts,
    build_app_for_testing_artefacts,
    xc_project_details,
):
    xctestrun = Xctest.parse_xctestrun(build_app_for_testing_artefacts.xctestrun_path)

    for test_configuration in xctestrun.TestConfigurations:
        for test_target in test_configuration.TestTargets:
            assert pathlib.Path(test_target.app_path).exists()
            assert test_target.app_path.startswith(build_app_artefacts.products_dir)

            assert pathlib.Path(test_target.ui_test_app_path).exists()
            assert test_target.ui_test_app_path.startswith(
                build_app_artefacts.products_dir
            )


@pytest.mark.requires_sudo
@pytest.mark.real_device
@pytest.mark.asyncio
async def test_enabled_tests(
    build_app_artefacts,
    build_app_for_testing_artefacts,
    ios_destination,
    ios_device,
    xc_test_case,
):
    i_services = IServices(ios_device)

    xctestrun = Xctest.parse_xctestrun(build_app_for_testing_artefacts.xctestrun_path)
    app_paths = set()

    for test_configuration in xctestrun.TestConfigurations:
        for test_target in test_configuration.TestTargets:
            app_paths.add(test_target.app_path)
            app_paths.add(test_target.ui_test_app_path)

    for app_path in app_paths:
        i_services.install_app(app_path)

    tests = await Xctest.list_tests(
        build_app_for_testing_artefacts.xctestrun_path,
        destination=ios_destination,
    )

    enabled_tests = tests.enabledTests

    assert len(enabled_tests) > 0
    assert xc_test_case in enabled_tests


@pytest.fixture(scope="module")
def session_test_plan(build_app_for_testing_artefacts, xc_test_case):
    return SessionTestPlan(
        name="Test Plan",
        reinstall_app=False,
        recording_start_strategy="launch",
        repetition_strategy="per_step",
        repetitions=1,
        xctestrun_config=XctestrunConfig(
            path=build_app_for_testing_artefacts.xctestrun_path,
            test_configuration="Test Scheme Action",  # Usually the user would specify this.
        ),
        recording_strategy="per_step",
        metrics=[Metric.cpu, Metric.memory, Metric.fps, Metric.gpu],
        steps=[
            PlanStep(
                order=0,
                name="Step 1",
                test_cases=[
                    StepTestCase(
                        xctest_id=xc_test_case,
                    )
                ],
            )
        ],
        end_on_failure=False,
    )


@pytest.fixture(scope="module")
def execution_plan(session_test_plan):
    plan = ExecutionPlan(test_plan=session_test_plan)
    plan.plan()
    return plan


@pytest.fixture(scope="module")
def session_id():
    return uuid.uuid4()


@pytest.fixture(scope="module")
def session(test_output_dir, ios_device, session_id, execution_plan):
    return Session(
        session_id=session_id,
        output_dir=test_output_dir,
        device=ios_device,
        execution_plan=execution_plan,
    )


@pytest.mark.requires_sudo
@pytest.mark.real_device
async def test_execute_tests(
    ios_device, session, execution_plan, test_output_dir, session_id
):
    await session.run()

    assert test_output_dir.exists()

    files = list(test_output_dir.glob("*"))

    assert len(files) == 2
    assert len([file for file in files if file.suffix == ".trace"]) == 1
    assert len([file for file in files if file.suffix == ".xcresult"]) == 1

    for file in files:
        assert file.stem == hash_session_execution_step(
            session_id=session_id, execution_step=execution_plan.execution_steps[0]
        )

    for execution_step in execution_plan.execution_steps:
        trace_path = (
            test_output_dir
            / f"{hash_session_execution_step(session_id, execution_step)}.trace"
        )
        toc_path = (
            test_output_dir
            / f"{hash_session_execution_step(session_id, execution_step)}_toc.xml"
        )
        data_path = (
            test_output_dir
            / f"{hash_session_execution_step(session_id, execution_step)}_data.xml"
        )
        await Xctrace.export_toc(trace_path.as_posix(), toc_path.as_posix())
        await Xctrace.export_data(
            trace_path.as_posix(),
            data_path.as_posix(),
            run=1,
            schemas=[Schema.SYSMON_PROCESS, Schema.CORE_ANIMATION_FPS_ESTIMATE],
        )

        assert trace_path.exists()
        assert toc_path.exists()

        toc = Xctrace.parse_toc_xml(toc_path.as_posix())
        assert toc is not None
        assert toc.runs is not None
        assert len(toc.runs) == 1

        data = Xctrace.parse_data_xml(data_path.as_posix(), toc)
        assert data is not None
        assert len(data) == 1
        assert data[0].get("sysmon-process") is not None
        assert data[0].get("core-animation-fps-estimate") is not None
        assert data[0].get("stdouterr-output") is None

        xcresult_path = (
            test_output_dir
            / f"{hash_session_execution_step(session_id, execution_step)}.xcresult"
        )
        xcresult_tool = XcresultTool(xcresult_path.as_posix())

        tests_result = await xcresult_tool.get_tests()
        assert tests_result is not None

        test_summary = await xcresult_tool.get_test_summary()
        assert test_summary is not None
