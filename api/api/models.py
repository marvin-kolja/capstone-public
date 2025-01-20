import pathlib
import uuid
import datetime
from typing import Literal, Optional

from core.device.i_device import IDeviceStatus
from core.test_session.metrics import Metric
from core.test_session.session_state import StatusLiteral
from core.xc.xcresult.models.test_results import summary as xcresult_test_summary
from core.xc.xctrace.xml_parser import Sysmon, CoreAnimation, ProcessStdoutErr
from pydantic import ConfigDict, BaseModel
from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field as SQLField, Relationship, Column, JSON, String

from api.custom_db_types import PathType, CreatedAtField, UpdatedAtField


######################################
#              Device                #
######################################


class DeviceBase(SQLModel):
    device_class: str
    device_name: str
    build_version: str
    product_version: str
    product_type: str


class Device(DeviceBase, table=True):
    __tablename__ = "device"

    id: str = SQLField(primary_key=True)
    udid: str = SQLField(
        unique=True
    )  # For now, it is the same as id, but we may want to change the primary key to something else


class DeviceWithStatus(DeviceBase):
    id: str
    udid: str

    connected: bool = False
    status: Optional[IDeviceStatus] = None


######################################
#         Session Test Plan          #
######################################


RepetitionStrategy = Literal["entire_suite", "per_step"]
RecordingStrategy = Literal["per_step", "per_test"]
RecordingStartStrategy = Literal["launch", "attach"]


class SessionTestPlanStepBase(SQLModel):
    name: str
    repetitions: int | None = SQLField(ge=1, default=1)
    test_cases: list[str] = SQLField(min_length=1, sa_column=Column(JSON))
    metrics: list[Metric] | None = SQLField(sa_column=Column(JSON), default=None)
    recording_start_strategy: RecordingStartStrategy | None = SQLField(
        sa_type=String, default=None
    )
    reinstall_app: bool | None = SQLField(default=None)


class SessionTestPlanStep(SessionTestPlanStepBase, table=True):
    __tablename__ = "session_testplan_step"
    __table_args__ = (UniqueConstraint("test_plan_id", "order"),)

    id: uuid.UUID | None = SQLField(primary_key=True, default_factory=uuid.uuid4)
    order: int = SQLField(ge=0)

    test_plan_id: uuid.UUID = SQLField(
        foreign_key="session_testplan.id", ondelete="CASCADE"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class SessionTestPlanStepCreate(SessionTestPlanStepBase):
    pass


class SessionTestPlanStepPublic(SessionTestPlanStepBase):
    id: uuid.UUID
    order: int


class SessionTestPlanStepUpdate(SessionTestPlanStepBase):
    name: str | None = None
    test_cases: list[str] | None = None
    metrics: list[Metric] | None = None
    recording_start_strategy: RecordingStartStrategy | None = None
    reinstall_app: bool | None = None


class SessionTestPlanBase(SQLModel):
    name: str
    xc_test_plan_name: str
    end_on_failure: bool | None = SQLField(default=False)
    repetitions: int = SQLField(ge=1)
    repetition_strategy: RepetitionStrategy = SQLField(sa_type=String)
    metrics: list[Metric] = SQLField(sa_column=Column(JSON))
    recording_strategy: RecordingStrategy | None = SQLField(
        sa_type=String, default="per_test"
    )
    recording_start_strategy: RecordingStartStrategy | None = SQLField(
        sa_type=String, default="launch"
    )
    reinstall_app: bool | None = SQLField(default=False)


class SessionTestPlan(SessionTestPlanBase, table=True):
    __tablename__ = "session_testplan"

    id: uuid.UUID | None = SQLField(primary_key=True, default_factory=uuid.uuid4)
    project_id: uuid.UUID = SQLField(foreign_key="xc_project.id", ondelete="CASCADE")

    steps: list[SessionTestPlanStep] = Relationship(cascade_delete=True)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class SessionTestPlanCreate(SessionTestPlanBase):
    project_id: uuid.UUID


class SessionTestPlanPublic(SessionTestPlanBase):
    id: uuid.UUID
    end_on_failure: bool
    recording_strategy: RecordingStrategy
    recording_start_strategy: RecordingStartStrategy
    reinstall_app: bool
    steps: list[SessionTestPlanStepPublic]
    project_id: uuid.UUID


class SessionTestPlanUpdate(SessionTestPlanBase):
    name: str | None = None
    xc_test_plan_name: str | None = None
    end_on_failure: bool | None = None
    repetitions: int | None = None
    repetition_strategy: RepetitionStrategy | None = None
    metrics: list[Metric] | None = None
    recording_strategy: RecordingStrategy | None = None
    recording_start_strategy: RecordingStartStrategy | None = None
    reinstall_app: bool | None = None


######################################
#               Project              #
######################################


class XcProjectResourceModelBase(SQLModel):
    name: str


class XcProjectResourceModel(XcProjectResourceModelBase):
    id: uuid.UUID = SQLField(primary_key=True, default_factory=uuid.uuid4)
    project_id: uuid.UUID = SQLField(foreign_key="xc_project.id", ondelete="CASCADE")


class XcProjectConfiguration(XcProjectResourceModel, table=True):
    __tablename__ = "xc_project_configuration"


class XcProjectConfigurationPublic(XcProjectResourceModelBase):
    pass


class XcProjectTestPlan(XcProjectResourceModel, table=True):
    __tablename__ = "xc_project_test_plan"

    scheme_id: uuid.UUID = SQLField(
        foreign_key="xc_project_scheme.id", ondelete="CASCADE"
    )


class XcProjectTestPlanPublic(XcProjectResourceModelBase):
    pass


class XcProjectScheme(XcProjectResourceModel, table=True):
    __tablename__ = "xc_project_scheme"

    xc_test_plans: list[XcProjectTestPlan] = Relationship(cascade_delete=True)


class XcProjectSchemePublic(XcProjectResourceModelBase):
    xc_test_plans: list[XcProjectTestPlanPublic]


class XcProjectTarget(XcProjectResourceModel, table=True):
    __tablename__ = "xc_project_target"


class XcProjectTargetPublic(XcProjectResourceModelBase):
    pass


class XcProjectBase(SQLModel):
    path: pathlib.Path = SQLField(sa_column=Column(PathType))


class XcProject(XcProjectBase, table=True):
    __tablename__ = "xc_project"

    id: uuid.UUID = SQLField(primary_key=True, default_factory=uuid.uuid4)
    name: str

    configurations: list[XcProjectConfiguration] = Relationship(cascade_delete=True)
    schemes: list[XcProjectScheme] = Relationship(cascade_delete=True)
    targets: list[XcProjectTarget] = Relationship(cascade_delete=True)


class XcProjectCreate(XcProjectBase):
    pass


class XcProjectPublic(XcProjectBase):
    id: uuid.UUID
    name: str

    configurations: list[XcProjectConfigurationPublic]
    schemes: list[XcProjectSchemePublic]
    targets: list[XcProjectTargetPublic]


######################################
#               Build                #
######################################


class XctestrunBase(SQLModel):
    path: pathlib.Path = SQLField(sa_column=Column(PathType, unique=True))
    test_configurations: list[str] = SQLField(sa_column=Column(JSON))


class Xctestrun(XctestrunBase, table=True):
    __tablename__ = "xctestrun"

    id: uuid.UUID | None = SQLField(primary_key=True, default_factory=uuid.uuid4)

    build_id: uuid.UUID = SQLField(
        foreign_key="build.id", ondelete="CASCADE", unique=True
    )


class XctestrunPublic(XctestrunBase):
    id: uuid.UUID


BuildStatus = Literal[
    "pending",
    "running",
    "success",
    "failure",
]


class BuildBase(SQLModel):
    scheme: str
    configuration: str
    test_plan: str
    device_id: str
    status: BuildStatus = SQLField(sa_type=String, default="pending")


class Build(BuildBase, table=True):
    __tablename__ = "build"

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "device_id",
            "scheme",
            "configuration",
            "test_plan",
            name="unique_build",
        ),
    )

    id: uuid.UUID | None = SQLField(primary_key=True, default_factory=uuid.uuid4)
    project_id: uuid.UUID = SQLField(foreign_key="xc_project.id", ondelete="CASCADE")
    device_id: str = SQLField(foreign_key="device.id", ondelete="CASCADE")
    xctestrun: Xctestrun | None = Relationship(cascade_delete=True)


class BuildPublic(BuildBase):
    id: uuid.UUID
    project_id: uuid.UUID
    device_id: str
    xctestrun: XctestrunPublic | None


class StartBuildRequest(BaseModel):
    scheme: str
    configuration: str
    test_plan: str
    device_id: str


######################################
#          Execution Result          #
######################################


class XcTestResultDataBase(SQLModel):
    start_time: Optional[float]
    end_time: Optional[float]
    result: xcresult_test_summary.TestResult = SQLField(sa_column=Column(JSON))
    total_test_count: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    expected_failures: int
    test_failures: list[xcresult_test_summary.TestFailure] = SQLField(
        sa_column=Column(JSON)
    )


class XcTestResult(XcTestResultDataBase, table=True):
    __tablename__ = "test_result"

    id: uuid.UUID = SQLField(primary_key=True, default_factory=uuid.uuid4)
    execution_step_id: uuid.UUID = SQLField(
        foreign_key="execution_step.id", ondelete="CASCADE"
    )


class XcTestResultPublic(XcTestResultDataBase):
    pass


class TraceResultDataBase(SQLModel):
    id: uuid.UUID = SQLField(primary_key=True, default_factory=uuid.uuid4)
    execution_step_id: uuid.UUID = SQLField(
        foreign_key="trace_result.id", ondelete="CASCADE"
    )


class SysmonDB(TraceResultDataBase, Sysmon, table=True):
    __tablename__ = "sysmon"


class CoreAnimationDB(TraceResultDataBase, CoreAnimation, table=True):
    __tablename__ = "core_animation"


class ProcessStdoutErrDB(TraceResultDataBase, ProcessStdoutErr, table=True):
    __tablename__ = "process_stdout_err"


class TraceResultBase(SQLModel):
    export_status: StatusLiteral = SQLField(sa_type=String, default="not_started")


class TraceResult(TraceResultBase, table=True):
    __tablename__ = "trace_result"
    id: uuid.UUID | None = SQLField(primary_key=True, default_factory=uuid.uuid4)
    execution_step_id: uuid.UUID = SQLField(
        foreign_key="execution_step.id", ondelete="CASCADE"
    )

    sysmon: SysmonDB = Relationship(cascade_delete=True)
    core_animation: CoreAnimationDB = Relationship(cascade_delete=True)
    process_stdout_err: ProcessStdoutErrDB = Relationship(cascade_delete=True)


class TraceResultPublic(TraceResultBase):
    sysmon: Sysmon
    core_animation: CoreAnimation
    process_stdout_err: ProcessStdoutErr


######################################
#          Execution Steps           #
######################################


class ExecutionStepBase(SQLModel):
    id: uuid.UUID | None = SQLField(primary_key=True, default_factory=uuid.uuid4)

    plan_repetition: int
    plan_step_order: int
    step_repetition: int
    recording_start_strategy: RecordingStartStrategy = SQLField(sa_type=String)
    reinstall_app: bool
    metrics: list[Metric] = SQLField(sa_column=Column(JSON))
    test_cases: list[str] = SQLField(min_length=1, sa_column=Column(JSON))
    end_on_failure: bool
    test_target_name: str

    status: StatusLiteral = SQLField(sa_type=String, default="not_started")

    created_at: datetime.datetime = CreatedAtField()
    updated_at: datetime.datetime = UpdatedAtField()


class ExecutionStep(ExecutionStepBase, table=True):
    __tablename__ = "execution_step"
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "plan_repetition",
            "plan_step_order",
            "step_repetition",
            name="unique_execution_step",
        ),
    )
    session_id: uuid.UUID = SQLField(foreign_key="session.id", ondelete="CASCADE")

    xc_test_result: XcTestResult = Relationship(cascade_delete=True)
    trace_result: TraceResult = Relationship(cascade_delete=True)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ExecutionStepPublic(ExecutionStepBase):
    id: uuid.UUID
    xc_test_result: XcTestResultPublic
    trace_result: TraceResultPublic


######################################
#              Session               #
######################################


class TestSessionBase(SQLModel):
    id: uuid.UUID = SQLField(primary_key=True)
    xc_test_configuration_name: str
    status: StatusLiteral = SQLField(sa_type=String, default="not_started")

    created_at: datetime.datetime = CreatedAtField()
    updated_at: datetime.datetime = UpdatedAtField()


class TestSession(TestSessionBase, table=True):
    __tablename__ = "session"

    # TODO: Consider storing device, plan, and build as JSON fields to avoid loosing data if the referenced record is
    #  deleted
    device_id: str = SQLField(
        foreign_key="device.id", ondelete="SET NULL", nullable=True
    )  # Set device_id to NULL if the device is deleted as we want to keep the session record
    plan_id: uuid.UUID | None = SQLField(
        foreign_key="session_testplan.id", ondelete="SET NULL", nullable=True
    )  # Set plan_id to NULL if the plan is deleted as we want to keep the session record
    build_id: uuid.UUID | None = SQLField(
        foreign_key="build.id", ondelete="SET NULL", nullable=True
    )  # Set build_id to NULL if the build is deleted as we want to keep the session record

    device_snapshot: Device = SQLField(sa_column=Column(JSON))
    plan_snapshot: SessionTestPlan = SQLField(sa_column=Column(JSON))
    build_snapshot: Build = SQLField(sa_column=Column(JSON))

    device: Device | None = Relationship()
    plan: SessionTestPlan | None = Relationship()
    build: Build | None = Relationship()
    execution_steps: list[ExecutionStep] = Relationship(cascade_delete=True)


class TestSessionPublic(TestSessionBase):
    device: DeviceWithStatus | None
    plan: SessionTestPlanPublic | None
    build: BuildPublic | None
    execution_steps: list[ExecutionStepPublic]


class TestSessionCreate(BaseModel):
    plan_id: uuid.UUID
    build_id: uuid.UUID
