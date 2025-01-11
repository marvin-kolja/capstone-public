import pathlib
from typing import Optional
from xml.etree import ElementTree

import xmltodict
from pydantic import BaseModel, Field, AliasPath, AliasChoices


class ProcessEntry(BaseModel):
    name: str = Field(validation_alias=AliasChoices("name", "@name"))
    pid: int = Field(validation_alias=AliasChoices("pid", "@pid"))
    return_exit_status: Optional[int] = Field(
        validation_alias=AliasChoices("return_exit_status", "@return-exit-status"),
        default=None,
    )
    termination_reason: Optional[str] = Field(
        validation_alias=AliasChoices("termination_reason", "@termination-reason"),
        default=None,
    )
    path: Optional[str] = Field(
        validation_alias=AliasChoices("path", "@path"), default=None
    )


class TOCRunInfoTarget(BaseModel):
    process: ProcessEntry


class TOCRunInfoSummary(BaseModel):
    start_date: str = Field(validation_alias=AliasChoices("start_date", "start-date"))
    end_date: str = Field(validation_alias=AliasChoices("end_date", "end-date"))
    duration: float
    end_reason: str = Field(validation_alias=AliasChoices("end_reason", "end-reason"))
    instruments_version: str = Field(
        validation_alias=AliasChoices("instruments_version", "instruments-version")
    )
    template_name: str = Field(
        validation_alias=AliasChoices("template_name", "template-name")
    )
    recording_mode: str = Field(
        validation_alias=AliasChoices("recording_mode", "recording-mode")
    )
    time_limit: Optional[str] = Field(
        validation_alias=AliasChoices("time_limit", "time-limit"), default=None
    )


class TOCRunInfo(BaseModel):
    target: TOCRunInfoTarget
    summary: TOCRunInfoSummary


class TOCDataTable(BaseModel):
    schema_name: str = Field(validation_alias=AliasChoices("schema_name", "@schema"))


class TOCRun(BaseModel):
    number: int = Field(validation_alias=AliasChoices("number", "@number"))
    info: TOCRunInfo
    processes: list[ProcessEntry] = Field(
        validation_alias=AliasChoices(AliasPath("processes", "process"), "processes")
    )
    data: list[TOCDataTable] = Field(
        validation_alias=AliasChoices(AliasPath("data", "table"), "data")
    )


class TOC(BaseModel):
    runs: list[TOCRun]


def parse_toc_xml(path: pathlib.Path) -> TOC:
    """
    Parses the given TOC XML file by first converting it to a dictionary and then validating it against the TOC model.

    For parsing the XML file to a dictionary, the xmltodict library is used.

    :param path: The path to the TOC XML file.
    :return: The parsed TOC data.
    """

    with path.open("r") as file:
        data = xmltodict.parse(file.read())
        return TOC.model_validate(data)
