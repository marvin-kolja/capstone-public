import pathlib
import uuid
import datetime
from enum import StrEnum
from typing import Literal, Optional, Annotated, Any

from core.device.i_device import IDeviceStatus
from core.test_session.metrics import Metric
from core.test_session.session_state import StatusLiteral
from core.xc.xcresult.models.test_results import summary as xcresult_test_summary
from core.xc.xctrace.xml_parser import Sysmon, CoreAnimation, ProcessStdoutErr
from pydantic import ConfigDict, BaseModel, BeforeValidator
from sqlalchemy import UniqueConstraint
from sqlmodel import (
    SQLModel,
    Field as SQLField,
    Relationship,
    Column,
    JSON,
    String,
    Enum,
)

from api.custom_db_types import PathType, CreatedAtField, UpdatedAtField


_common_relationship_kwargs = {"lazy": "selectin"}


######################################
#           Health Check             #
######################################

ServerStatus = Literal["ok", "unhealthy"]
ResourceStatus = Literal["ok", "unavailable"]


class HealthCheck(BaseModel):
    status: ServerStatus
    db: ResourceStatus
    tunnel_connect: ResourceStatus


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


class RepetitionStrategy(StrEnum):
    entire_suite = "entire_suite"
    per_step = "per_step"

    @classmethod
    def from_string(cls, value: str) -> "RepetitionStrategy":
        if value == "entire_suite":
            return RepetitionStrategy.entire_suite
        elif value == "per_step":
            return RepetitionStrategy.per_step
        else:
            raise ValueError(f"Invalid value for RepetitionStrategy: {value}")

    def to_literal(self) -> Literal["entire_suite", "per_step"]:
        return str(self.value)


class RecordingStrategy(StrEnum):
    per_step = "per_step"
    per_test = "per_test"

    @classmethod
    def from_string(cls, value: str) -> "RecordingStrategy":
        if value == "per_step":
            return RecordingStrategy.per_step
        elif value == "per_test":
            return RecordingStrategy.per_test
        else:
            raise ValueError(f"Invalid value for RecordingStrategy: {value}")

    def to_literal(self) -> Literal["per_step", "per_test"]:
        return str(self.value)


class RecordingStartStrategy(StrEnum):
    launch = "launch"
    attach = "attach"

    @classmethod
    def from_string(cls, value: str) -> "RecordingStartStrategy":
        if value == "launch":
            return RecordingStartStrategy.launch
        elif value == "attach":
            return RecordingStartStrategy.attach
        else:
            raise ValueError(f"Invalid value for RecordingStartStrategy: {value}")

    def to_literal(self) -> Literal["launch", "attach"]:
        return str(self.value)


class SessionTestPlanStepBase(SQLModel):
    name: str
    repetitions: int | None = SQLField(ge=1, default=1)
    test_cases: list[str] = SQLField(min_length=1, sa_column=Column(JSON))
    metrics: list[Metric] | None = SQLField(sa_column=Column(JSON), default=None)
    recording_start_strategy: RecordingStartStrategy | None = SQLField(
        sa_column=Column(Enum(RecordingStartStrategy), nullable=True), default=None
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
    end_on_failure: bool | None = SQLField(default=False)
    repetitions: int = SQLField(ge=1)
    repetition_strategy: RepetitionStrategy = SQLField(
        sa_column=Column(Enum(RepetitionStrategy), nullable=False)
    )
    metrics: list[Metric] = SQLField(sa_column=Column(JSON))
    recording_strategy: RecordingStrategy | None = SQLField(
        sa_column=Column(Enum(RecordingStrategy)), default=RecordingStrategy.per_test
    )
    recording_start_strategy: RecordingStartStrategy | None = SQLField(
        sa_column=Column(Enum(RecordingStartStrategy)),
        default=RecordingStartStrategy.launch,
    )
    reinstall_app: bool | None = SQLField(default=False)


class SessionTestPlan(SessionTestPlanBase, table=True):
    __tablename__ = "session_testplan"

    id: uuid.UUID | None = SQLField(primary_key=True, default_factory=uuid.uuid4)
    project_id: uuid.UUID = SQLField(foreign_key="xc_project.id", ondelete="CASCADE")
    build_id: uuid.UUID = SQLField(foreign_key="build.id", ondelete="CASCADE")

    steps: list[SessionTestPlanStep] = Relationship(
        cascade_delete=True, sa_relationship_kwargs=_common_relationship_kwargs
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class SessionTestPlanCreate(SessionTestPlanBase):
    project_id: uuid.UUID
    build_id: uuid.UUID


class SessionTestPlanPublic(SessionTestPlanBase):
    id: uuid.UUID
    end_on_failure: bool
    recording_strategy: RecordingStrategy
    recording_start_strategy: RecordingStartStrategy
    reinstall_app: bool
    steps: list[SessionTestPlanStepPublic]
    project_id: uuid.UUID
    build_id: uuid.UUID


class SessionTestPlanUpdate(SessionTestPlanBase):
    name: str | None = None
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

    xc_test_plans: list[XcProjectTestPlan] = Relationship(
        cascade_delete=True, sa_relationship_kwargs=_common_relationship_kwargs
    )


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

    configurations: list[XcProjectConfiguration] = Relationship(
        cascade_delete=True, sa_relationship_kwargs=_common_relationship_kwargs
    )
    schemes: list[XcProjectScheme] = Relationship(
        cascade_delete=True, sa_relationship_kwargs=_common_relationship_kwargs
    )
    targets: list[XcProjectTarget] = Relationship(
        cascade_delete=True, sa_relationship_kwargs=_common_relationship_kwargs
    )


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

    xc_test_cases: list[str] | None = SQLField(
        sa_column=Column(JSON, nullable=True), default=None
    )


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
    xctestrun: Xctestrun | None = Relationship(
        cascade_delete=True, sa_relationship_kwargs=_common_relationship_kwargs
    )


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
    result: xcresult_test_summary.TestResult = SQLField(
        sa_column=Column(Enum(xcresult_test_summary.TestResult))
    )
    total_test_count: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    expected_failures: int
    test_failures: list[xcresult_test_summary.TestFailure] = SQLField(
        sa_column=Column(JSON)
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


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
    trace_result_id: uuid.UUID = SQLField(
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

    sysmon: list[SysmonDB] = Relationship(
        cascade_delete=True, sa_relationship_kwargs=_common_relationship_kwargs
    )
    core_animation: list[CoreAnimationDB] = Relationship(
        cascade_delete=True, sa_relationship_kwargs=_common_relationship_kwargs
    )
    process_stdout_err: list[ProcessStdoutErrDB] = Relationship(
        cascade_delete=True, sa_relationship_kwargs=_common_relationship_kwargs
    )


class TraceResultPublic(TraceResultBase):
    sysmon: list[Sysmon]
    core_animation: list[CoreAnimation]
    process_stdout_err: list[ProcessStdoutErr]


######################################
#          Execution Steps           #
######################################


class ExecutionStepBase(SQLModel):
    id: uuid.UUID | None = SQLField(primary_key=True, default_factory=uuid.uuid4)

    plan_repetition: int
    plan_step_order: int
    step_repetition: int
    recording_start_strategy: RecordingStartStrategy = SQLField(
        sa_column=Column(Enum(RecordingStartStrategy), nullable=False)
    )
    reinstall_app: bool
    metrics: list[Metric] = SQLField(sa_column=Column(JSON))
    test_cases: list[str] = SQLField(min_length=1, sa_column=Column(JSON))
    end_on_failure: bool
    test_target_name: str

    status: StatusLiteral = SQLField(sa_type=String, default="not_started")
    xcresult_path: pathlib.Path | None = SQLField(
        sa_column=Column(PathType, nullable=True)
    )
    trace_path: pathlib.Path | None = SQLField(
        sa_column=Column(PathType, nullable=True)
    )

    created_at: datetime.datetime = CreatedAtField()
    updated_at: datetime.datetime = UpdatedAtField()

    model_config = ConfigDict(arbitrary_types_allowed=True)


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

    xc_test_result: XcTestResult | None = Relationship(
        cascade_delete=True, sa_relationship_kwargs=_common_relationship_kwargs
    )
    trace_result: TraceResult | None = Relationship(
        cascade_delete=True, sa_relationship_kwargs=_common_relationship_kwargs
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ExecutionStepPublic(ExecutionStepBase):
    id: uuid.UUID
    xc_test_result: XcTestResultPublic | None
    trace_result: TraceResultPublic | None


######################################
#              Session               #
######################################


class TestSessionBase(SQLModel):
    __test__ = False

    xc_test_configuration_name: str

    status: StatusLiteral = SQLField(sa_type=String, default="not_started")

    created_at: datetime.datetime = CreatedAtField()
    updated_at: datetime.datetime = UpdatedAtField()


class TestSession(TestSessionBase, table=True):
    __tablename__ = "session"
    __test__ = False

    id: uuid.UUID | None = SQLField(primary_key=True, default_factory=uuid.uuid4)

    device_id: str = SQLField(
        foreign_key="device.id", ondelete="SET NULL", nullable=True
    )  # Set device_id to NULL if the device is deleted as we want to keep the session record
    plan_id: uuid.UUID | None = SQLField(
        foreign_key="session_testplan.id", ondelete="SET NULL", nullable=True
    )  # Set plan_id to NULL if the plan is deleted as we want to keep the session record
    build_id: uuid.UUID | None = SQLField(
        foreign_key="build.id", ondelete="SET NULL", nullable=True
    )  # Set build_id to NULL if the build is deleted as we want to keep the session record

    # TODO: Pydantic models do not serialize to JSON by default. For now we use dicts which requires dumping and loading
    #  to convert to and from JSON. We should consider using one of the suggested solutions in the following issue:
    #  https://github.com/fastapi/sqlmodel/issues/63#issuecomment-2581016387
    device_snapshot: dict = SQLField(sa_column=Column(JSON))
    plan_snapshot: dict = SQLField(sa_column=Column(JSON))
    build_snapshot: dict = SQLField(sa_column=Column(JSON))

    device: Device | None = Relationship(
        sa_relationship_kwargs=_common_relationship_kwargs
    )
    plan: SessionTestPlan | None = Relationship(
        sa_relationship_kwargs=_common_relationship_kwargs
    )
    build: Build | None = Relationship(
        sa_relationship_kwargs=_common_relationship_kwargs
    )
    execution_steps: list[ExecutionStep] = Relationship(
        cascade_delete=True, sa_relationship_kwargs=_common_relationship_kwargs
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


def dict_to_pydantic_validator(model: type[BaseModel]):
    """
    Returns a function that validates the incoming data using passed model
    :param model: pydantic model
    :return: a function that can be used in a BeforeValidator
    """

    def parse(data: Any) -> Any:
        validated = model.model_validate(data)
        return validated

    return parse


class TestSessionPublic(TestSessionBase):
    __test__ = False

    id: uuid.UUID
    device_snapshot: Annotated[
        DeviceWithStatus, BeforeValidator(dict_to_pydantic_validator(DeviceWithStatus))
    ]
    plan_snapshot: Annotated[
        SessionTestPlanPublic,
        BeforeValidator(dict_to_pydantic_validator(SessionTestPlanPublic)),
    ]
    build_snapshot: Annotated[
        BuildPublic, BeforeValidator(dict_to_pydantic_validator(BuildPublic))
    ]
    execution_steps: list[ExecutionStepPublic]


class TestSessionCreate(BaseModel):
    __test__ = False

    plan_id: uuid.UUID
    xc_test_configuration_name: str
