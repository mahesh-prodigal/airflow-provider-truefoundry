from enum import Enum
import time

from airflow.utils.decorators import apply_defaults
from airflow.exceptions import AirflowException
from airflow.models import BaseOperator

from truefoundry.deploy import trigger_job, get_job_run, terminate_job_run
from truefoundry_provider.hooks.truefoundry import TrueFoundryHook


class JobRunState(str, Enum):
    SCHEDULED: str = "SCHEDULED"
    RUNNING: str = "RUNNING"
    TERMINATING: str = "TERMINATING"
    TERMINATED: str = "TERMINATED"
    FAILED: str = "FAILED"
    FINISHED: str = "FINISHED"


class TrueFoundryJobRunNowOperator(BaseOperator):

    # Used in airflow.models.BaseOperator
    template_fields = ("application_fqn", "command", "parameters",
                       "wait_for_termination", "polling_interval", "truefoundry_conn_id")
    # Brand color (blue) under white text
    ui_color = "#1CB1C2"
    ui_fgcolor = "#fff"

    def __init__(
        self,
        application_fqn: str,
        command: str | None = None,
        parameters: str | None = None,
        wait_for_termination: bool = True,
        polling_interval: float = 20,
        truefoundry_conn_id='truefoundry_default',
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.application_fqn = application_fqn
        self.command = command
        self.parameters = parameters
        self.wait_for_termination = wait_for_termination
        self.polling_interval = polling_interval
        self.truefoundry_conn_id = truefoundry_conn_id
        self.job_run_name = None

    def execute(self, context):
        hook = TrueFoundryHook(truefoundry_conn_id=self.truefoundry_conn_id)
        conn = hook.get_conn()

        self.log.info(f"Triggering job for application_fqn: {self.application_fqn} on truefoundry host {conn.host}."
                      f" command: {self.command}, parameters: {self.parameters},"
                      f" wait_for_termination: {self.wait_for_termination}, polling_interval: {self.polling_interval},"
                      f" truefoundry_conn_id: {self.truefoundry_conn_id}"
                      f" {type({self.command})}, {type({self.parameters})}")
        kwargs = {}
        if self.command and self.parameters:
            raise AirflowException(
                f"Task Failed: Cannot pass both parameters and command for Truefoundry Job"
            )

        try:
            self.polling_interval = float(self.polling_interval)
        except Exception:
            raise AirflowException(
                f"Task Failed: polling_interval should be float value"
            )

        if not isinstance(self.wait_for_termination, bool):
            raise AirflowException(
                f"Task Failed: wait_for_termination should be boolean"
            )

        if self.command:
            kwargs["command"] = self.command
        if self.parameters:
            kwargs["params"] = self.parameters

        job_run = trigger_job(application_fqn=self.application_fqn, **kwargs)
        self.job_run_name = job_run.jobRunName

        if self.wait_for_termination is True:
            self.log.info(f"Polling job status every {self.polling_interval} seconds")
            while True:
                job_run_object = get_job_run(
                    application_fqn=self.application_fqn, job_run_name=self.job_run_name
                )
                status = job_run_object.status
                if status in [
                    JobRunState.RUNNING,
                    JobRunState.SCHEDULED,
                    JobRunState.TERMINATING,
                ]:
                    time.sleep(self.polling_interval)
                    continue
                else:
                    if status == JobRunState.FINISHED:
                        return
                    elif status == JobRunState.FAILED:
                        retries = job_run_object.retries
                        raise AirflowException(
                            f"JobRunName: {self.job_run_name} failed after {retries} retries"
                        )
                    elif status == JobRunState.TERMINATED:
                        raise AirflowException(
                            f"JobRunName: {self.job_run_name} is terminated"
                        )
                    else:
                        raise AirflowException(f"Unknown status: {status}")

    def on_kill(self):
        if self.job_run_name:
            self.log.info(f"Terminating Job with jobRunName: f{self.job_run_name}")
            terminate_job_run(
                application_fqn=self.application_fqn, job_run_name=self.job_run_name
            )
        else:
            self.log.info("Skipping job run termination as it has not started yet")
