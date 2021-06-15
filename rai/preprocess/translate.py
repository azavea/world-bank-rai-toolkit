import sys
import logging

from argostranslate import package, translate

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(levelname)s: %(name)s: %(message)s')
log = logging.getLogger()


class Translator():
    def __init__(self, from_code: str, to_code: str) -> None:
        self.populate_packages()
        self.model = self.load_model(from_code, to_code)

    def translate(self, s: str) -> str:
        return self.model.translate(s)

    def __call__(self, s: str) -> str:
        return self.translate(s)

    def populate_packages(self):
        package.update_package_index()
        self.installed_packages = {(p.from_code, p.to_code): p
                                   for p in package.get_installed_packages()}
        self.available_packages = {(p.from_code, p.to_code): p
                                   for p in package.get_available_packages()}

    def load_model(self, from_code: str,
                   to_code: str) -> translate.CachedTranslation:
        self.install_package_if_needed(from_code, to_code)
        langs = {l.code: l for l in translate.get_installed_languages()}
        model = langs[from_code].get_translation(langs[to_code])
        return model

    def install_package_if_needed(self, from_code: str, to_code: str) -> None:
        k = (from_code, to_code)
        if k in self.installed_packages:
            log.info('Loading already installed model.')
        elif k in self.available_packages:
            log.info('Downloading package ...')
            pkg = self.packages[k]
            model_path = pkg.download()
            log.info('Installing package ...')
            package.install_from_path(model_path)
        else:
            raise KeyError(f'({k}) not found in available packages.')
