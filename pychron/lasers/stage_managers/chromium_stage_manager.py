from pychron.lasers.stage_managers.stage_manager import StageManager


class ChromiumStageManager(StageManager):
    def get_current_position(self):
        self.parent.update_position()
        self.debug('get_current_position {},{}'.format(self.parent.x, self.parent.y))
        return self.parent.x, self.parent.y