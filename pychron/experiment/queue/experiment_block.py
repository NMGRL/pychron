from traits.has_traits import HasTraits
from traits.trait_types import String
from pychron.experiment.automated_run.spec import AutomatedRunSpec
from pychron.experiment.automated_run.uv.spec import UVAutomatedRunSpec
from pychron.experiment.queue.parser import RunParser, UVRunParser
from pychron.loggable import Loggable


class ExperimentBlock(Loggable):
    extract_device = String
    mass_spectrometer = String

    def _setup_params(self,params):
        pass

    def extract_runs(self, path):
        with open(path,'r') as fp:
            line_gen=self._get_line_generator(fp)
            # meta = self._extract_meta(line_gen)
            return self._load_runs(line_gen)

    def _get_line_generator(self, txt):
        if isinstance(txt, (str,unicode)):
            return (l for l in txt.split('\n'))
        else:
            return txt

    def _load_runs(self, line_gen):
        aruns = []
        delim = '\t'

        header = map(str.strip, line_gen.next().split(delim))

        pklass = RunParser
        if self.extract_device == 'Fusions UV':
            pklass = UVRunParser
        parser = pklass()
        for linenum, line in enumerate(line_gen):
            skip = False
            line = line.rstrip()

            # load commented runs but flag as skipped
            if line.startswith('##'):
                continue
            if line.startswith('#'):
                skip = True
                line = line[1:]

            if not line:
                continue

            try:
                script_info, params = parser.parse(header, line)
                self._setup_params(params)
                params['skip'] = skip
                params['mass_spectrometer'] = self.mass_spectrometer

                klass = AutomatedRunSpec
                if self.extract_device == 'Fusions UV':
                    klass = UVAutomatedRunSpec

                arun = klass()
                arun.load(script_info, params)
                #arun = self._automated_run_factory(script_info, params, klass)

                aruns.append(arun)

            except Exception, e:
                import traceback

                print traceback.print_exc()
                self.warning_dialog('Invalid Experiment file {}\nlinenum= {}\nline= {}'.format(e, linenum, line))

                return

        return aruns

