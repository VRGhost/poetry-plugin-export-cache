import cleo
import poetry

class CustomCommand(cleo.commands.command.Command):

    name = "export-cache"

    def handle(self) -> int:
        self.line("My command")

        return 0

def factory():
    return CustomCommand()

class ExportCachePlugin(poetry.plugins.application_plugin.ApplicationPlugin):

    def activate(self, application: poetry.console.application.Application):
        print(type(application))
        1/0
        application.command_loader.register_factory("export cache", factory)
