"""
Test the whole process from building the app to parsing the test results (.trace, .xcresult).
"""

import os
import pathlib
import tempfile
import uuid

import pytest

from core.build.app_builder import (
    AppBuilder,
    XcodeBuildArtefacts,
    XcodeTestBuildArtefacts,
)
from core.device.i_device_manager import IDeviceManager
from core.device.i_services import IServices
from core.subprocesses.xcodebuild_command import (
    IOSDestination,
    XcodebuildCommand,
)
from core.subprocesses.xctrace_command import XctraceCommand
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
from core.test_session.xctest import Xctest
from core.xc.xc_project import XcProject


@pytest.fixture(scope="module", autouse=True)
def fix_xcodebuild_sudo_issue(build_output_dir, test_output_dir):
    """
    It seems when executing xcodebuild using sudo it is unable to it is unable to automatically sign applications during
    the build process. This workaround always uses the current user when executing xcodebuild in a subprocess.

    It also seems that xctrace may also have issues executing as sudo. This workaround also uses the current user when
    executing xctrace in a subprocess.

    This leads to another issue as then the process does not have access to the paths created by the sudo user. Thus, we
    also need to change the permission of:
    - build_output_dir
    - test_output_dir
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

        test_output_dir_path = pathlib.Path(test_output_dir)
        build_output_dir_path = pathlib.Path(build_output_dir)
        for path in [test_output_dir_path, build_output_dir_path]:
            if path.exists():
                # if the dir is created by sudo, the current user does not have access to it thus we need to change the
                # permissions
                if path.stat().st_uid == 0:
                    os.chmod(path, 0o777)
                if path.parent.stat().st_uid == 0:
                    os.chmod(path.parent, 0o777)


@pytest.fixture(scope="module")
def tmp_dir():
    with tempfile.TemporaryDirectory(delete=False) as tmp_dir:
        yield tmp_dir


@pytest.fixture(scope="module")
def build_output_dir():
    test_root = pathlib.Path(__file__).parent.parent
    build_path = test_root.joinpath("test_data/build_output_dir")
    if not build_path.exists():
        build_path.mkdir()
    return build_path.resolve().as_posix()


@pytest.fixture(scope="module")
def test_output_dir(tmp_dir):
    test_path = pathlib.Path(tmp_dir, "test_output_dir")
    test_path.mkdir()
    yield test_path.resolve().as_posix()


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
    build_artefacts = await app_builder.build(
        scheme=xc_project_scheme,
        configuration=xc_project_configuration,
        output_dir=build_output_dir,
        destination=ios_destination,
    )
    build_for_testing_artefacts = await app_builder.build_for_testing(
        scheme=xc_project_scheme,
        test_plan=xc_project_test_plan,
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


@pytest.fixture
def test_plan(build_app_for_testing_artefacts, xc_test_case):
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


@pytest.mark.requires_sudo
@pytest.mark.real_device
async def test_execute_tests(ios_device, test_output_dir, test_plan):
    execution_plan = ExecutionPlan(test_plan=test_plan)
    execution_plan.plan()

    session_id = uuid.uuid4()
    test_session = Session(
        session_id=session_id,
        output_dir=test_output_dir,
        device=ios_device,
        execution_plan=execution_plan,
    )

    await test_session.run()

    assert pathlib.Path(test_output_dir).exists()

    files = list(pathlib.Path(test_output_dir).glob("*"))

    assert len(files) == 2
    assert len([file for file in files if file.suffix == ".trace"]) == 1
    assert len([file for file in files if file.suffix == ".xcresult"]) == 1

    for file in files:
        assert file.stem == hash_session_execution_step(
            session_id=session_id, execution_step=execution_plan.execution_steps[0]
        )


@pytest.mark.skip("Requires trace file parsing")
@pytest.mark.asyncio
async def test_parse_trace_file(test_output_dir):
    pass


@pytest.mark.skip("Requires xcresult file parsing")
@pytest.mark.asyncio
async def test_parse_xcresult_file(test_output_dir):
    pass
