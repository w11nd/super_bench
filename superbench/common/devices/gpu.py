"""GPU device module."""

from pathlib import Path
import platform

from superbench.common.utils import logger


class GPU():
    """GPU device helper class."""
    def __init__(self):
        """Initialize."""
        self._vendor = self.get_vendor()
        # TODO: check corresponding compute framework availability

    def get_vendor(self):
        """Get GPU vendor.

        Returns:
            str: GPU vendor, nvidia/amd/ascend or platform specific variants.
        """
        # Linux device check
        if platform.system() == 'Linux':
            # Check NVIDIA
            if Path('/dev/nvidiactl').is_char_device():
                if not list(Path('/dev').glob('nvidia[0-9]*')):
                    logger.warning('NVIDIA driver found but no GPU devices detected')
                return 'nvidia'
            
            # Check AMD
            if Path('/dev/kfd').is_char_device() and Path('/dev/dri').is_dir():
                if not list(Path('/dev/dri').glob('renderD*')):
                    logger.warning('AMD driver found but no GPU devices detected')
                return 'amd'
            
            # Check Ascend
            if Path('/dev/davinci_manager').exists():
                ascend_devices = list(Path('/dev').glob('davinci[0-9]*'))
                if not ascend_devices:
                    logger.warning('Ascend driver found but no NPU devices detected')
                else:
                    # Additional verification through version info
                    minor_path = Path('/dev/davinci_manager/desc') / ascend_devices[0].name / 'minor'
                    if minor_path.exists():
                        return 'ascend'
            
        # Windows check
        elif platform.system() == 'Windows':
            # NVIDIA detection
            if list(Path(r'C:\Windows\System32').glob('*DriverStore/FileRepository/nv*.inf_amd64_*/nvapi64.dll')):
                return 'nvidia-graphics'
            
            # AMD detection
            if list(Path(r'C:\Windows\System32').glob('*DriverStore/FileRepository/u*.inf_amd64_*/*/aticfx64.dll')):
                return 'amd-graphics'
            
        return None

    @property
    def vendor(self):
        """Get the GPU vendor."""
        return self._vendor