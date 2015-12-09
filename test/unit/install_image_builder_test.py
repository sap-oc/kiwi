from nose.tools import *
from mock import patch
from mock import call
import mock
import kiwi

import nose_helper

from kiwi.exceptions import *
from kiwi.install_image_builder import InstallImageBuilder


class TestInstallImageBuilder(object):
    def setup(self):
        self.bootloader = mock.Mock()
        kiwi.install_image_builder.BootLoaderConfig.new = mock.Mock(
            return_value=self.bootloader
        )
        self.squashed_image = mock.Mock()
        kiwi.install_image_builder.FileSystemSquashFs = mock.Mock(
            return_value=self.squashed_image
        )
        self.iso_image = mock.Mock()
        kiwi.install_image_builder.FileSystemIsoFs = mock.Mock(
            return_value=self.iso_image
        )
        self.mbrid = mock.Mock()
        self.mbrid.get_id = mock.Mock(
            return_value='0xffffffff'
        )
        kiwi.install_image_builder.ImageIdentifier = mock.Mock(
            return_value=self.mbrid
        )
        kiwi.install_image_builder.Path = mock.Mock()
        self.checksum = mock.Mock()
        kiwi.install_image_builder.Checksum = mock.Mock(
            return_value=self.checksum
        )
        self.kernel = mock.Mock()
        self.kernel.get_kernel = mock.Mock()
        self.kernel.get_xen_hypervisor = mock.Mock()
        self.kernel.copy_kernel = mock.Mock()
        self.kernel.copy_xen_hypervisor = mock.Mock()
        kiwi.install_image_builder.Kernel = mock.Mock(
            return_value=self.kernel
        )
        self.xml_state = mock.Mock()
        self.xml_state.xml_data.get_name = mock.Mock(
            return_value='result-image'
        )
        self.boot_image_task = mock.Mock()
        self.boot_image_task.boot_root_directory = 'initrd_dir'
        self.boot_image_task.initrd_filename = 'initrd'
        self.install_image = InstallImageBuilder(
            self.xml_state, 'target_dir', 'some-diskimage', self.boot_image_task
        )
        self.install_image.machine = mock.Mock()
        self.install_image.machine.get_domain = mock.Mock(
            return_value='dom0'
        )

    @patch('kiwi.install_image_builder.mkdtemp')
    @patch('__builtin__.open')
    @patch('kiwi.install_image_builder.Command.run')
    def test_create_install_iso(self, mock_command, mock_open, mock_dtemp):
        mock_dtemp.return_value = 'tmpdir'
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)

        self.install_image.create_install_iso()

        self.checksum.md5.assert_called_once_with(
            'initrd_dir/etc/image.md5'
        )
        assert mock_open.call_args_list == [
            call('initrd_dir/config.vmxsystem', 'w'),
            call('tmpdir/config.isoclient', 'w')
        ]
        assert file_mock.write.call_args_list == [
            call('IMAGE="some-diskimage"\n'),
            call('IMAGE="some-diskimage"\n')
        ]
        self.squashed_image.create_on_file.assert_called_once_with(
            'some-diskimage.squashfs'
        )
        assert self.bootloader.setup_install_boot_images.call_args_list == [
            call(lookup_path='initrd_dir', mbrid=None),
            call(lookup_path='initrd_dir', mbrid=self.mbrid)
        ]
        assert self.bootloader.setup_install_boot_images.call_args_list == [
            call(lookup_path='initrd_dir', mbrid=None),
            call(lookup_path='initrd_dir', mbrid=self.mbrid)
        ]
        assert self.bootloader.setup_install_image_config.call_args_list == [
            call(mbrid=None),
            call(mbrid=self.mbrid)
        ]
        assert self.bootloader.write.call_args_list == [
            call(), call()
        ]
        self.boot_image_task.create_initrd.assert_called_once_with(
            self.mbrid
        )
        self.kernel.copy_kernel.assert_called_once_with(
            'tmpdir/boot/x86_64/loader', '/linux'
        )
        self.kernel.copy_xen_hypervisor.assert_called_once_with(
            'tmpdir/boot/x86_64/loader', '/xen.gz'
        )
        assert mock_command.call_args_list == [
            call(['mv', 'some-diskimage.squashfs', 'tmpdir']),
            call(['mv', 'initrd', 'tmpdir/boot/x86_64/loader/initrd'])
        ]
        self.iso_image.create_on_file.assert_called_once_with(
            'target_dir/result-image.install.iso'
        )

    @patch('kiwi.install_image_builder.mkdtemp')
    @patch('__builtin__.open')
    @patch('kiwi.install_image_builder.Command.run')
    @raises(KiwiInstallBootImageError)
    def test_create_install_iso_no_kernel_found(
        self, mock_command, mock_open, mock_dtemp
    ):
        self.kernel.get_kernel.return_value = False
        self.install_image.create_install_iso()

    @patch('kiwi.install_image_builder.mkdtemp')
    @patch('__builtin__.open')
    @patch('kiwi.install_image_builder.Command.run')
    @raises(KiwiInstallBootImageError)
    def test_create_install_iso_no_hypervisor_found(
        self, mock_command, mock_open, mock_dtemp
    ):
        self.kernel.get_xen_hypervisor.return_value = False
        self.install_image.create_install_iso()

    def test_create_install_pxe_archive(self):
        # TODO
        self.install_image.create_install_pxe_archive()

    @patch('kiwi.install_image_builder.Path.wipe')
    def test_destructor(self, mock_wipe):
        self.install_image.media_dir = 'media-dir'
        self.install_image.__del__()
        mock_wipe.assert_called_once_with('media-dir')
        self.install_image.media_dir = None
