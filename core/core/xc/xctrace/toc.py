import pathlib
from typing import Optional, Any

import xmltodict
from pydantic import BaseModel, Field, AliasChoices, model_validator


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
    duration: float = Field(validation_alias=AliasChoices("duration", "duration"))
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
    processes: list[ProcessEntry]
    data: list[TOCDataTable]

    @model_validator(mode="before")
    @classmethod
    def restructure_list_fields(cls, data: Any) -> dict:
        if not isinstance(data, dict):
            raise ValueError("TOC run must be a dictionary")

        processes = data["processes"]

        if isinstance(processes, dict):
            process = processes["process"]
            if isinstance(process, dict):
                data["processes"] = [process]
            elif isinstance(process, list):
                data["processes"] = process
            else:
                raise ValueError("TOC run must contain a 'process' element")

        table_data = data["data"]

        if isinstance(table_data, dict):
            table = table_data["table"]
            if isinstance(table, dict):
                data["data"] = [table]
            elif isinstance(table, list):
                data["data"] = table
            else:
                raise ValueError("TOC run must contain a 'table' element")

        return data


class TOC(BaseModel):
    runs: list[TOCRun]

    @model_validator(mode="before")
    @classmethod
    def restructure_runs(cls, data: Any) -> dict:
        if not isinstance(data, dict):
            raise ValueError("TOC data must be a dictionary")

        if "runs" in data:
            return data

        if "trace-toc" not in data:
            raise ValueError("TOC data must contain a 'trace-toc' element")

        trace_toc = data["trace-toc"]
        if "run" not in trace_toc:
            raise ValueError("TOC data must contain a 'run' element")

        run = trace_toc["run"]
        if isinstance(run, dict):
            return {"runs": [run]}
        elif isinstance(run, list):
            return {"runs": run}
        else:
            raise ValueError("TOC data must contain a 'run' element")


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
