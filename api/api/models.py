import pathlib
import uuid
from typing import Literal, Optional

from core.device.i_device import IDeviceStatus
from core.test_session.metrics import Metric
from pydantic import ConfigDict
from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field as SQLField, Relationship, Column, JSON, String

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
    xctestrun_path: str
    xctestrun_test_configuration: str
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

    steps: list[SessionTestPlanStep] = Relationship(cascade_delete=True)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class SessionTestPlanCreate(SessionTestPlanBase):
    pass


class SessionTestPlanPublic(SessionTestPlanBase):
    id: uuid.UUID
    end_on_failure: bool
    recording_strategy: RecordingStrategy
    recording_start_strategy: RecordingStartStrategy
    reinstall_app: bool
    steps: list[SessionTestPlanStepPublic]


class SessionTestPlanUpdate(SessionTestPlanBase):
    name: str | None = None
    xctestrun_path: str | None = None
    xctestrun_test_configuration: str | None = None
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

    schema_id: uuid.UUID = SQLField(
        foreign_key="xc_project_schema.id", ondelete="CASCADE"
    )


class XcProjectTestPlanPublic(XcProjectResourceModelBase):
    pass


class XcProjectSchema(XcProjectResourceModel, table=True):
    __tablename__ = "xc_project_schema"

    xc_test_plans: list[XcProjectTestPlan] = Relationship(cascade_delete=True)


class XcProjectSchemaPublic(XcProjectResourceModelBase):
    xc_test_plans: list[XcProjectTestPlanPublic]


class XcProjectTarget(XcProjectResourceModel, table=True):
    __tablename__ = "xc_project_target"


class XcProjectTargetPublic(XcProjectResourceModelBase):
    pass


class XcProjectBase(SQLModel):
    path: pathlib.Path = SQLField(sa_type=String)


class XcProject(XcProjectBase, table=True):
    __tablename__ = "xc_project"

    id: uuid.UUID = SQLField(primary_key=True, default_factory=uuid.uuid4)
    name: str

    configurations: list[XcProjectConfiguration] = Relationship(cascade_delete=True)
    schemas: list[XcProjectSchema] = Relationship(cascade_delete=True)
    targets: list[XcProjectTarget] = Relationship(cascade_delete=True)


class XcProjectCreate(XcProjectBase):
    pass


class XcProjectPublic(XcProjectBase):
    id: uuid.UUID
    name: str

    configurations: list[XcProjectConfigurationPublic]
    schemas: list[XcProjectSchemaPublic]
    targets: list[XcProjectTargetPublic]
