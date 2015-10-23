from .base import Base
from ptero_common import statuses
from sqlalchemy import Column, func
from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import backref, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSON
import celery
import os
import pwd
from ptero_common import nicer_logging


LOG = nicer_logging.getLogger(__name__)


class PreExecFailed(Exception):
    pass


__all__ = ['Job']


WEBHOOKS_TO_TRIGGER = {
    statuses.running: [statuses.running],
    statuses.errored: [statuses.errored, 'ended'],
    statuses.succeeded: [statuses.succeeded, 'ended'],
    statuses.failed: [statuses.failed, 'ended'],
}


class Job(Base):
    __tablename__ = 'job'

    id = Column(UUID(), primary_key=True)

    # expected to be a list of strings (enforced in jsonschema)
    command_line = Column(JSON, nullable=False)

    working_directory = Column(Text, nullable=False)
    environment = Column(JSON, default=dict)
    stdin = Column(Text)

    umask = Column(Integer)
    user = Column(Text, nullable=False, index=True)

    webhooks = Column(JSON, default=dict, nullable=False)

    stdout = Column(Text)
    stderr = Column(Text)
    exit_code = Column(Text)

    @property
    def status(self):
        statuses = self.status_history
        if statuses:
            return statuses[-1].status

    def set_status(self, status, message=None):
        JobStatusHistory(job=self, status=status, message=message)

    def trigger_webhook(self, new_status):
        webhooks = WEBHOOKS_TO_TRIGGER.get(new_status, [])
        for webhook_name in webhooks:
            urls = self.webhooks.get(webhook_name, [])
            if not isinstance(urls, list):
                urls = [urls]

            for url in urls:
                LOG.info('Webhook: "%s" for job %s -- %s',
                        webhook_name, self.id, url,
                        extra={'jobId': self.id})
                self.http_task.delay('POST', url, **self.as_dict)

    @property
    def http_task(self):
        return celery.current_app.tasks[
            'ptero_common.celery.http.HTTP'
        ]

    @property
    def as_dict(self):
        return {
            'commandLine': self.command_line,
            'environment': self.environment,
            'exitCode': self.exit_code,
            'jobId': self.id,
            'status': self.status,
            'statusHistory': [h.as_dict for h in self.status_history],
            'stdin': self.stdin,
            'stderr': self.stderr,
            'stdout': self.stdout,
            'user': self.user,
            'webhooks': self.webhooks,
            'workingDirectory': self.working_directory,
        }

    def _setup_execution_environment(self):
        pw_ent = self._get_pw_ent()

        if self.process_user == 'root':
            self._set_groups(pw_ent.pw_gid)
            self._set_gid(pw_ent.pw_gid)
            self._set_uid(pw_ent.pw_uid)
        elif self.user != self.process_user:
            raise PreExecFailed("Attempted to submit job as invalid user (%s),"
                    " only valid value is (%s)" %
                    (self.user, self.process_user))

        self._set_umask()
        self._set_working_directory()

    def _get_pw_ent(self):
        try:
            pw_ent = pwd.getpwnam(self.user)
        except KeyError as e:
            raise PreExecFailed(e.message)
        return pw_ent

    @property
    def process_user(self):
        return pwd.getpwuid(os.getuid())[0]

    def _set_groups(self, gid):
        try:
            os.initgroups(self.user, gid)
        except OSError as e:
            raise PreExecFailed('Failed to initgroups: ' + e.strerror)

    def _set_gid(self, gid):
        try:
            os.setregid(gid, gid)
        except OSError as e:
            raise PreExecFailed('Failed to setregid: ' + e.strerror)

    def _set_uid(self, uid):
        try:
            os.setreuid(uid, uid)
        except OSError as e:
            raise PreExecFailed('Failed to setreuid: ' + e.strerror)

    def _set_umask(self):
        if self.umask is not None:
            try:
                os.umask(self.umask)
            except TypeError as e:
                raise PreExecFailed('Failed to set umask: ' + e.message)

    def _set_working_directory(self):
        try:
            os.chdir(self.working_directory)
        except OSError as e:
            raise PreExecFailed(
                'Failed to chdir(%s): %s' %
                (self.working_directory, e.strerror))


class JobStatusHistory(Base):
    __tablename__ = 'job_status_history'

    id = Column(Integer, primary_key=True)
    job_id = Column(UUID(), ForeignKey(Job.id), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=func.now(),
                       nullable=False)

    status = Column(Text, index=True, nullable=False)
    message = Column(Text)

    job = relationship(Job,
                       backref=backref('status_history', order_by=timestamp))

    @property
    def as_dict(self):
        result = {
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
        }

        if self.message is not None:
            result['message'] = self.message

        return result
