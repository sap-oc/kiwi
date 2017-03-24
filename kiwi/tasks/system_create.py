# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of kiwi.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi.  If not, see <http://www.gnu.org/licenses/>
#
"""
usage: kiwi system create -h | --help
       kiwi system create --root=<directory> --target-dir=<directory>
       kiwi system create help

commands:
    create
        create a system image from the specified root directory
        the root directory is the result of a system prepare
        command
    create help
        show manual page for create command

options:
    --root=<directory>
        the path to the root directory, usually the result of
        a former system prepare call
    --target-dir=<directory>
        the target directory to store the system image file(s)
"""
import os

# project
from kiwi.tasks.base import CliTask
from kiwi.help import Help
from kiwi.builder import ImageBuilder
from kiwi.system.setup import SystemSetup
from kiwi.privileges import Privileges
from kiwi.path import Path
from kiwi.logger import log


class SystemCreateTask(CliTask):
    """
    Implements creation of system images

    Attributes

    * :attr:`manual`
        Instance of Help
    """
    def process(self):
        """
        Create a system image from the specified root directory
        the root directory is the result of a system prepare
        command
        """
        self.manual = Help()
        if self._help():
            return

        Privileges.check_for_root_permissions()

        abs_target_dir_path = os.path.abspath(
            self.command_args['--target-dir']
        )
        abs_root_path = os.path.abspath(self.command_args['--root'])

        self.load_xml_description(
            abs_root_path
        )
        self.runtime_checker.check_target_directory_not_in_shared_cache(
            abs_target_dir_path
        )

        log.info('Creating system image')
        if not os.path.exists(abs_target_dir_path):
            Path.create(abs_target_dir_path)

        setup = SystemSetup(
            xml_state=self.xml_state,
            root_dir=abs_root_path
        )
        setup.call_image_script()

        image_builder = ImageBuilder(
            self.xml_state,
            abs_target_dir_path,
            abs_root_path
        )
        result = image_builder.create()
        result.print_results()
        result.dump(
            os.sep.join([abs_target_dir_path, 'kiwi.result'])
        )

    def _help(self):
        if self.command_args['help']:
            self.manual.show('kiwi::system::create')
        else:
            return False
        return self.manual
