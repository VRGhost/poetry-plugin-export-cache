import poetry.console.application
import poetry.plugins
from cleo.commands.command import Command


class CustomCommand(Command):
    name = "export-cache"

    def handle(self) -> int:
        self.line("My command")

        return 0


def factory():
    return CustomCommand()


class ExportCachePlugin(poetry.plugins.application_plugin.ApplicationPlugin):
    def activate(self, application: poetry.console.application.Application):
        application.command_loader.register_factory("export-cache", factory)
