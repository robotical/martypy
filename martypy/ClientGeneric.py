from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Union, Tuple
from warnings import warn

class ClientGeneric(ABC):

    SIDE_CODES = {
        'left'    : 0,
        'right'   : 1,
        'forward' : 2,
        'back'    : 3,
        'auto'    : 0,
    }

    EYE_POSES = {
        'angry'   : 'eyesAngry',
        'excited' : 'eyesExcited',
        'normal'  : 'eyesNormal',
        'wide'    : 'eyesWide',
        'wiggle'  : 'wiggleEyes'
    }

    DISCO_PATTERNS = {
        "show-off": "show-off",
        "pinwheel": "pinwheel",
        "off": "off"
    }

    NOT_IMPLEMENTED = "Unfortunately this Marty doesn't do that"

    def __init__(self, blocking: Union[bool, None], *args, **kwargs):
        super().__init__()
        if len(args) > 0:
            warn(f"Ignoring unexpected constructor argument(s): {args}", stacklevel=4)
        if len(kwargs) > 0:
            warn(f"Ignoring unexpected constructor argument(s): {kwargs}", stacklevel=4)
        self._is_blocking: bool = True if blocking is None else blocking

    @classmethod
    def dict_merge(cls, *dicts):
        '''
        Merge all provided dicts into one dict
        '''
        merged = {}
        for d in dicts:
            if not isinstance(d, dict):
                raise ValueError('Value should be a dict')
            else:
                merged.update(d)
        return merged

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def close(self):
        pass

    def is_blocking(self, local_override: Optional[bool] = None) -> bool:
        """
        Check if this client is blocking, optionally taking into account a local
        blocking override flag.
        """
        if local_override is not None:
            return local_override
        else:
            return self._is_blocking

    def set_blocking(self, blocking: bool):
        self._is_blocking = blocking

    @abstractmethod
    def wait_if_required(self, expected_wait_ms: int, blocking_override: Union[bool, None]):
        raise NotImplementedError()

    @abstractmethod
    def hello(self) -> bool:
        return False

    @abstractmethod
    def get_ready(self) -> bool:
        return False

    @abstractmethod
    def stand_straight(self, move_time: int) -> bool:
        return False

    @abstractmethod
    def discover(self) -> List[str]:
        return []

    @abstractmethod
    def stop(self, stop_type: str, stopCode: int) -> bool:
        return False

    @abstractmethod
    def resume(self) -> bool:
        return False

    @abstractmethod
    def hold_position(self, hold_time: int) -> bool:
        return False

    @abstractmethod
    def move_joint(self, joint_id: int, position: int, move_time: int) -> bool:
        return False

    @abstractmethod
    def get_joint_position(self, joint_id: Union[int, str]) -> float:
        return 0

    @abstractmethod
    def get_joint_current(self, joint_id: Union[int, str]) -> float:
        return 0

    @abstractmethod
    def get_joint_status(self, joint_id: Union[int, str]) -> int:
        return 0

    @abstractmethod
    def lean(self, direction: str, amount: Optional[int], move_time: int) -> bool:
        return False

    @abstractmethod
    def walk(self, num_steps: int = 2, start_foot:str = 'auto', turn: int = 0,
                step_length:int = 25, move_time: int = 1500) -> bool:
        return False

    @abstractmethod
    def eyes(self, joint_id: int, pose_or_angle: Union[str, int], move_time: int = 1000) -> bool:
        return False

    @abstractmethod
    def kick(self, side: str = 'right', twist: int = 0, move_time: int = 2500) -> bool:
        return False

    @abstractmethod
    def arms(self, left_angle: int, right_angle: int, move_time: int) -> bool:
        return False

    @abstractmethod
    def celebrate(self, move_time: int = 4000) -> bool:
        return False

    @abstractmethod
    def circle_dance(self, side: str = 'right', move_time: int = 2500) -> bool:
        return False

    @abstractmethod
    def dance(self, side: str = 'right', move_time: int = 3000) -> bool:
        return False

    @abstractmethod
    def wiggle(self, move_time: int = 5000) -> bool:
        return False

    @abstractmethod
    def sidestep(self, side: str, steps: int = 1, step_length: int = 50,
            move_time: int = 1000) -> bool:
        return False

    @abstractmethod
    def set_volume(self, volume: int) -> bool:
        pass

    @abstractmethod
    def get_volume(self) -> int:
        return 0

    @abstractmethod
    def play_sound(self, name_or_freq_start: Union[str,float], 
            freq_end: Optional[float] = None, 
            duration: Optional[int] = None) -> bool:
        return False

    @abstractmethod
    def pinmode_gpio(self, gpio: int, mode: str) -> bool:
        return False

    @abstractmethod
    def write_gpio(self, gpio: int, value: int) -> bool:
        return False

    @abstractmethod
    def digitalread_gpio(self, gpio: int) -> bool:
        return False

    @abstractmethod
    def i2c_write(self, *byte_array: int) -> bool:
        return False

    @abstractmethod
    def i2c_write_to_ric(self, address: int, byte_array: bytes) -> bool:
        return False

    @abstractmethod
    def get_battery_voltage(self) -> float:
        return 0

    @abstractmethod
    def get_battery_remaining(self) -> float:
        return 0

    @abstractmethod
    def get_distance_sensor(self) -> Union[int, float]:
        return 0

    @abstractmethod
    def foot_on_ground(self, add_on_or_side: str) -> bool:
        return False

    @abstractmethod
    def foot_obstacle_sensed(self, add_on_or_side: str) -> bool:
        return False
        
    @abstractmethod
    def get_obstacle_sensor_reading(self, add_on_or_side: str) -> int:
        return 0

    @abstractmethod
    def get_ground_sensor_reading(self, add_on_or_side: str) -> int:
        return 0

    @abstractmethod
    def get_accelerometer(self, axis: Optional[str] = None, axisCode: int = 0) -> float:
        return 0

    @abstractmethod
    def enable_motors(self, enable: bool = True, clear_queue: bool = True) -> bool:
        return False

    @abstractmethod
    def enable_safeties(self, enable: bool = True) -> bool:
        return False

    @abstractmethod
    def fall_protection(self, enable: bool = True) -> bool:
        return False

    @abstractmethod
    def motor_protection(self, enable: bool = True) -> bool:
        return False

    @abstractmethod
    def battery_protection(self, enable: bool = True) -> bool:
        return False

    @abstractmethod
    def buzz_prevention(self, enable: bool = True) -> bool:
        return False

    @abstractmethod
    def lifelike_behaviour(self, enable: bool = True) -> bool:
        return False

    @abstractmethod
    def set_parameter(self, *byte_array: int) -> bool:
        return False

    @abstractmethod
    def save_calibration(self) -> bool:
        return False

    @abstractmethod
    def clear_calibration(self) -> bool:
        return False

    @abstractmethod
    def is_calibrated(self) -> bool:
        return False

    @abstractmethod
    def ros_command(self, *byte_array: int) -> bool:
        return False

    @abstractmethod
    def keyframe (self, time: float, num_of_msgs: int, msgs) -> List[bytes]:
        return False

    @abstractmethod
    def get_chatter(self) -> bytes:
        return False

    @abstractmethod
    def get_firmware_version(self) -> bool:
        return False

    @abstractmethod
    def _mute_serial(self) -> bool:
        return False

    @abstractmethod
    def ros_serial_formatter(self, topicID: int, send: bool = False, *message: int) -> List[int]:
        return False

    @abstractmethod
    def is_moving(self) -> bool:
        return False

    @abstractmethod
    def is_paused(self) -> bool:
        return False

    @abstractmethod
    def get_robot_status(self) -> Dict:
        return {}

    @abstractmethod
    def get_joints(self) -> Dict:
        return {}

    @abstractmethod
    def get_power_status(self) -> Dict:
        return {}

    @abstractmethod
    def get_add_ons_status(self) -> Dict:
        return {}

    @abstractmethod
    def get_add_on_status(self, add_on_name_or_id: Union[int, str]) -> Dict:
        return {}

    @abstractmethod
    def add_on_query(self, add_on_name: str, data_to_write: bytes, num_bytes_to_read: int) -> Dict:
        return {}

    @abstractmethod
    def get_system_info(self) -> Dict:
        return {}

    @abstractmethod
    def set_marty_name(self, name: str) -> bool:
        return False

    @abstractmethod
    def get_marty_name(self) -> str:
        return ""

    @abstractmethod
    def is_marty_name_set(self) -> bool:
        return False

    @abstractmethod
    def get_hw_elems_list(self) -> List:
        return []

    @abstractmethod
    def send_ric_rest_cmd(self, ricRestCmd: str) -> None:
        pass

    @abstractmethod
    def send_ric_rest_cmd_sync(self, ricRestCmd: str) -> Dict:
        return {}

    @abstractmethod
    def disco_off(self, add_on: str) -> bool :
        return False

    @abstractmethod
    def disco_pattern(self, pattern: int, add_on: str) -> bool :
        return False

    @abstractmethod   
    def disco_color(self, color: Union[str, Tuple[int, int, int]], add_on: str, region: Union[int, str]) -> bool:  
        return False

    @abstractmethod
    def disco_group_operation(self, disco_operation: Callable, whoami_type_codes: set, operation_kwargs: dict) -> bool:
        return False

    @abstractmethod
    def register_logging_callback(self, loggingCallback: Callable[[str],None]) -> None:
        pass

    @abstractmethod
    def register_publish_callback(self, messageCallback: Callable[[int],None]) -> None:
        pass

    @abstractmethod
    def register_report_callback(self, messageCallback: Callable[[str],None]) -> None:
        pass

    @abstractmethod
    def get_interface_stats(self) -> Dict:
        return {}

    @abstractmethod
    def preException(self, isFatal: bool) -> None:
        pass

    @abstractmethod
    def get_test_output(self) -> dict:
        return ""

    @abstractmethod
    def is_conn_ready(self) -> bool:
        return False

    @abstractmethod
    def send_file(self, filename: str, 
                progress_callback: Callable[[int, int], bool] = None,
                file_dest:str = "fs") -> bool:
        return False

    @abstractmethod
    def play_mp3(self, filename: str,
                progress_callback: Callable[[int, int], bool] = None) -> bool:
        return False

    @abstractmethod
    def get_file_list(self) -> List[str]:
        return []

    @abstractmethod
    def delete_file(self, filename: str) -> bool:
        return False