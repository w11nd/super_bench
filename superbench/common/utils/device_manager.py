# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Device Managerment Library Utility."""

from typing import Optional
from pathlib import Path
from superbench.common.utils import logger
from superbench.common.utils import process
from superbench.common.devices import GPU
import re

gpu = GPU()
if gpu.vendor == 'nvidia' or gpu.vendor == 'nvidia-graphics':
    import py3nvml.py3nvml as nvml
elif gpu.vendor == 'amd' or gpu.vendor == 'amd-graphics':
    import amdsmi as rocml


class DeviceManager:
    """Device management base module."""
    def __init__(self):
        """Constructor."""
        self._device_count = self.get_device_count()

    def get_device_count(self):
        """Get the number of device.

        Return:
            count (int): count of device.
        """
        return 0

    def get_device_compute_capability(self):
        """Get the compute capability of device.

        Return:
            cap (float): the compute capability of device, None means failed to get the data.
        """
        return None

    def get_device_utilization(self, idx):
        """Get the utilization of device.

        Args:
            idx (int): device index.

        Return:
            util (int): the utilization of device, None means failed to get the data.
        """
        return None

    def get_device_temperature(self, idx):
        """Get the temperature of device, unit: celsius.

        Args:
            idx (int): device index.

        Return:
            temp (int): the temperature of device, None means failed to get the data.
        """
        return None

    def get_device_power(self, idx):
        """Get the realtime power of device, unit: watt.

        Args:
            idx (int): device index.

        Return:
            temp (int): the realtime power of device, None means failed to get the data.
        """
        return None

    def get_device_power_limit(self, idx):
        """Get the power management limit of device, unit: watt.

        Args:
            idx (int): device index.

        Return:
            temp (int): the power management limit of device, None means failed to get the data.
        """
        return None

    def get_device_memory(self, idx):
        """Get the memory information of device, unit: byte.

        Args:
            idx (int): device index.

        Return:
            used (int): the used device memory in bytes, None means failed to get the data.
            total (int): the total device memory in bytes, None means failed to get the data.
        """
        return None, None

    def get_device_row_remapped_info(self, idx):
        """Get the row remapped information of device.

        Args:
            idx (int): device index.

        Return:
            remapped_metrics (dict): the row remapped information, None means failed to get the data.
        """
        return None

    def get_device_ecc_error(self, idx):
        """Get the ecc error information of device.

        Args:
            idx (int): device index.

        Return:
            corrected_ecc (int)  : the count of single bit ecc error.
            uncorrected_ecc (int): the count of double bit ecc error.
        """
        return None, None


class NvidiaDeviceManager(DeviceManager):
    """Device management module for Nvidia."""
    def __init__(self):
        """Constructor."""
        nvml.nvmlInit()
        super().__init__()

        self._device_handlers = list()
        for i in range(self._device_count):
            self._device_handlers.append(nvml.nvmlDeviceGetHandleByIndex(i))

    def __del__(self):
        """Destructor."""
        nvml.nvmlShutdown()

    def get_device_count(self):
        """Get the number of device.

        Return:
            count (int): count of device.
        """
        return nvml.nvmlDeviceGetCount()

    def get_device_compute_capability(self):
        """Get the compute capability of device.

        Return:
            cap (float): the compute capability of device, None means failed to get the data.
        """
        try:
            cap = nvml.nvmlDeviceGetCudaComputeCapability(self._device_handlers[0])
        except Exception as err:
            logger.warning('Get device compute capability failed: {}'.format(str(err)))
            return None
        return cap

    def get_device_utilization(self, idx):
        """Get the utilization of device.

        Args:
            idx (int): device index.

        Return:
            util (int): the utilization of device, None means failed to get the data.
        """
        try:
            util = nvml.nvmlDeviceGetUtilizationRates(self._device_handlers[idx])
        except Exception as err:
            logger.warning('Get device utilization failed: {}'.format(str(err)))
            return None
        return util.gpu

    def get_device_temperature(self, idx):
        """Get the temperature of device, unit: celsius.

        Args:
            idx (int): device index.

        Return:
            temp (int): the temperature of device, None means failed to get the data.
        """
        temp = None
        try:
            temp = nvml.nvmlDeviceGetTemperature(self._device_handlers[idx], nvml.NVML_TEMPERATURE_GPU)
        except Exception as err:
            logger.warning('Get device temperature failed: {}'.format(str(err)))
        return temp

    def get_device_power(self, idx):
        """Get the realtime power of device, unit: watt.

        Args:
            idx (int): device index.

        Return:
            temp (int): the realtime power of device, None means failed to get the data.
        """
        try:
            power = nvml.nvmlDeviceGetPowerUsage(self._device_handlers[idx])
        except Exception as err:
            logger.warning('Get device power failed: {}'.format(str(err)))
            return None
        return int(int(power) / 1000)

    def get_device_power_limit(self, idx):
        """Get the power management limit of device, unit: watt.

        Args:
            idx (int): device index.

        Return:
            temp (int): the power management limit of device, None means failed to get the data.
        """
        try:
            powerlimit = nvml.nvmlDeviceGetPowerManagementLimit(self._device_handlers[idx])
        except Exception as err:
            logger.warning('Get device power limitation failed: {}'.format(str(err)))
            return None
        return int(int(powerlimit) / 1000)

    def get_device_memory(self, idx):
        """Get the memory information of device, unit: byte.

        Args:
            idx (int): device index.

        Return:
            used (int): the used device memory in bytes, None means failed to get the data.
            total (int): the total device memory in bytes, None means failed to get the data.
        """
        try:
            mem = nvml.nvmlDeviceGetMemoryInfo(self._device_handlers[idx])
        except Exception as err:
            logger.warning('Get device memory failed: {}'.format(str(err)))
            return None, None
        return mem.used, mem.total

    def get_device_row_remapped_info(self, idx):
        """Get the row remapped information of device.

        The command 'nvidia-smi -i idx -q' contains the following output:
            Remapped Rows
                Correctable Error                 : 0
                Uncorrectable Error               : 0
                Pending                           : No
                Remapping Failure Occurred        : No
                Bank Remap Availability Histogram
                    Max                           : 640 bank(s)
                    High                          : 0 bank(s)
                    Partial                       : 0 bank(s)
                    Low                           : 0 bank(s)
                    None                          : 0 bank(s)
            Temperature
                GPU Current Temp                  : 36 C

        Args:
            idx (int): device index.

        Return:
            remapped_metrics (dict): the row remapped information, None means failed to get the data.
        """
        output = process.run_command('nvidia-smi -i {} -q'.format(idx), quiet=True)
        if output.returncode == 0:
            begin = output.stdout.find('Remapped Rows')
            end = output.stdout.find('Temperature', begin)
            if begin != -1 and end != -1:
                remapped_info = output.stdout[begin:end]
                remapped_info = remapped_info.split('\n')
                remapped_info = [item for item in remapped_info if ':' in item]
                remapped_metrics = dict()
                for item in remapped_info:
                    key_value = item.split(':')
                    key = 'gpu_remap_' + key_value[0].lower().strip().replace(' ', '_')
                    value = key_value[1].replace('bank(s)', '').strip()
                    try:
                        value = int(value)
                        remapped_metrics[key] = value
                    except Exception:
                        continue

                return remapped_metrics

        return None

    def get_device_ecc_error(self, idx):
        """Get the ecc error information of device.

        Args:
            idx (int): device index.

        Return:
            corrected_ecc (int)  : the count of single bit ecc error.
            uncorrected_ecc (int): the count of double bit ecc error.
        """
        corrected_ecc = 0
        uncorrected_ecc = 0
        for location_idx in range(nvml.NVML_MEMORY_LOCATION_COUNT):
            try:
                count = nvml.nvmlDeviceGetMemoryErrorCounter(
                    self._device_handlers[idx], nvml.NVML_MEMORY_ERROR_TYPE_CORRECTED, nvml.NVML_VOLATILE_ECC,
                    location_idx
                )
                corrected_ecc += count
            except nvml.NVMLError:
                pass
            except Exception as err:
                logger.warning('Get device ECC information failed: {}'.format(str(err)))
                return None, None

            try:
                count = nvml.nvmlDeviceGetMemoryErrorCounter(
                    self._device_handlers[idx], nvml.NVML_MEMORY_ERROR_TYPE_UNCORRECTED, nvml.NVML_VOLATILE_ECC,
                    location_idx
                )
                uncorrected_ecc += count
            except nvml.NVMLError:
                pass
            except Exception as err:
                logger.warning('Get device ECC information failed: {}'.format(str(err)))
                return None, None

        return corrected_ecc, uncorrected_ecc


class AmdDeviceManager(DeviceManager):
    """Device management module for AMD."""
    def __init__(self):
        """Constructor."""
        rocml.amdsmi_init()
        self._device_handlers = rocml.amdsmi_get_processor_handles()
        super().__init__()

    def __del__(self):
        """Destructor."""
        rocml.amdsmi_shut_down()

    def get_device_count(self):
        """Get the number of device.

        Return:
            count (int): count of device.
        """
        return len(self._device_handlers)

    def get_device_utilization(self, idx):
        """Get the utilization of device.

        Args:
            idx (int): device index.

        Return:
            util (int): the utilization of device, None means failed to get the data.
        """
        try:
            engine_usage = rocml.amdsmi_get_gpu_activity(self._device_handlers[idx])
        except Exception as err:
            logger.warning('Get device utilization failed: {}'.format(str(err)))
            return None
        return engine_usage['gfx_activity']

    def get_device_temperature(self, idx):
        """Get the temperature of device, unit: celsius.

        Args:
            idx (int): device index.

        Return:
            temp (int): the temperature of device, None means failed to get the data.
        """
        temp = None
        try:
            temp = rocml.amdsmi_get_temp_metric(
                self._device_handlers[idx], rocml.AmdSmiTemperatureType.EDGE, rocml.AmdSmiTemperatureMetric.CURRENT
            )
        except (rocml.AmdSmiLibraryException, rocml.AmdSmiParameterException):
            pass
        except Exception as err:
            logger.warning('Get device temperature failed: {}'.format(str(err)))
        return temp

    def get_device_power(self, idx):
        """Get the realtime power of device, unit: watt.

        Args:
            idx (int): device index.

        Return:
            temp (int): the realtime power of device, None means failed to get the data.
        """
        try:
            power_measure = rocml.amdsmi_get_power_info(self._device_handlers[idx])
        except Exception as err:
            logger.warning('Get device power failed: {}'.format(str(err)))
            return None
        return int(power_measure['average_socket_power'])

    def get_device_power_limit(self, idx):
        """Get the power management limit of device, unit: watt.

        Args:
            idx (int): device index.

        Return:
            temp (int): the power management limit of device, None means failed to get the data.
        """
        try:
            power_measure = rocml.amdsmi_get_power_info(self._device_handlers[idx])
        except Exception as err:
            logger.warning('Get device power limit failed: {}'.format(str(err)))
            return None
        return int(power_measure['power_limit'])

    def get_device_memory(self, idx):
        """Get the memory information of device, unit: byte.

        Args:
            idx (int): device index.

        Return:
            used (int): the used device memory in bytes, None means failed to get the data.
            total (int): the total device memory in bytes, None means failed to get the data.
        """
        try:
            mem_used = rocml.amdsmi_get_gpu_memory_usage(self._device_handlers[idx], rocml.AmdSmiMemoryType.VRAM)
            mem_total = rocml.amdsmi_get_gpu_memory_total(self._device_handlers[idx], rocml.AmdSmiMemoryType.VRAM)
        except Exception as err:
            logger.warning('Get device memory failed: {}'.format(str(err)))
            return None, None
        return mem_used, mem_total

    def get_device_ecc_error(self, idx):
        """Get the ecc error information of device.

        Args:
            idx (int): device index.

        Return:
            corrected_ecc (int)  : the count of single bit ecc error.
            uncorrected_ecc (int): the count of double bit ecc error.
        """
        corrected_ecc = 0
        uncorrected_ecc = 0
        for block in rocml.AmdSmiGpuBlock:
            try:
                ecc_count = rocml.amdsmi_get_gpu_ecc_count(self._device_handlers[idx], block)
                corrected_ecc += ecc_count['correctable_count']
                uncorrected_ecc += ecc_count['uncorrectable_count']
            except (rocml.AmdSmiLibraryException, rocml.AmdSmiParameterException):
                pass
            except Exception as err:
                logger.info('Get device ECC information failed: {}'.format(str(err)))

        return corrected_ecc, uncorrected_ecc


#昇腾没有对应的python库可以直接调用，因此只能通过解析npu-smi来得到
class AscendDeviceManager(DeviceManager):
    """Device management module for Huawei Ascend."""
    def __init__(self):
        """Constructor."""
        super().__init__()
        # 检查npu-smi工具是否存在
        self._npu_smi_path = "/usr/local/sbin/npu-smi"
        if not Path(self._npu_smi_path).exists():
            logger.error("npu-smi tool not found at {}".format(self._npu_smi_path))
            raise RuntimeError("Ascend NPU management tool missing")

    def _run_npu_smi(self, args):
        """Execute npu-smi command and return parsed output."""
        result = process.run_command(f"{self._npu_smi_path} {args}", quiet=True)
        if result.returncode != 0:
            logger.warning(f"npu-smi command failed: {result.stderr}")
            return None
        return result.stdout

    def get_device_count(self):
        """获取昇腾设备数量"""
        try:
            # 检查设备文件数量
            davinci_devices = list(Path('/dev').glob('davinci[0-9]*'))
            return len(davinci_devices)
        except Exception as e:
            logger.error(f"Get Ascend device count failed: {str(e)}")
            return 0

    def get_device_utilization(self, idx):
        """获取设备利用率"""
        output = self._run_npu_smi(f"info -i {idx} -c 0 -t usage")
        if output:
            match = re.search(r"Aicore Usages Rate\(%\) *: *([-+]?\d*\.?\d+)", output)
            if match:
                return int(match.group(1))
        return None

    def get_device_temperature(self, idx):
        """获取芯片温度"""
        output = self._run_npu_smi(f"info  -i {idx} -c 0 -t temp")
        if output:
            match = re.search(r"NPU Temperature \(C\) *: *([-+]?\d*\.?\d+)", output)
            if match:
                return int(match.group(1))
        return None

    def get_device_power(self, idx):
        """实时功率获取"""
        output = self._run_npu_smi(f"info -i {idx} -c 0 -t power")
        if output:
            match = re.search(r"NPU Real-time Power\(W\) *: *([-+]?\d*\.?\d+)", output)
            if match:
                return int(match.group(1))
        return None

    def get_device_memory(self, idx):
        """内存信息获取"""
        output = self._run_npu_smi(f"info -i {idx} -c 0 -t usage")
        if output:
            total_match = re.search(r"HBM Capacity\(MB\) *: *([-+]?\d*\.?\d+)", output)
            used_match = re.search(r"HBM Usages Rate\(%\) *: *([-+]?\d*\.?\d+)", output)
            if total_match and used_match:
                return int(used_match.group(1)), float(total_match.group(1)) * int(used_match.group(1))
        return None, None

    def get_device_ecc_error(self, idx):
        """单比特可以纠正"""
        output = self._run_npu_smi(f"info -i {idx} -c 0 -t ecc")
        if output:
            corrected_ecc = re.search(r"HBM Single Bit Aggregate Total Err Cnt *: *([-+]?\d*\.?\d+)", output)
            uncorrected_ecc = re.search(r"HBM Double Bit Aggregate Total Err Cnt *: *([-+]?\d*\.?\d+)", output)
            return int(corrected_ecc.group(1)), int(uncorrected_ecc.group(1))
        return None, None


    

device_manager: Optional[DeviceManager] = DeviceManager()
if gpu.vendor == 'nvidia' or gpu.vendor == 'nvidia-graphics':
    device_manager = NvidiaDeviceManager()
elif gpu.vendor == 'amd' or gpu.vendor == 'amd-graphics':
    device_manager = AmdDeviceManager()
elif gpu.vendor == 'ascend':  # 新增昇腾分支
    try:
        device_manager = AscendDeviceManager()
    except Exception as e:
        logger.error(f"Initialize Ascend device manager failed: {str(e)}")

