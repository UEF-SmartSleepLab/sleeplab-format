import copy
import logging
import numpy as np
import scipy.signal

from importlib import import_module
from sleeplab_format.extractor.config import ArrayAction, ArrayConfig, SeriesConfig
from sleeplab_format.models import ArrayAttributes, SampleArray, Series, AASMSleepStage, Subject
from typing import Callable


logger = logging.getLogger(__name__)


def import_function(func_str: str) -> Callable:
    """Import a function from a string.
    
    E.g. `import_function('sleeplab_extractor.preprocess.resample_polyphase')`
    """
    module_str, func_name = func_str.rsplit('.', maxsplit=1)
    module = import_module(module_str)
    func = getattr(module, func_name)
    return func


def chain_action(
        orig_func: Callable,
        orig_attrs: ArrayAttributes,
        action: ArrayAction,
        ref_func: Callable | None) -> Callable:
    """Use a closure to chain orig_func with an action."""
    def inner():
        kwargs = copy.deepcopy(action.kwargs)
        if ref_func is not None:
            kwargs['ref_s'] = ref_func()

        return _func(orig_func(), orig_attrs, **kwargs)

    _func = import_function(action.method)
    return inner


def process_array(
        arr_dict: dict[str, SampleArray],
        cfg: ArrayConfig) -> SampleArray:
    """Process a SampleArray according to the actions defined in cfg."""
    # Create a deep copy not to modify the source dataset
    arr = arr_dict[cfg.name].model_copy(deep=True)

    for action in cfg.actions:
        if action.ref_name is not None:
            if action.ref_name not in arr_dict.keys() and action.alt_ref_names is not None:
                alt_name_set = set(action.alt_ref_names).intersection(set(arr_dict.keys()))
                if alt_name_set != set():
                    action.ref_name = alt_name_set.pop()
            try:
                ref_func = arr_dict[action.ref_name].values_func
            except KeyError:
                logger.warning(f'Discarding {cfg.name} since reference {[action.ref_name] + (action.alt_ref_names or [])} was not found in {arr_dict.keys()}')
                return None
        else:
            ref_func = None

        _values_func = chain_action(
            arr.values_func,
            arr.attributes,
            action,
            ref_func)
        _attributes = arr.attributes.model_copy(update=action.updated_attributes)
        arr = arr.model_copy(update={'attributes': _attributes, 'values_func': _values_func})

    return arr


def process_subject(subject: Subject, cfg: SeriesConfig) -> Subject | None:
    """Process all conditions and sample arrays for a single subject."""
    _sample_arrays = {}
    _cfg = cfg.model_copy(deep=True)

    if _cfg.filter_conds is not None:
        for cond in _cfg.filter_conds:
            _func = import_function(cond.method)
            if cond.kwargs is None:
                bool_keep = _func(subject)
            else:
                bool_keep = _func(subject, **cond.kwargs)

            if not bool_keep:
                _msg = f'Skipping subject {subject.metadata.subject_id} due to filter_cond {cond.name}'
                logger.info(_msg)
                return None, _msg

    for array_cfg in _cfg.array_configs:
        if array_cfg.alt_names is not None:
            alt_name_set = set(array_cfg.alt_names).intersection(set(subject.sample_arrays.keys()))
        else:
            alt_name_set = set()

        if array_cfg.name not in subject.sample_arrays.keys() and alt_name_set != set():
            array_cfg.name = alt_name_set.pop()

        if array_cfg.name in subject.sample_arrays.keys():
            _arr = process_array(subject.sample_arrays, array_cfg)
            if _arr is not None:
                _sample_arrays[_arr.attributes.name] = _arr
        else:
            logger.warning(f'{[array_cfg.name] + (array_cfg.alt_names or [])} not in sample arrays for subject {subject.metadata.subject_id}')

    if cfg.required_result_array_names is not None:
        # Ignore subjects with missing required arrays
        array_names = set([a.attributes.name for a in _sample_arrays.values()])
        required = set(_cfg.required_result_array_names)
        if not required.issubset(array_names):
            _msg = f'Skipping subject {subject.metadata.subject_id} with missing sample arrays. Required: {required}, missing: {required - array_names}'
            logger.warning(_msg)
            return None, _msg

    return subject.model_copy(update={'sample_arrays': _sample_arrays})


def process_series(series: Series, cfg: SeriesConfig) -> Series:
    # A handled skip is a subject for which process_subject returns None,
    # unhandled is a subject for which process_subject throws an exception
    skipped = {'handled': {}, 'unhandled': {}}
    updated_subjects = {}
    for sid, subj in series.subjects.items():
        try:
            _subj = process_subject(subj, cfg)
            match _subj:
                case Subject():
                    updated_subjects[sid] = _subj
                case (None, str(msg)):
                    skipped['handled'][sid] = msg
                case _:
                    skipped['unhandled'][sid] = f'process_subject(): incorrect return type {repr(_subj)}'
        except Exception as e:
            skipped['unhandled'][sid] = repr(e)

    return series.model_copy(update={'subjects': updated_subjects}), skipped


def filter_by_tst(
        subject: Subject,
        hypnogram_key: str,
        min_tst_sec: float) -> bool:
    allowed_stages = [
        AASMSleepStage.N1,
        AASMSleepStage.N2,
        AASMSleepStage.N3,
        AASMSleepStage.R
    ]
    hg = subject.annotations[hypnogram_key].annotations
    tst = sum([ann.duration for ann in hg if ann.name in allowed_stages])
    return tst >= min_tst_sec


def is_power_of_two(x: float) -> bool:
    return np.log2(x) % 1 == 0.0


def _decimate(s: np.array, factor: int) -> np.array:
    """Implement decimation of powers of two by consecutive decimation by 2.
    
    If higher factors are used, considerably more noise may be induced in the signals.
    """
    assert is_power_of_two(factor)
    if factor < 4:
        return scipy.signal.decimate(s, factor)
    else:
        return _decimate(scipy.signal.decimate(s, 2), factor // 2)


def decimate(
        s: np.array,
        attributes: ArrayAttributes, *,
        fs_new: float,
        dtype: np.dtype = np.float32) -> np.array:
    # Cast to float64 before IIR filtering!!!
    s = s.astype(np.float64)
    ds_factor = int(attributes.sampling_rate // fs_new)
    return _decimate(s, ds_factor).astype(dtype)


def resample_polyphase(
        s: np.array,
        attributes: ArrayAttributes, *,
        fs_new: float,
        dtype: np.dtype = np.float32) -> np.array:
    """Resample the signal using scipy.signal.resample_polyphase."""
    # Cast to float64 before filtering
    s = s.astype(np.float64)
    
    up = int(fs_new)
    down = int(attributes.sampling_rate)
    
    resampled = scipy.signal.resample_poly(s, up, down)
    return resampled.astype(dtype)


def cheby2_filtfilt(
        s: np.array,
        fs: float,
        cutoff: float,
        order: int = 5,
        rs: float = 40.0,
        btype='highpass') -> np.array:
    """Chebyshev type1 highpass filtering.
    
    Args:
        s: the signal
        fs: sampling freq in Hz
        cutoff: cutoff freq in Hz
    Returns:
        the filtered signal
    """
    nyq = 0.5 * fs
    norm_cutoff = cutoff / nyq
    sos = scipy.signal.cheby2(order, rs, norm_cutoff, btype=btype, output='sos')
    return scipy.signal.sosfiltfilt(sos, s)


def highpass(
        s: np.array,
        attributes: ArrayAttributes, *,
        cutoff: float,
        dtype=np.float32) -> np.array:
    return cheby2_filtfilt(s, attributes.sampling_rate, cutoff, btype='highpass').astype(dtype)


def lowpass(
        s: np.array,
        attributes: ArrayAttributes, *,
        cutoff: float,
        dtype=np.float32) -> np.array:
    return cheby2_filtfilt(s, attributes.sampling_rate, cutoff, btype='lowpass').astype(dtype)


def z_score_norm(
        s: np.array,
        attributes: ArrayAttributes,
        dtype=np.float32) -> np.array:
    return ((s - np.mean(s)) / np.std(s)).astype(dtype)

def iqr_norm(
	s: np.array, attributes: 
	ArrayAttributes, 
	dtype=np.float32) -> np.array:
    """Interquartile range standardization for the signal."""
    q75, q25 = np.percentile(s, [75 ,25])
    iqr = q75 - q25
    if iqr == 0: 
        return np.zeros(s.shape, dtype=dtype)
    else:
        return ((s - np.median(s)) / iqr).astype(dtype)

def sub_ref(
        s: np.array,
        attributes: ArrayAttributes, *,
        ref_s: np.array,
        dtype=np.float32) -> np.array:
    return (s - ref_s).astype(dtype)


def add_ref(
        s: np.array,
        attributes: ArrayAttributes, *,
        ref_s: np.array,
        dtype=np.float32) -> np.array:
    return (s + ref_s).astype(dtype)


def upsample_linear(
        s: np.array,
        attributes: ArrayAttributes, *,
        fs_new: float,
        dtype=np.float32):
    """Linear interpolation for upsampling signals such as SpO2."""
    fs_orig = attributes.sampling_rate
    n = len(s)
    int_factor = fs_new // fs_orig
    x = np.arange(0, int_factor*n, int_factor)
    x_new = np.arange(int_factor*n - 1)
    s_interp = np.interp(x_new, x, s)

    # Repeat the last element to match signal lengths
    s_interp = np.append(s_interp, s_interp[-1])
    return s_interp.astype(dtype)
