import poetry

class ExportCachePlugin(poetry.plugins.application_plugin.ApplicationPlugin):

    def activate(self):
        1/0