"""
DATAPROCESS.FUNCTIONS Package

数据处理功能实现模块。

此目录包含各种具体的数据处理功能实现，
如批处理绘图、列选择对话框、数据转换、状态查找等。
"""

from .batch_plot import BatchPlotDialog
from .calculate import compute_stats_from_selection, compute_diffs, read_csv_columns_for_batch, compute_batch_all_results
from .column_selection_dialog import ColumnSelectionDialog
from .data_convert import DataConvertDialog
from .editable_table import EditableTable
from .encoding_dialog import EncodingDialog
from .filter_comparison import FilterDialog,FilterComparisonDialog
from .scatter_plot import plot_scatter
from .states_lookup import StatesLookupWindow,StatesColumnSelectionDialog
from .steady_state_diff import SteadyStateDiffDialog
from .uid_data_processor import UIDDataProcessorDialog


# 定义公共接口
__all__ = [
    'BatchPlotDialog',
    'compute_stats_from_selection',
    'compute_diffs',
    'read_csv_columns_for_batch',
    'compute_batch_all_results',
    'ColumnSelectionDialog',
    'DataConvertDialog',
    'EditableTable',
    'EncodingDialog',
    'FilterDialog','FilterComparisonDialog',
    'plot_scatter',
    'StatesLookupWindow','StatesColumnSelectionDialog',
    'SteadyStateDiffDialog',
    'UIDDataProcessorDialog',
]